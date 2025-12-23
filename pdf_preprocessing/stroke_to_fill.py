'''Prompt: you are an avid python programmer. You have to write a well organised optimised function to implement stroke-to-fill normalization(Rectification).
input is page.get_drawings from PyMuPDF library and output is also of the same type.'''

'''
This is a sophisticated problem in PDF data extraction. In the wild, many "solid rectangles" (like table separators, underlines, or progress bars) are actually drawn as thick single lines (strokes). This inconsistency confuses geometric algorithms that expect all solid blocks to be "fills".

The following function identifies these iso-oriented (horizontal or vertical) strokes and converts them into filled rectangles.
'''

########################################################################################################################################

import fitz  # PyMuPDF
from typing import List, Dict, Any

def normalize_strokes_to_fills(drawings: List[Dict[str, Any]], 
                               width_tolerance: float = 0.5) -> List[Dict[str, Any]]:
    """
    Converts vector strokes (lines) into equivalent filled rectangles.
    
    This function looks for drawings that are:
    1. Pure strokes (have stroke color, no fill color).
    2. Iso-oriented lines (perfectly horizontal or vertical).
    3. Have a non-trivial width.

    It mutates these objects to become "Filled Rectangles" visually identical 
    to the original stroke. This normalizes the data for downstream layout analysis.

    Args:
        drawings (List[Dict]): The output from page.get_drawings().
        width_tolerance (float): Minimum stroke width to consider for conversion. 
                                 Ignores hairlines (< 0.5) which are usually borders.

    Returns:
        List[Dict]: A new list of drawing dictionaries with strokes rectified.
    """
    
    cleaned_drawings = []

    for path in drawings:
        # Create a shallow copy to avoid mutating the original dataset unpredictably
        # We perform a shallow copy because drawing dicts are flat enough for our needs here,
        # but deepcopy is safer if you plan to modify nested 'items'.
        new_path = path.copy()
        
        # --- FILTERING CRITERIA ---
        
        # 1. Must have a stroke width (width) and stroke color (color)
        width = new_path.get("width", 0)
        stroke_color = new_path.get("color")
        fill_color = new_path.get("fill")
        items = new_path.get("items", [])

        # 2. Skip if it already has a fill (it's likely a complex shape or outlined box)
        if fill_color is not None:
            cleaned_drawings.append(new_path)
            continue

        # 3. Skip if stroke is missing, invisible, or too thin (hairlines)
        if stroke_color is None or width is None or width < width_tolerance:
            cleaned_drawings.append(new_path)
            continue

        # 4. Check if the path is a single line segment
        # We are only interested in converting single lines "('l', p1, p2)" 
        # into rectangles. We do not touch curves ('c') or existing rects ('re').
        if len(items) != 1 or items[0][0] != "l":
            cleaned_drawings.append(new_path)
            continue

        # --- RECTIFICATION LOGIC ---
        
        # Extract line coordinates
        # item structure: ("l", Point(x1, y1), Point(x2, y2))
        cmd, p1, p2 = items[0]
        
        # Determine orientation with a small epsilon for float precision
        is_vertical = abs(p1.x - p2.x) < 0.01
        is_horizontal = abs(p1.y - p2.y) < 0.01

        if not (is_vertical or is_horizontal):
            # It's a diagonal line. Converting this to an axis-aligned rect 
            # is geometrically incorrect. Keep as is.
            cleaned_drawings.append(new_path)
            continue

        # Calculate the new filled rectangle geometry
        # Visual Logic: The stroke is centered on the line. 
        # We must expand outwards by width / 2.
        half_w = width / 2
        
        if is_horizontal:
            # Expand Y axis
            top = min(p1.y, p2.y) - half_w
            bottom = max(p1.y, p2.y) + half_w
            left = min(p1.x, p2.x)
            right = max(p1.x, p2.x)
        else: # is_vertical
            # Expand X axis
            left = min(p1.x, p2.x) - half_w
            right = max(p1.x, p2.x) + half_w
            top = min(p1.y, p2.y)
            bottom = max(p1.y, p2.y)

        # Create the new Rect object
        new_rect = fitz.Rect(left, top, right, bottom)

        # --- UPDATE THE DRAWING OBJECT ---
        
        # 1. Swap Stroke Color to Fill Color
        new_path["fill"] = stroke_color  # The stroke color becomes the fill
        new_path["color"] = None         # Remove the stroke border
        
        # 2. Update the geometry item to be a Rectangle ("re") instead of Line ("l")
        new_path["items"] = [("re", new_rect)]
        
        # 3. Update the logical bounding box
        # Note: PyMuPDF's 'rect' usually already accounts for stroke width,
        # but re-calculating ensures strict consistency.
        new_path["rect"] = new_rect
        
        # 4. Reset width (filled shapes don't strictly need a width, but 0 is safe)
        new_path["width"] = 0 
        
        # 5. Update type (Optional, usually 'f' for fill, 's' for stroke)
        new_path["type"] = "f" 

        cleaned_drawings.append(new_path)

    return cleaned_drawings


############################################################################################################

''' 
Why this logic is optimized

1. Selective Targeting (len(items) == 1): It does not blindly convert every stroke. It specifically targets single line segments. It ignores complex paths (curves, multi-segment lines) because converting those to rectangles destroys the shape.
2. Geometry Math (Half-width expansion):
  A stroke of width=10 at y=100 visually covers y=95 to y=105.
  The function correctly calculates y ± width/2 to ensure the new "filled" rectangle occupies the exact same pixels as the old "stroked" line.
3. Property Swapping: It correctly moves the color (stroke) to fill and sets the width to 0. This ensures that if you render this new data, it looks identical to the original.
4. Tolerance: It uses width_tolerance. Thin lines (hairlines < 0.5pt) are usually borders or underlines for text and should often remain lines. Thick lines (> 2.0pt) are usually visual separators or bars that act like blocks.
'''

'''
Example Usage:
import fitz

doc = fitz.open("input.pdf")
page = doc[0]

# 1. Get raw drawings
raw_drawings = page.get_drawings()

# 2. Rectify
clean_drawings = normalize_strokes_to_fills(raw_drawings)

# 3. Verify (Optional: Print changes)
print(f"Original Count: {len(raw_drawings)}")
print(f"Processed Count: {len(clean_drawings)}")

# Example check of a converted item
for d in clean_drawings:
    if d["type"] == "f" and d["items"][0][0] == "re":
        # This was potentially a stroke before
        pass
'''
