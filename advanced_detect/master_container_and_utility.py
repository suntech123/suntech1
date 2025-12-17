import fitz
from dataclasses import dataclass, field
from typing import List, Literal, Tuple
from collections import Counter

# --- Your Optimized Data Structures (Recap) ---
@dataclass(slots=True)
class VisualLine:
    x0: float; y0: float; x1: float; y1: float
    orientation: Literal['H', 'V', 'RECT']
    thickness: float

@dataclass(slots=True)
class TextSpan:
    x0: float; y0: float; x1: float; y1: float
    text: str; font: str; size: float; flags: int
    
    @property
    def is_bold(self): return bool(self.flags & 16) or "Bold" in self.font

@dataclass(slots=True)
class PDFWord:
    x0: float; y0: float; x1: float; y1: float
    text: str

# --- Utility: Coordinate Clustering ---
def get_unique_axes(coords: List[float], tolerance: float = 3.0) -> int:
    """Returns number of unique lines after clustering close coordinates."""
    if not coords: return 0
    coords.sort()
    unique_count = 0
    last = -100.0
    for c in coords:
        if abs(c - last) > tolerance:
            unique_count += 1
            last = c
    return unique_count