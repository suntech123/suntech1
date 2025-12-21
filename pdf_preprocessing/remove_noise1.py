'''Prompt: Also could we check if we can remove noise which is not only at the exact boundary of the page but the boundary shorter to certail number of pixels inside from each side ie a tolerance limit.
        Could we also think this tolerance with number of pixels possible in the narrowest margin possible in standard documents'''



'''Yes, we can definitely do this. This is a common requirement when dealing with scanned documents (to remove "scanner shadows") or to ignore printer crop marks.
To achieve this, we introduce the concept of a "Safe Area" (or Content Box). Instead of checking if the object touches the page edge, we check if the object enters the safe content area.

The Logic: The "Safe Area" Check
If we define a tolerance (e.g., 50 pixels/points), we virtually shrink the page by that amount from all sides.

1. If a drawing is entirely inside the "margin zone" (it does not touch the Safe Area), we treat it as noise.
2. If a drawing crosses from the margin into the Safe Area (like a header line or a chart), we keep it.

1. Updated Code with Tolerance
Here is the updated function. I added an edge_tolerance parameter.'''

#### Code

import fitz  # PyMuPDF

def get_clean_page_drawings(page: fitz.Page, 
                            speck_threshold: float = 2.0, 
                            ignore_white: bool = True,
                            edge_tolerance: float = 0.0):
    """
    Args:
        edge_tolerance (float): Distance (in points) from the edge to consider 'margin noise'.
                                Objects completely within this margin are removed.
    """
    raw_drawings = page.get_drawings()
    clean_drawings = []
    
    # Get the physical page size
    page_rect = page.rect
    
    # Create the "Safe Area" (Page minus the tolerance margins)
    # Coordinates: (left+tol, top+tol, right-tol, bottom-tol)
    safe_rect = fitz.Rect(
        page_rect.x0 + edge_tolerance,
        page_rect.y0 + edge_tolerance,
        page_rect.x1 - edge_tolerance,
        page_rect.y1 - edge_tolerance
    )

    for path in raw_drawings:
        if not path["items"]: continue

        rect = path["rect"]
        
        # --- CRITERIA 1: OFF-PAGE & MARGIN NOISE ---
        # OLD LOGIC: if not rect.intersects(page_rect): continue
        
        # NEW LOGIC: 
        # We check if the rect touches the "Safe Area".
        # If it returns False, it means the object is either off-page 
        # OR "trapped" entirely inside the tolerance margin.
        if not rect.intersects(safe_rect):
            continue

        # --- CRITERIA 2: SIZE (SPECKS) ---
        if rect.width < speck_threshold and rect.height < speck_threshold:
            continue

        # --- CRITERIA 3: INVISIBLE / WHITE ---
        stroke_op = path.get("opacity", 1.0)
        fill_op = path.get("fill_opacity", 1.0)
        
        if stroke_op == 0 and fill_op == 0:
            continue

        stroke_color = path.get("color")
        fill_color = path.get("fill")
        
        if stroke_color is None and fill_color is None:
            continue

        if ignore_white:
            is_white_fill = fill_color == (1.0, 1.0, 1.0)
            has_no_border = stroke_color is None or stroke_color == (1.0, 1.0, 1.0)
            if is_white_fill and has_no_border:
                continue

        clean_drawings.append(path)

    return clean_drawings



###############################################################################################################################################

'''2. What are the Standard Margins? (The Tolerance Values)
You asked about the "narrowest margin possible." In PDF processing (PyMuPDF), units are usually in Points (1/72 of an inch).
Here are the standard values you can use for edge_tolerance:

A. For Removing "Scanner Noise" (Recommended)
If you just want to remove the black/gray edges caused by scanning a book or paper:
  --Value: 10 to 20 points.
  --Why: Scanner shadows rarely extend more than roughly 5mm (15-20 pts) into the page. This is safe; it won't delete page numbers.

B. For "Narrow" Office Documents
Standard Word documents use "Narrow Margins" of 0.5 inches.
  --Value: 36 points (0.5 inch).
  --Risk: This might delete Headers, Footers, and Page Numbers, as they often live inside the 0.5-inch margin area.

C. For "Standard" Office Documents
The default Word layout uses 1.0 inch.
  --Value: 72 points (1 inch).
  --Risk: High. This will almost certainly delete page numbers and legal disclaimers at the bottom of the page.

D. The "Printer Safe" Minimum
Printers generally cannot print to the absolute edge of the paper. They need a "gripper" area.
  --Value: 12 to 18 points (roughly 1/6 to 1/4 inch).
  --Insight: This is usually the safest "aggressive" setting. If an object is within 18 points of the edge and doesn't touch the center, it is almost certainly an artifact, crop mark, or printer info, not content.

Summary: Which value should you choose?
I recommend setting edge_tolerance = 15.

15 points clears out scanner borders and binding shadows.
It is small enough that it will not delete page numbers (which are usually positioned at least 36 points from the edge).
It effectively answers your requirement: removes boundary noise but keeps objects that cross from the boundary into the page.'''



