import fitz
import math
from dataclasses import dataclass, field
from typing import Tuple

@dataclass(slots=True)
class PageElement:
    """
    Production-grade representation of a document element.
    """
    # --- 1. ID & Structure ---
    page_num: int
    block_id: int        # KEY: Groups spans into logical paragraphs
    
    # --- 2. Geometry ---
    rect: fitz.Rect      # The bounding box
    
    # --- 3. Content ---
    text: str            
    element_type: str    # 'text', 'image', 'drawing'
    
    # --- 4. Orientation (NEW) ---
    # Default is Horizontal Left-to-Right: (1.0, 0.0)
    dir: Tuple[float, float] = (1.0, 0.0) 
    
    # --- 5. Style & Typography ---
    font_name: str = ""
    font_size: float = 0.0
    color: int = 0
    flags: int = 0
    
    # --- 6. Advanced Typographical Metrics ---
    ascender: float = 0.0
    descender: float = 0.0
    origin_y: float = 0.0    # The baseline Y-coordinate
    
    # --- 7. Special Properties ---
    alpha: int = 255     # Transparency (Watermark detection)
    image_dpi: int = 0   # Resolution (Logo detection)

    # --- Helper Properties ---
    @property
    def is_vertical(self) -> bool:
        """
        Returns True if text is vertical (sidebar revision numbers).
        Checks if x-component of direction is 0.
        """
        return self.dir[0] == 0

    @property
    def is_horizontal(self) -> bool:
        """Returns True if text is standard horizontal."""
        return self.dir[1] == 0

    @property
    def rotation_angle(self) -> int:
        """
        Returns the rotation angle in degrees.
        (1, 0) -> 0 deg
        (0, -1) -> 90 deg (Vertical going up)
        """
        # Calculate angle from cosine(dir[0]) and sine(dir[1])
        angle_rad = math.atan2(self.dir[1], self.dir[0])
        return int(math.degrees(angle_rad))


######## Read

import sys

def extract_complete_elements(page: fitz.Page) -> list[PageElement]:
    elements = []
    
    # Use DEHYPHENATE to handle split words like "Confi- dential"
    raw_dict = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)

    for block in raw_dict["blocks"]:
        block_id = block.get("number", 0)
        
        # --- IMAGES (Type 1) ---
        if block["type"] == 1:
            # Images don't have 'dir' in the same way text lines do.
            # We assume standard orientation (1, 0) or derive from transform if needed.
            
            # Simple DPI calc (native width / pdf width * 72)
            w_pts = (block["bbox"][2] - block["bbox"][0])
            dpi = (block["width"] / w_pts * 72) if w_pts > 0 else 0
            
            elements.append(PageElement(
                page_num=page.number + 1,
                block_id=block_id,
                rect=fitz.Rect(block["bbox"]),
                text="<image>",
                element_type="image",
                dir=(1.0, 0.0), # Default for images
                image_dpi=int(dpi)
            ))
            continue

        # --- TEXT (Type 0) ---
        for line in block["lines"]:
            # EXTRACT DIRECTION HERE (From Line Level)
            # Default to horizontal (1.0, 0.0) if missing
            current_dir = line.get("dir", (1.0, 0.0))
            
            for span in line["spans"]:
                # Optimization: Intern font names
                f_name = sys.intern(span["font"])
                
                elem = PageElement(
                    page_num=page.number + 1,
                    block_id=block_id,
                    rect=fitz.Rect(span["bbox"]),
                    text=span["text"].strip(),
                    element_type="text",
                    
                    # --- NEW: Assign Direction ---
                    dir=current_dir,
                    
                    # Style
                    font_name=f_name,
                    font_size=span["size"],
                    color=span["color"],
                    flags=span["flags"],
                    
                    # Metrics
                    ascender=span['ascender'],
                    descender=span['descender'],
                    origin_y=span['origin'][1], 
                    alpha=span.get('alpha', 255)
                )
                
                if elem.text:
                    elements.append(elem)

    return elements