import xml.etree.ElementTree as ET
import pandas as pd
import statistics
import time
import os
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple

# ==========================================
# PART 1: OPTIMIZED DATA STRUCTURES
# ==========================================

@dataclass(frozen=True)
class FontSpec:
    """Immutable, hashable representation of a font."""
    size: int
    family: str
    color: str

@dataclass
class TextFragment:
    """Atomic unit of text. Uses __slots__ for maximum memory efficiency."""
    __slots__ = ['text', 'top', 'left', 'width', 'height', 'font_id', 'right', 'bottom']
    
    text: str
    top: int
    left: int
    width: int
    height: int
    font_id: str
    right: int
    bottom: int

    @classmethod
    def from_node(cls, node: ET.Element) -> 'TextFragment':
        top = int(node.get('top'))
        left = int(node.get('left'))
        width = int(node.get('width'))
        height = int(node.get('height'))
        # itertext() handles <b>, <i> nested tags; strip() removes whitespace
        text = "".join(node.itertext()).strip()
        
        return cls(
            text=text,
            top=top,
            left=left,
            width=width,
            height=height,
            font_id=node.get('font'),
            right=left + width,
            bottom=top + height
        )

class TextLine:
    """Represents a reconstructed visual line."""
    __slots__ = ['fragments', 'top', 'bottom', 'left']

    def __init__(self, first_fragment: TextFragment):
        self.fragments: List[TextFragment] = [first_fragment]
        self.top = first_fragment.top
        self.bottom = first_fragment.bottom
        self.left = first_fragment.left

    def add(self, fragment: TextFragment):
        self.fragments.append(fragment)
        if fragment.bottom > self.bottom:
            self.bottom = fragment.bottom

    def get_text_content(self, space_threshold: int = 3) -> str:
        """Reconstructs text with spaces based on X-axis gaps."""
        if not self.fragments: return ""
        
        # Sort left-to-right
        self.fragments.sort(key=lambda f: f.left)
        
        buffer = [self.fragments[0].text]
        for i in range(1, len(self.fragments)):
            curr = self.fragments[i]
            prev = self.fragments[i-1]
            gap = curr.left - prev.right
            
            if gap > space_threshold:
                buffer.append(" ")
            buffer.append(curr.text)
            
        return "".join(buffer)

@dataclass
class HeaderContext:
    """State Machine to track the current hierarchical context."""
    filename: str
    page_num: int
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None

    def update_header(self, level: str, text: str):
        if level == 'h1':
            self.h1, self.h2, self.h3 = text, None, None
        elif level == 'h2':
            self.h2, self.h3 = text, None
        elif level == 'h3':
            self.h3 = text

    def to_dict(self, body_text: str) -> Dict:
        return {
            "Filename": self.filename,
            "PageNo": self.page_num,
            "Header1": self.h1,
            "Header2": self.h2,
            "Header3": self.h3,
            "Text": body_text
        }

# ==========================================
# PART 2: STATISTICAL & GEOMETRIC LOGIC
# ==========================================

def calculate_dynamic_y_tolerance(fragments: List[TextFragment]) -> int:
    """Statistically determines 'jitter' tolerance for line grouping."""
    if not fragments: return 3
    heights = [f.height for f in fragments]
    if not heights: return 3
    
    # Mode height (Body text size)
    try:
        dominant_height = statistics.mode(heights)
    except statistics.StatisticsError:
        dominant_height = statistics.median(heights)

    # Analyze vertical gaps
    sorted_by_top = sorted(fragments, key=lambda f: f.top)
    jitter_values = []
    
    for i in range(1, len(sorted_by_top)):
        diff = sorted_by_top[i].top - sorted_by_top[i-1].top
        # Only consider diffs that are NOT line breaks (heuristic < 50% height)
        if 0 <= diff < (dominant_height * 0.5):
            jitter_values.append(diff)

    if not jitter_values:
        return max(2, int(dominant_height * 0.1))

    # Mean + 2 StdDev covers 95% of noise
    mean_val = statistics.mean(jitter_values)
    std_val = statistics.stdev(jitter_values) if len(jitter_values) > 1 else 0
    calc_tol = int(mean_val + (2 * std_val))
    
    return max(2, min(calc_tol, int(dominant_height * 0.3)))

def determine_font_roles(font_map: Dict[str, FontSpec], lines: List[TextLine]) -> Dict[str, str]:
    """Assigns 'h1', 'h2', 'body' roles based on usage frequency and size."""
    if not lines: return {}

    # Count font usage (by size)
    font_usage = {} 
    size_to_ids = {} 
    
    for line in lines:
        fid = line.fragments[0].font_id
        if fid not in font_map: continue
        size = font_map[fid].size
        
        font_usage[size] = font_usage.get(size, 0) + 1
        if size not in size_to_ids: size_to_ids[size] = set()
        size_to_ids[size].add(fid)

    if not font_usage: return {}

    # Body = Most frequent size (Mode)
    body_size = max(font_usage, key=font_usage.get)
    
    # Headers = Sizes larger than body
    all_sizes = sorted(font_usage.keys(), reverse=True)
    header_sizes = [s for s in all_sizes if s > body_size]
    
    role_map = {}
    
    # Assign H1 (Largest)
    if len(header_sizes) >= 1:
        for fid in size_to_ids[header_sizes[0]]: role_map[fid] = 'h1'
            
    # Assign H2 (Second Largest)
    if len(header_sizes) >= 2:
        for fid in size_to_ids[header_sizes[1]]: role_map[fid] = 'h2'
    
    # Map 'body' explicitly
    for size in all_sizes:
        if size <= body_size:
            for fid in size_to_ids[size]: role_map[fid] = 'body'
            
    return role_map

# ==========================================
# PART 3: EXTRACTION & PARSING
# ==========================================

def extract_text_lines(page_element: ET.Element) -> List[TextLine]:
    """Raw XML -> Sorted TextLine objects."""
    fragments = [TextFragment.from_node(n) for n in page_element.findall('text')]
    
    # Filter empty texts
    fragments = [f for f in fragments if f.text]
    if not fragments: return []

    # Dynamic Tolerance
    y_tol = calculate_dynamic_y_tolerance(fragments)

    # Sort: Top (Primary), Left (Secondary)
    fragments.sort(key=lambda f: (f.top, f.left))

    # Cluster
    lines = []
    current_line = TextLine(fragments[0])
    lines.append(current_line)
    
    for i in range(1, len(fragments)):
        frag = fragments[i]
        if abs(frag.top - current_line.top) <= y_tol:
            current_line.add(frag)
        else:
            current_line = TextLine(frag)
            lines.append(current_line)
            
    return lines

def parse_page_to_data_rows(filename: str, page_num: int, 
                            lines: List[TextLine], font_map: Dict[str, FontSpec]) -> List[Dict]:
    """Buffered State Machine to generate table rows."""
    
    role_map = determine_font_roles(font_map, lines)
    context = HeaderContext(filename, page_num)
    text_buffer = [] 
    rows = []

    def flush_buffer():
        if not text_buffer: return
        full_text = " ".join(text_buffer)
        rows.append(context.to_dict(full_text))
        text_buffer.clear()

    for i, line in enumerate(lines):
        first_frag = line.fragments[0]
        fid = first_frag.font_id
        text_content = line.get_text_content()
        role = role_map.get(fid, 'body')

        if role in ['h1', 'h2', 'h3']:
            # New Header: Flush previous content -> Update Header
            flush_buffer()
            context.update_header(role, text_content)
        else:
            # Body Text: Check for paragraph break (vertical gap)
            if i > 0 and text_buffer:
                prev_line = lines[i-1]
                gap = line.top - prev_line.bottom
                # Heuristic: If gap > 60% of font size, it's a new paragraph
                font_size = font_map[fid].size if fid in font_map else 12
                if gap > (font_size * 0.6):
                    flush_buffer()

            text_buffer.append(text_content)

    flush_buffer() # Final flush
    return rows

# ==========================================
# PART 4: MAIN EXECUTION FLOW
# ==========================================

def get_xml_root(path):
    return ET.parse(path).getroot()

def sanitize_xml(root):
    """Removes empty nodes in-place."""
    for page in root.findall('page'):
        for node in page.findall('text'):
            if not "".join(node.itertext()).strip():
                page.remove(node)
    return root

def create_font_map(root):
    m = {}
    for f in root.findall('.//fontspec'):
        m[f.get('id')] = FontSpec(
            size=int(f.get('size', 0)),
            family=f.get('family', ''),
            color=f.get('color', '')
        )
    return m

def main(xml_file_path: str, output_csv_path: str):
    # TIMING: Start
    t_start = time.perf_counter()
    filename = os.path.basename(xml_file_path)

    print(f"--- Processing: {filename} ---")

    # 1. Load & Sanitize
    t0 = time.perf_counter()
    root = get_xml_root(xml_file_path)
    root = sanitize_xml(root)
    font_map = create_font_map(root)
    t1 = time.perf_counter()
    print(f"[Stats] Parsing & Map Creation: {t1 - t0:.4f} sec")

    # 2. Process Pages
    t0 = time.perf_counter()
    all_rows = []
    pages = root.findall('page')
    
    for i, page in enumerate(pages):
        # A. Geometry
        lines = extract_text_lines(page)
        # B. Logic
        page_rows = parse_page_to_data_rows(filename, i + 1, lines, font_map)
        all_rows.extend(page_rows)
        
    t1 = time.perf_counter()
    print(f"[Stats] Logic Processing ({len(pages)} pages): {t1 - t0:.4f} sec")

    # 3. Create DataFrame & Save
    t0 = time.perf_counter()
    df = pd.DataFrame(all_rows)
    
    # Fill NaN headers with blank strings for cleaner output
    df.fillna("", inplace=True)
    
    # Reorder columns to ensure consistency
    cols = ["Filename", "PageNo", "Header1", "Header2", "Header3", "Text"]
    # Ensure columns exist even if no headers were found
    for c in cols:
        if c not in df.columns: df[c] = ""
    df = df[cols]

    df.to_csv(output_csv_path, index=False, encoding='utf-8')
    t1 = time.perf_counter()
    print(f"[Stats] DataFrame Construction & Save: {t1 - t0:.4f} sec")

    # TIMING: Total
    print(f"--- Completed in {time.perf_counter() - t_start:.4f} seconds ---")
    print(f"Rows Generated: {len(df)}")

if __name__ == "__main__":
    # Update these paths
    INPUT_XML = "COC26-INS-2018.xml" 
    OUTPUT_CSV = "parsed_database_table.csv"
    
    if os.path.exists(INPUT_XML):
        main(INPUT_XML, OUTPUT_CSV)
    else:
        print("File not found. Please check input path.")