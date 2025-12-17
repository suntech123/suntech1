from dataclasses import dataclass
from typing import Literal

@dataclass(slots=True)
class VisualLine:
    """
    Represents a visual separator (border, grid line, or thin filled rectangle).
    """
    x0: float
    y0: float
    x1: float
    y1: float
    orientation: Literal['H', 'V', 'RECT'] # Horizontal, Vertical, or Box
    thickness: float
    is_fill: bool  # True if it came from a 'fill' (background), False if 'stroke'

    @property
    def length(self):
        return max(self.x1 - self.x0, self.y1 - self.y0)

    @property
    def center(self):
        return ((self.x0 + self.x1) / 2, (self.y0 + self.y1) / 2)

# --- Transformer Function ---
def parse_drawings_to_lines(drawings: list) -> list[VisualLine]:
    visuals = []
    
    for path in drawings:
        # The 'rect' in the dict is the bounding box of the whole path
        rect = path["rect"]
        
        # Calculate dimensions
        width = rect.width
        height = rect.height
        
        # 1. Classification Logic (Crucial for Tables)
        # Identify if this vector is a Horizontal Line, Vertical Line, or Block
        
        # Heuristic: If width is > 10x height, it's a Horizontal Separator
        if width > height * 5:
            orientation = 'H'
        # Heuristic: If height > 10x width, it's a Vertical Separator
        elif height > width * 5:
            orientation = 'V'
        else:
            orientation = 'RECT' # Likely a cell shading or a square box

        # 2. Optimization: Filter out tiny noise (dots/specks)
        if width < 1 and height < 1:
            continue

        visuals.append(VisualLine(
            x0=rect.x0, y0=rect.y0, x1=rect.x1, y1=rect.y1,
            orientation=orientation,
            thickness=min(width, height), # Thickness is the smaller dimension
            is_fill=(path["type"] == 'f')
        ))
        
    return visuals