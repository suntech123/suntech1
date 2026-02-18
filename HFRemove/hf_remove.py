import fitz  # PyMuPDF
from dataclasses import dataclass, field

@dataclass(slots=True)
class PageElement:
    """
    Memory-optimized representation of a document element.
    Using slots prevents the creation of __dict__ for every instance.
    """
    # --- Core Geometry & Content ---
    rect: fitz.Rect
    text: str = ""
    element_type: str = "text"  # Renamed from 'type' to avoid shadowing built-in
    page_num: int = 0
    
    # --- Style Metadata ---
    font_size: float = 0.0
    font_name: str = ""
    color: int = 0
    flags: int = 0
    
    # --- Helper Properties (Computed, no memory cost) ---
    @property
    def is_bold(self) -> bool:
        """Checks flags (2^4) and font name for bold indicators."""
        return (self.flags & 16) or ("bold" in self.font_name.lower())

    @property
    def is_italic(self) -> bool:
        """Checks flags (2^1) and font name for italic indicators."""
        return (self.flags & 2) or ("italic" in self.font_name.lower())

    @property
    def area(self) -> float:
        return self.rect.width * self.rect.height

    @property
    def y_mid(self) -> float:
        """Useful for clustering text on the same line."""
        return (self.rect.y0 + self.rect.y1) / 2