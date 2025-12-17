from dataclasses import dataclass
from typing import List

@dataclass(slots=True)
class TextSpan:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    font: str
    size: float
    flags: int  # Critical for detecting Bold headers
    block_id: int # Useful to keep track of grouping

    @property
    def is_bold(self):
        # PyMuPDF flag: 2^4 (16) usually indicates Bold
        return bool(self.flags & 16) or "bold" in self.font.lower()

    @property
    def center_y(self):
        return (self.y0 + self.y1) / 2

def flatten_pdf_dict(page_dict: dict) -> List[TextSpan]:
    """
    Converts the nested dictionary into a flat list of rich text spans.
    """
    spans = []
    
    for block in page_dict.get("blocks", []):
        if block["type"] != 0: # 0 = Text, 1 = Image
            continue
            
        for line in block.get("lines", []):
            for span in line.get("spans", []):
                bbox = span["bbox"]
                spans.append(TextSpan(
                    x0=bbox[0],
                    y0=bbox[1],
                    x1=bbox[2],
                    y1=bbox[3],
                    text=span["text"],
                    font=span["font"],
                    size=span["size"],
                    flags=span["flags"],
                    block_id=block["number"]
                ))
    return spans

# Usage
# raw_dict = page.get_text("dict")
# flat_data = flatten_pdf_dict(raw_dict)
# Now you can sort them easily:
# flat_data.sort(key=lambda s: (s.y0, s.x0))