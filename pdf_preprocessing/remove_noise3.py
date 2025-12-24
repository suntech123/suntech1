import fitz  # PyMuPDF
from typing import List, Dict, Any

def get_clean_drawings(raw_drawings: List[Dict[str, Any]], 
                       page_rect: fitz.Rect,
                       speck_threshold: float = 2.0, 
                       ignore_white: bool = True,
                       edge_tolerance: float = 15.0) -> List[Dict[str, Any]]:
    """
    Filters a list of vector drawings (from page.get_drawings()), removing noise based on size, 
    visibility, and margin placement.

    Args:
        raw_drawings (list): The output from page.get_drawings().
        page_rect (fitz.Rect): The dimensions of the page (page.rect). 
                               Required to calculate margins.
        speck_threshold (float): Max dimensions (in points) to consider a 'speck'.
        ignore_white (bool): If True, filters out white-on-white shapes.
        edge_tolerance (float): The 'Safe Area' margin in points. 
                                Objects completely inside this margin (or off-page) are removed.

    Returns:
        list: A filtered list of drawing dictionaries.
    """

    clean_drawings = []

    # 1. Define the "Safe Content Area"
    # We use the provided page_rect to calculate the inner safe zone.
    safe_rect = fitz.Rect(
        page_rect.x0 + edge_tolerance,
        page_rect.y0 + edge_tolerance,
        page_rect.x1 - edge_tolerance,
        page_rect.y1 - edge_tolerance
    )

    for path in raw_drawings:
        # --- CHECK 1: EMPTY PATHS ---
        if not path["items"]:
            continue

        # The 'rect' in the path dictionary is usually a fitz.Rect, 
        # but if it was serialized/deserialized it might be a list. 
        # We ensure it is a fitz.Rect for the .intersects() method.
        path_rect = fitz.Rect(path["rect"])

        # --- CHECK 2: MARGIN & OFF-PAGE NOISE ---
        # If the drawing does not touch the Safe Area, it is noise.
        if not path_rect.intersects(safe_rect):
            continue

        # --- CHECK 3: SPECKS (TINY DOTS) ---
        if path_rect.width < speck_threshold and path_rect.height < speck_threshold:
            continue

        # --- CHECK 4: VISIBILITY (OPACITY) ---
        stroke_op = path.get("stroke_opacity", 1.0)
        fill_op = path.get("fill_opacity", 1.0)

        stroke_color = path.get("color") # None = no stroke
        fill_color = path.get("fill")    # None = no fill

        # Logic: Is the stroke invisible? (No color OR 0 opacity)
        is_stroke_invisible = (stroke_color is None) or (stroke_op == 0)

        # Logic: Is the fill invisible? (No fill OR 0 opacity)
        is_fill_invisible = (fill_color is None) or (fill_op == 0)

        # If BOTH are invisible, the object can't be seen
        if is_stroke_invisible and is_fill_invisible:
            continue

        # --- CHECK 5: WHITE-ON-WHITE (OPTIONAL) ---
        if ignore_white:
            is_white_fill = fill_color == (1.0, 1.0, 1.0)

            # A border is "missing" if it has no color, is white, or is transparent
            has_no_border = (stroke_color is None) or \
                            (stroke_color == (1.0, 1.0, 1.0)) or \
                            (stroke_op == 0)

            if is_white_fill and has_no_border:
                continue

        # If it passed all filters, keep it
        clean_drawings.append(path)

    return clean_drawings