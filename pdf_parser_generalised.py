import xml.etree.ElementTree as ET
import pandas as pd
import statistics
import time
import os
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any

# ==========================================
# 1. OPTIMIZED STRUCTURES
# ==========================================

@dataclass(frozen=True)
class FontSpec:
    size: int; family: str; color: str

@dataclass
class TextFragment:
    __slots__ = ['text', 'top', 'left', 'width', 'height', 'font_id', 'right', 'bottom']
    text: str; top: int; left: int; width: int; height: int
    font_id: str; right: int; bottom: int

    @classmethod
    def from_node(cls, node: ET.Element) -> 'TextFragment':
        top = int(node.get('top'))
        left = int(node.get('left'))
        width = int(node.get('width'))
        height = int(node.get('height'))
        text = "".join(node.itertext()).strip()
        return cls(text, top, left, width, height, node.get('font'), left + width, top + height)

class TextLine:
    __slots__ = ['fragments', 'top', 'bottom', 'left']
    def __init__(self, first_fragment: TextFragment):
        self.fragments = [first_fragment]
        self.top = first_fragment.top
        self.bottom = first_fragment.bottom
        self.left = first_fragment.left

    def add(self, fragment: TextFragment):
        self.fragments.append(fragment)
        if fragment.bottom > self.bottom: self.bottom = fragment.bottom

    def get_text_content(self, space_threshold: int = 3) -> str:
        if not self.fragments: return ""
        self.fragments.sort(key=lambda f: f.left)
        buffer = [self.fragments[0].text]
        for i in range(1, len(self.fragments)):
            curr = self.fragments[i]; prev = self.fragments[i-1]
            if (curr.left - prev.right) > space_threshold: buffer.append(" ")
            buffer.append(curr.text)
        return "".join(buffer)

@dataclass
class HeaderContext:
    """
    Generalized State Machine.
    Stores headers in a dictionary: {1: "Title", 2: "Subtitle", ...}
    """
    filename: str
    page_num: int
    # Dynamic dictionary: Key=Level(int), Value=Text(str)
    headers: Dict[int, str] = field(default_factory=dict)

    def update_page_num(self, new_page_num: int):
        self.page_num = new_page_num

    def update_header(self, level: int, text: str):
        """
        Updates level N and clears all levels deeper than N.
        """
        self.headers[level] = text
        
        # Clear any header deeper than the current one (e.g., if updating H2, clear H3, H4...)
        # We convert to list to avoid runtime error during iteration
        for existing_level in list(self.headers.keys()):
            if existing_level > level:
                del self.headers[existing_level]

    def to_dict(self, body_text: str) -> Dict[str, Any]:
        """Dynamically builds row dict based on active headers."""
        row = {
            "Filename": self.filename,
            "PageNo": self.page_num,
            "Text": body_text
        }
        # Inject active headers
        for level, text in self.headers.items():
            row[f"Header{level}"] = text
        return row

# ==========================================
# 2. DYNAMIC GLOBAL ANALYSIS
# ==========================================

def generate_global_role_map(root: ET.Element, font_map: Dict[str, FontSpec]) -> Dict[str, Union[int, str]]:
    """
    Maps Font IDs to roles.
    Returns: 
       - Integer (1, 2, 3...) for Headers.
       - 'body' string for Body text.
    """
    font_counts = {}
    
    # 1. Tally volume of text per font
    for text_node in root.findall('.//text'):
        fid = text_node.get('font')
        if fid in font_map:
            text_len = len("".join(text_node.itertext()).strip())
            if text_len > 0:
                font_counts[fid] = font_counts.get(fid, 0) + text_len

    if not font_counts: return {}

    # 2. Identify Body (Most frequent)
    body_fid = max(font_counts, key=font_counts.get)
    body_size = font_map[body_fid].size

    # 3. Identify Candidates (Larger than Body)
    candidates = set()
    for fid in font_counts:
        if font_map[fid].size > body_size:
            candidates.add(font_map[fid].size)
    
    # Sort sizes descending (Biggest is H1, Next is H2...)
    sorted_sizes = sorted(list(candidates), reverse=True)
    
    # 4. Create Map
    role_map = {}
    
    # Map Headers (Dynamic Depth)
    # enumerate(sorted_sizes, 1) means start counting at 1 -> H1, H2...
    size_to_level = {size: i for i, size in enumerate(sorted_sizes, 1)}
    
    for fid in font_counts:
        f_size = font_map[fid].size
        if f_size in size_to_level:
            role_map[fid] = size_to_level[f_size] # Assigns int: 1, 2, 3...
        else:
            role_map[fid] = 'body'

    print(f"Detected {len(sorted_sizes)} Header Levels above Body Size {body_size}.")
    return role_map

# ==========================================
# 3. EXTRACTION UTILS
# ==========================================

def calculate_dynamic_y_tolerance(fragments: List[TextFragment]) -> int:
    if not fragments: return 3
    heights = [f.height for f in fragments]
    if not heights: return 3
    try: dom = statistics.mode(heights)
    except: dom = statistics.median(heights)
    
    frags = sorted(fragments, key=lambda f: f.top)
    jitter = [frags[i].top - frags[i-1].top for i in range(1, len(frags)) 
              if 0 <= (frags[i].top - frags[i-1].top) < (dom * 0.5)]
    
    if not jitter: return max(2, int(dom * 0.1))
    calc = int(statistics.mean(jitter) + (2 * (statistics.stdev(jitter) if len(jitter)>1 else 0)))
    return max(2, min(calc, int(dom * 0.3)))

def extract_text_lines(page: ET.Element) -> List[TextLine]:
    frags = [TextFragment.from_node(n) for n in page.findall('text')]
    frags = [f for f in frags if f.text]
    if not frags: return []
    y_tol = calculate_dynamic_y_tolerance(frags)
    frags.sort(key=lambda f: (f.top, f.left))
    lines = [TextLine(frags[0])]
    for i in range(1, len(frags)):
        if abs(frags[i].top - lines[-1].top) <= y_tol: lines[-1].add(frags[i])
        else: lines.append(TextLine(frags[i]))
    return lines

# ==========================================
# 4. PAGE PROCESSOR (Generalized)
# ==========================================

def parse_page_to_data_rows(lines: List[TextLine], 
                            font_map: Dict[str, FontSpec], 
                            role_map: Dict[str, Union[int, str]], 
                            context: HeaderContext) -> List[Dict]:
    
    body_buffer = []
    header_buffer = []
    
    # active_header_role is now an Integer (or None)
    active_header_role: Optional[int] = None 
    
    rows = []

    def commit_body():
        if body_buffer:
            rows.append(context.to_dict(" ".join(body_buffer)))
            body_buffer.clear()

    def commit_header():
        if active_header_role is not None and header_buffer:
            context.update_header(active_header_role, " ".join(header_buffer))
            header_buffer.clear()

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')

        # === 1. HEADER LOGIC ===
        # Check if role is an Integer (meaning it's a Header level)
        if isinstance(role, int):
            
            # Case A: Continuing the exact same header level (multiline)
            if active_header_role is not None and role == active_header_role:
                header_buffer.append(text)
                continue
            
            # Case B: Switching from one header to another (e.g. H1 -> H2, or H2 -> H1)
            # Or switching from Body -> Header
            if active_header_role is not None:
                commit_header() # Commit the previous header
            
            commit_body() # Commit any pending body text
            
            # Start new header
            active_header_role = role
            header_buffer.append(text)

        # === 2. BODY LOGIC ===
        else:
            # If we were reading a header, commit it now
            if active_header_role is not None:
                commit_header()
                active_header_role = None
            
            # Paragraph detection
            if i > 0 and body_buffer:
                prev = lines[i-1]
                gap = line.top - prev.bottom
                fs = font_map[fid].size if fid in font_map else 12
                if gap > (fs * 0.6): commit_body()
            
            body_buffer.append(text)

    # End of Page Cleanup
    if active_header_role is not None: commit_header()
    commit_body()
    
    return rows

# ==========================================
# 5. MAIN
# ==========================================

def main(xml_path: str, output_path: str):
    t0 = time.perf_counter()
    print(f"Reading {xml_path}...")
    try: root = ET.parse(xml_path).getroot()
    except Exception as e: return print(e)

    fmap = {}
    for f in root.findall('.//fontspec'):
        fmap[f.get('id')] = FontSpec(int(f.get('size',0)), f.get('family',''), f.get('color',''))

    # 1. Global Analysis (Dynamic Depth)
    global_roles = generate_global_role_map(root, fmap)
    
    # 2. Setup Persistent Context
    ctx = HeaderContext(os.path.basename(xml_path), 0)
    
    all_rows = []
    pages = root.findall('page')
    
    for i, page in enumerate(pages):
        ctx.update_page_num(i + 1)
        lines = extract_text_lines(page)
        all_rows.extend(parse_page_to_data_rows(lines, fmap, global_roles, ctx))

    # 3. Create DataFrame with Dynamic Columns
    df = pd.DataFrame(all_rows)
    
    if not df.empty:
        # Determine all Header columns present in the data (Header1, Header2, Header5...)
        header_cols = sorted([c for c in df.columns if c.startswith("Header")], 
                             key=lambda x: int(x.replace("Header", "")))
        
        # Define Final Column Order
        final_cols = ["Filename", "PageNo"] + header_cols + ["Text"]
        
        # Ensure all columns exist (fill NaN with blank)
        for c in final_cols:
            if c not in df.columns: df[c] = ""
        
        df = df[final_cols]
        df.fillna("", inplace=True)
    
    df.to_csv(output_path, index=False)
    print(f"Done in {time.perf_counter()-t0:.2f}s. Rows: {len(df)}")
    if not df.empty:
        print(f"Max Header Depth Found: {header_cols[-1] if header_cols else 'None'}")

if __name__ == "__main__":
    main("COC26-INS-2018.xml", "output_generalized.csv")