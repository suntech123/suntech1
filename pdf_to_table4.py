import xml.etree.ElementTree as ET
import pandas as pd
import statistics
import time
import os
from dataclasses import dataclass
from typing import List, Dict, Optional

# ==========================================
# 1. STRUCTURES
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
    """Persistent State Machine across pages."""
    filename: str
    page_num: int
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None

    def update_page_num(self, new_page_num: int):
        self.page_num = new_page_num

    def update_header(self, level: str, text: str):
        if level == 'h1': self.h1, self.h2, self.h3 = text, None, None
        elif level == 'h2': self.h2, self.h3 = text, None
        elif level == 'h3': self.h3 = text

    def to_dict(self, body_text: str) -> Dict:
        return {
            "Filename": self.filename, "PageNo": self.page_num,
            "Header1": self.h1, "Header2": self.h2, "Header3": self.h3,
            "Text": body_text
        }

# ==========================================
# 2. CORE LOGIC
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

def determine_font_roles(font_map: Dict[str, FontSpec], lines: List[TextLine]) -> Dict[str, str]:
    if not lines: return {}
    counts = {}
    size_map = {}
    for l in lines:
        fid = l.fragments[0].font_id
        if fid not in font_map: continue
        size = font_map[fid].size
        counts[size] = counts.get(size, 0) + 1
        if size not in size_map: size_map[size] = set()
        size_map[size].add(fid)
    
    if not counts: return {}
    body_sz = max(counts, key=counts.get)
    sizes = sorted(counts.keys(), reverse=True)
    header_sz = [s for s in sizes if s > body_sz]
    
    roles = {}
    if len(header_sz) >= 1: 
        for fid in size_map[header_sz[0]]: roles[fid] = 'h1'
    if len(header_sz) >= 2: 
        for fid in size_map[header_sz[1]]: roles[fid] = 'h2'
    for sz in sizes:
        if sz <= body_sz:
            for fid in size_map[sz]: roles[fid] = 'body'
    return roles

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
# 3. PAGE PROCESSOR (Stateless Context)
# ==========================================

def parse_page_to_data_rows(lines: List[TextLine], font_map: Dict[str, FontSpec], context: HeaderContext) -> List[Dict]:
    role_map = determine_font_roles(font_map, lines)
    body_buf = []
    head_buf = []
    act_role = None
    rows = []

    def commit_body():
        if body_buf:
            rows.append(context.to_dict(" ".join(body_buf)))
            body_buf.clear()

    def commit_head():
        if act_role and head_buf:
            context.update_header(act_role, " ".join(head_buf))
            head_buf.clear()

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')

        if act_role and role == act_role:
            head_buf.append(text)
            continue
        
        if act_role and role != act_role:
            commit_head()
            act_role = None
            
        if role in ['h1', 'h2', 'h3']:
            commit_body()
            act_role = role
            head_buf.append(text)
        else:
            if i > 0 and body_buf:
                prev = lines[i-1]
                gap = line.top - prev.bottom
                fs = font_map[fid].size if fid in font_map else 12
                if gap > (fs * 0.6): commit_body()
            body_buf.append(text)

    if act_role: commit_head()
    commit_body()
    return rows

# ==========================================
# 4. MAIN
# ==========================================

def main(xml_path: str, output_path: str):
    t0 = time.perf_counter()
    print(f"Reading {xml_path}...")
    try: root = ET.parse(xml_path).getroot()
    except Exception as e: return print(e)

    fmap = {}
    for f in root.findall('.//fontspec'):
        fmap[f.get('id')] = FontSpec(int(f.get('size',0)), f.get('family',''), f.get('color',''))

    # INITIALIZE CONTEXT ONCE
    ctx = HeaderContext(os.path.basename(xml_path), 0)
    
    all_rows = []
    pages = root.findall('page')
    
    for i, page in enumerate(pages):
        # Update Page Number in Context
        ctx.update_page_num(i + 1)
        
        lines = extract_text_lines(page)
        # Pass the Persistent Context
        all_rows.extend(parse_page_to_data_rows(lines, fmap, ctx))

    df = pd.DataFrame(all_rows)
    cols = ["Filename", "PageNo", "Header1", "Header2", "Header3", "Text"]
    for c in cols: 
        if c not in df.columns: df[c] = ""
    
    df[cols].to_csv(output_path, index=False)
    print(f"Done in {time.perf_counter()-t0:.2f}s. Rows: {len(df)}")

if __name__ == "__main__":
    main("COC26-INS-2018.xml", "output_cross_page.csv")