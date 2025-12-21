'''Prompt: i have observed "opacity" key is not present in output but "stroke_opacity" is present. is it due to library version'''


'''Yes, you are absolutely correct. This is due to a change in the PyMuPDF (fitz) library version.
Starting from PyMuPDF version 1.18.17, the single opacity key was removed and split into two separate keys to allow for more precise control:
stroke_opacity: Controls the transparency of the lines/borders.[1]
fill_opacity: Controls the transparency of the inner fill color.[1][2]
Why did they change this?
In PDF specification, it is possible for a shape to have a solid border but a transparent center (or vice versa).[1] The old opacity key was too simple because it applied to the whole object.[1] The new keys reflect the actual capabilities of PDF graphics better.
How to fix your code
You should check for both keys to be safe.[1] If you want a single "opacity" value to determine if something is visible, you should check if both are zero (invisible).[1]
Here is the updated logic for your noise reduction function:'''


# Old way (will fail in newer versions like yours)
# opacity = path.get("opacity", 1.0) 

# New way (Robust for all versions)
stroke_op = path.get("stroke_opacity", 1.0)
fill_op = path.get("fill_opacity", 1.0)

# The Logic:
# If an object has NO stroke (None) or transparent stroke (0)
# AND
# It has NO fill (None) or transparent fill (0)
# THEN -> It is invisible.

is_stroke_invisible = (path.get("color") is None) or (stroke_op == 0)
is_fill_invisible = (path.get("fill") is None) or (fill_op == 0)

if is_stroke_invisible and is_fill_invisible:
    continue  # Treat as noise

#######################################################
'''Quick Summary:
If you see stroke_opacity: You are on version 1.18.17 or newer.[1][2][3]
Action: Replace references to path["opacity"] with path.get("stroke_opacity", 1) and path.get("fill_opacity", 1).'''


################################################### Complete Code Below ########################################################################

'''Prompt : write the complete function again'''

'''This version includes:
  1. The "Safe Area" Logic: It removes noise trapped in the margins (defined by edge_tolerance) but keeps objects that cross from the margin into the main content.
  2. Version Compatibility: It uses stroke_opacity and fill_opacity instead of the old opacity key.
  3. Robust Visibility Checks: It correctly identifies invisible objects even if they have a color set but opacity is 0.'''


import fitz  # PyMuPDF

def get_clean_page_drawings(page: fitz.Page, 
                            speck_threshold: float = 2.0, 
                            ignore_white: bool = True,
                            edge_tolerance: float = 15.0):
    """
    Extracts vector drawings from a PyMuPDF page, filtering out noise based on size, 
    visibility, and margin placement.

    Args:
        page (fitz.Page): The page object to process.
        speck_threshold (float): Max dimensions (in points) to consider a 'speck'.
        ignore_white (bool): If True, filters out white-on-white shapes.
        edge_tolerance (float): The 'Safe Area' margin in points. 
                                Objects completely inside this margin (or off-page) are removed.
                                Objects crossing from margin to center are KEPT.

    Returns:
        list: A list of clean drawing dictionaries.
    """
    
    raw_drawings = page.get_drawings()
    clean_drawings = []
    
    # 1. Define the "Safe Content Area"
    # We shrink the page rect by the tolerance.
    # Any object that does NOT touch this inner rectangle is considered "margin noise".
    page_rect = page.rect
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

        rect = path["rect"]

        # --- CHECK 2: MARGIN & OFF-PAGE NOISE ---
        # If the drawing does not touch the Safe Area, it means it is either:
        # a) Completely off-screen
        # b) Trapped entirely inside the 'edge_tolerance' margin
        if not rect.intersects(safe_rect):
            continue

        # --- CHECK 3: SPECKS (TINY DOTS) ---
        # If both width and height are smaller than threshold, it's a dot/speck.
        if rect.width < speck_threshold and rect.height < speck_threshold:
            continue

        # --- CHECK 4: VISIBILITY (OPACITY) ---
        # Handle newer PyMuPDF versions splitting opacity into stroke/fill
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
        # Filters shapes that are white fill with no visible border (often used for masking)
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


#################




