import xml.etree.ElementTree as ET
import statistics
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional

# ==========================================
# PART 1: DATA STRUCTURES
# ==========================================

@dataclass(frozen=True)
class FontSpec:
    """
    Immutable representation of a font style.
    Used in a Dictionary for O(1) lookups.
    """
    size: int
    family: str
    color: str

@dataclass
class TextFragment:
    """
    The atomic unit of text. 
    Using __slots__ for high memory efficiency (reduced footprint).
    """
    __slots__ = ['text', 'top', 'left', 'width', 'height', 'font_id', 'right', 'bottom']
    
    text: str
    top: int
    left: int
    width: int
    height: int
    font_id: str
    
    # Pre-calculated boundaries for faster sorting/rendering
    right: int
    bottom: int

    @classmethod
    def from_node(cls, node: ET.Element) -> 'TextFragment':
        """Factory: Parses an XML node into a TextFragment."""
        top = int(node.get('top'))
        left = int(node.get('left'))
        width = int(node.get('width'))
        height = int(node.get('height'))
        # .itertext() handles nested tags like <b>, strip() removes surrounding whitespace
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
    """
    Represents a visual line of text (group of fragments).
    """
    __slots__ = ['fragments', 'top', 'bottom', 'left']

    def __init__(self, first_fragment: TextFragment):
        self.fragments: List[TextFragment] = [first_fragment]
        self.top = first_fragment.top
        self.bottom = first_fragment.bottom
        self.left = first_fragment.left

    def add(self, fragment: TextFragment):
        self.fragments.append(fragment)
        # Update bounding box if needed (though top usually stays consistent)
        if fragment.bottom > self.bottom:
            self.bottom = fragment.bottom

    def sort_horizontally(self):
        """Ensures text reads Left -> Right."""
        self.fragments.sort(key=lambda f: f.left)

    def get_text_content(self, space_threshold: int = 3) -> str:
        """
        Reconstructs the line string, injecting spaces based on X-axis gaps.
        """
        if not self.fragments: return ""
        
        self.sort_horizontally()
        
        buffer = [self.fragments[0].text]
        
        for i in range(1, len(self.fragments)):
            curr = self.fragments[i]
            prev = self.fragments[i-1]
            
            # Gap Logic: If distance between prev.end and curr.start > threshold, add space
            gap = curr.left - prev.right
            if gap > space_threshold:
                buffer.append(" ")
            
            buffer.append(curr.text)
            
        return "".join(buffer)

# ==========================================
# PART 2: STATISTICAL HELPERS
# ==========================================

def calculate_dynamic_y_tolerance(fragments: List[TextFragment]) -> int:
    """
    Statistically determines the acceptable Y-axis jitter to consider 
    two fragments as being on the 'same line'.
    """
    if not fragments: return 3
    
    # 1. Determine Dominant Font Height (Mode)
    heights = [f.height for f in fragments]
    if not heights: return 3
    
    try:
        dominant_height = statistics.mode(heights)
    except statistics.StatisticsError:
        dominant_height = statistics.median(heights)

    # 2. Analyze Vertical Gaps (Jitter vs Line Breaks)
    sorted_by_top = sorted(fragments, key=lambda f: f.top)
    jitter_values = []
    
    for i in range(1, len(sorted_by_top)):
        diff = sorted_by_top[i].top - sorted_by_top[i-1].top
        
        # Filter: Only consider small shifts.
        # If the gap is > 50% of font height, it's likely a new line, not jitter.
        if 0 <= diff < (dominant_height * 0.5):
            jitter_values.append(diff)

    # 3. Calculate Threshold (Mean + 2 StdDev)
    if not jitter_values:
        return max(2, int(dominant_height * 0.1))

    mean_jitter = statistics.mean(jitter_values)
    std_dev_jitter = statistics.stdev(jitter_values) if len(jitter_values) > 1 else 0
    
    # Cover 95% of jitter cases
    calc_tolerance = int(mean_jitter + (2 * std_dev_jitter))
    
    # 4. Clamp results (Min 2px, Max 30% of font height)
    max_limit = int(dominant_height * 0.3)
    final_tolerance = max(2, min(calc_tolerance, max_limit))
    
    return final_tolerance

# ==========================================
# PART 3: XML & METADATA PROCESSING
# ==========================================

def get_xml_root(file_path: str) -> Optional[ET.Element]:
    try:
        tree = ET.parse(file_path)
        return tree.getroot()
    except Exception as e:
        print(f"Error parsing XML: {e}")
        return None

def sanitize_xml_root(root: ET.Element) -> ET.Element:
    """Removes empty/whitespace-only text nodes from the tree."""
    removed_count = 0
    for page in root.findall('page'):
        to_remove = []
        for text in page.findall('text'):
            content = "".join(text.itertext())
            if not content.strip():
                to_remove.append(text)
        
        for node in to_remove:
            page.remove(node)
            removed_count += 1
    
    print(f"Sanitization: Removed {removed_count} ghost/empty text fragments.")
    return root

def create_font_map(root: ET.Element) -> Dict[str, FontSpec]:
    """Creates an O(1) lookup dictionary for font attributes."""
    font_map = {}
    for spec in root.findall('.//fontspec'):
        font_id = spec.get('id')
        try:
            size = int(spec.get('size', 0))
        except ValueError:
            size = 0
            
        font_map[font_id] = FontSpec(
            size=size,
            family=spec.get('family', 'Unknown'),
            color=spec.get('color', '#000000')
        )
    return font_map

# ==========================================
# PART 4: LAYOUT LOGIC
# ==========================================

def process_page(page_node: ET.Element, font_map: Dict[str, FontSpec]) -> str:
    """
    Core logic: Extracts, Sorts, Groups, and Renders text for a single page.
    """
    # 1. Extraction
    fragments = [TextFragment.from_node(node) for node in page_node.findall('text')]
    if not fragments:
        return ""

    # 2. Dynamic Calibration
    y_tolerance = calculate_dynamic_y_tolerance(fragments)

    # 3. Sorting (Top -> Left)
    fragments.sort(key=lambda f: (f.top, f.left))

    # 4. Line Grouping (The "Clustering")
    lines: List[TextLine] = []
    if fragments:
        current_line = TextLine(fragments[0])
        lines.append(current_line)
        
        for i in range(1, len(fragments)):
            frag = fragments[i]
            # Use dynamic tolerance to decide if on same line
            if abs(frag.top - current_line.top) <= y_tolerance:
                current_line.add(frag)
            else:
                current_line = TextLine(frag)
                lines.append(current_line)

    # 5. Page Reconstruction (Paragraph Handling)
    output_buffer = []
    if lines:
        output_buffer.append(lines[0].get_text_content())
        
        for i in range(1, len(lines)):
            curr = lines[i]
            prev = lines[i-1]
            
            # Get font size info for heuristic context
            font_id = prev.fragments[0].font_id
            font_size = font_map[font_id].size if font_id in font_map else 12
            
            # Paragraph Detection:
            # If vertical gap > 50% of font size, insert extra newline
            vertical_gap = curr.top - prev.bottom
            if vertical_gap > (font_size * 0.6):
                output_buffer.append("\n") # Paragraph break
            
            output_buffer.append(curr.get_text_content())

    return "\n".join(output_buffer)

# ==========================================
# PART 5: MAIN EXECUTION
# ==========================================

def main(xml_file_path: str, output_file_path: str):
    print(f"Processing {xml_file_path}...")
    
    # 1. Load
    root = get_xml_root(xml_file_path)
    if not root: return

    # 2. Sanitize
    root = sanitize_xml_root(root)

    # 3. Map Metadata
    font_map = create_font_map(root)
    print(f"Font Map: {len(font_map)} fonts loaded.")

    # 4. Process Pages
    full_text = []
    pages = root.findall('page')
    
    for i, page in enumerate(pages):
        page_text = process_page(page, font_map)
        full_text.append(page_text)
        print(f"Processed Page {i+1}/{len(pages)}")

    # 5. Save
    final_output = "\n\n--- PAGE BREAK ---\n\n".join(full_text)
    try:
        with open(output_file_path, "w", encoding="utf-8") as f:
            f.write(final_output)
        print(f"Success! Output saved to: {output_file_path}")
    except IOError as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    # Example Usage
    # Replace 'input.xml' with your actual file name
    INPUT_FILE = "input.xml" 
    OUTPUT_FILE = "reconstructed_text.txt"
    
    main(INPUT_FILE, OUTPUT_FILE)