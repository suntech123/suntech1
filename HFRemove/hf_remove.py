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




########

import sys
import fitz  # PyMuPDF
from typing import List

# ... (Insert your PageElement class definition here) ...

class PageParser:
    """
    Module responsible for ingesting PyMuPDF pages and converting them 
    into our optimized PageElement structures.
    """

    @staticmethod
    def extract_elements(page: fitz.Page) -> List[PageElement]:
        """
        Extracts Text, Images, and Vector Drawings from a page.
        Returns a flat list of PageElements.
        """
        elements: List[PageElement] = []
        page_num = page.number

        # ---------------------------------------------------------
        # 1. Extract TEXT and IMAGES via get_text("dict")
        # ---------------------------------------------------------
        # flags=fitz.TEXT_PRESERVE_LIGATURES prevents "fi" becoming a single unknown char
        # flags=fitz.TEXT_DEHYPHENATE helps rejoin words split across lines
        raw_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_LIGATURES | fitz.TEXT_DEHYPHENATE)

        for block in raw_dict["blocks"]:
            
            # --- Case A: Text Block (type=0) ---
            if block["type"] == 0:
                for line in block["lines"]:
                    for span in line["spans"]:
                        text_content = span["text"].strip()
                        
                        # Skip empty whitespace spans to save memory
                        if not text_content:
                            continue

                        # Optimization: Intern font names to save RAM
                        # (Healthcare docs repeat "Arial" thousands of times)
                        font_name = sys.intern(span["font"])

                        element = PageElement(
                            rect=fitz.Rect(span["bbox"]),
                            text=text_content,
                            element_type="text",
                            page_num=page_num,
                            # Style Metadata
                            font_size=span["size"],
                            font_name=font_name,
                            color=span["color"],
                            flags=span["flags"]
                        )
                        elements.append(element)

            # --- Case B: Image Block (type=1) ---
            # Crucial for detecting Logos in headers
            elif block["type"] == 1:
                element = PageElement(
                    rect=fitz.Rect(block["bbox"]),
                    text="<image>",  # Placeholder text
                    element_type="image",
                    page_num=page_num,
                    # Images don't have font properties, leave defaults
                    font_size=0.0,
                    font_name="",
                    color=0,
                    flags=0
                )
                elements.append(element)

        # ---------------------------------------------------------
        # 2. Extract VECTOR DRAWINGS (Lines/Rects)
        # ---------------------------------------------------------
        # Healthcare docs often use horizontal lines to separate headers.
        # We need these to determine the "cut-off" line.
        drawings = page.get_drawings()
        
        for draw in drawings:
            # We are interested in the visible area (rect) of the drawing
            draw_rect = fitz.Rect(draw["rect"])
            
            # Filter out invisible or tiny specks
            if draw_rect.width < 1 or draw_rect.height < 1:
                continue

            element = PageElement(
                rect=draw_rect,
                text="<drawing>",
                element_type="drawing",
                page_num=page_num,
                # Vector graphics usually don't map to text styles directly
                font_size=0.0,
                font_name="",
                color=draw.get("color", 0), # Some drawings track color
                flags=0
            )
            elements.append(element)

        return elements



######

def analyze_document(pdf_path: str):
    doc = fitz.open(pdf_path)
    
    all_elements = []

    for page in doc:
        # Populate data for this page
        page_elements = PageParser.extract_elements(page)
        
        # Example Logic: Inspect what we found
        print(f"--- Page {page.number + 1} ---")
        for elem in page_elements:
            
            # Logic: If it's in the top 10% and BOLD, it might be a header
            is_top_margin = elem.rect.y1 < page.rect.height * 0.10
            
            if is_top_margin and elem.is_bold:
                print(f"[POTENTIAL HEADER] Text: '{elem.text}' | Font: {elem.font_name} | Y: {elem.rect.y1}")
                
            # Logic: Detect Separator Lines
            if is_top_margin and elem.element_type == "drawing" and elem.rect.width > 200:
                print(f"[HEADER LINE DETECTED] Y: {elem.rect.y1}")

        # Store for global analysis if needed
        all_elements.extend(page_elements)

# Run it
# analyze_document("sample_policy.pdf")