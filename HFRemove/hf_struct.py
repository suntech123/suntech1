import fitz
from dataclasses import dataclass

@dataclass(slots=True)
class PageElement:
    """
    Comprehensive representation of a document element.
    Includes Geometry, Content, Typography, and Structural IDs.
    """
    # --- 1. ID & Structure ---
    page_num: int
    block_id: int        # KEY: Groups spans into paragraphs
    
    # --- 2. Geometry ---
    rect: fitz.Rect      # The bounding box (hitbox)
    
    # --- 3. Content ---
    text: str            # Empty if image/drawing
    element_type: str    # 'text', 'image', 'drawing'
    
    # --- 4. Style & Typography ---
    font_name: str
    font_size: float
    color: int
    flags: int           # Bold/Italic info
    
    # --- 5. Advanced Typographical Metrics (New) ---
    ascender: float      # Height above baseline (0 to 1)
    descender: float     # Depth below baseline (usually negative)
    origin_y: float      # The exact baseline Y-coordinate
    
    # --- 6. Special Properties ---
    alpha: int = 255     # Transparency (Watermark detection)
    image_dpi: int = 0   # Resolution (Logo detection)

    @property
    def is_header_candidate(self) -> bool:
        """Example helper: Checks if this looks like header text."""
        # Must be in top 20% OR be a distinct isolated block
        return True # (Implement logic based on rect.y1)



########extract data


def extract_complete_elements(page: fitz.Page) -> list[PageElement]:
    elements = []
    # Note: text_preserve_ligatures=False is usually better for NLP, 
    # but strictly following the user's desire for 'dict':
    raw_dict = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)

    for block in raw_dict["blocks"]:
        block_id = block["number"]
        
        # --- IMAGES ---
        if block["type"] == 1:
            # Calculate roughly the DPI (DPI = Native Pixels / PDF Inch)
            # PDF Inch = 72 units.
            # This is an approximation.
            w_pts = block["bbox"][2] - block["bbox"][0]
            if w_pts > 0:
                dpi = (block["width"] / w_pts) * 72
            else:
                dpi = 0
            
            elements.append(PageElement(
                page_num=page.number + 1,
                block_id=block_id,
                rect=fitz.Rect(block["bbox"]),
                text="<image>",
                element_type="image",
                font_name="", font_size=0, color=0, flags=0,
                ascender=0, descender=0, origin_y=block["bbox"][3],
                alpha=255, # Images usually don't report alpha in block dict same way
                image_dpi=int(dpi)
            ))
            continue

        # --- TEXT ---
        for line in block["lines"]:
            # 'dir' in line gives orientation if needed
            
            for span in line["spans"]:
                # Extracting the new Typography Metrics
                asc = span['ascender']
                desc = span['descender']
                origin = span['origin'] # Tuple (x, y)
                
                elem = PageElement(
                    page_num=page.number + 1,
                    block_id=block_id,
                    rect=fitz.Rect(span["bbox"]),
                    text=span["text"].strip(),
                    element_type="text",
                    font_name=span["font"], # Recommend sys.intern()
                    font_size=span["size"],
                    color=span["color"],
                    flags=span["flags"],
                    
                    # NEW FIELDS POPULATION
                    ascender=asc,
                    descender=desc,
                    origin_y=origin[1], # The baseline Y
                    alpha=span.get('alpha', 255),
                    image_dpi=0
                )
                if elem.text:
                    elements.append(elem)

    return elements
