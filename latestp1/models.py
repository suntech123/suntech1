# models.py
from dataclasses import dataclass, field
from typing import Optional

@dataclass
class RawLine:
    """Represents a single line of text extracted from PDF with metadata."""
    text: str
    font_name: str
    font_size: float
    page_number: int
    is_bold: bool

@dataclass
class ParsedSection:
    """Represents a finalized row for the CSV output."""
    header_l1: Optional[str] = None
    header_l2: Optional[str] = None
    header_l3: Optional[str] = None
    body_text: str = ""
    page_number: int = 0