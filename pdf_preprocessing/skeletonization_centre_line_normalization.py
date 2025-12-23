'''
Prompt: Now i have to implement skeletonization/Centre Line Normalization
'''

'''
This is the logical inverse of the previous function. This technique is extremely useful for Table Structure Recognition or Layout Analysis, where you want to detect separators (lines) but the PDF generator has drawn them as thin filled rectangles.
Here is the optimized function for Vector Skeletonization (converting bar-like rectangles into single-stroke lines).
'''

###########################################################################################################################

def skeletonize_fills_to_strokes(drawings: List[Dict[str, Any]], 
                                 ratio_threshold: float = 3.0) -> List[Dict[str, Any]]:
    """
    Performs Center Line Normalization (Skeletonization) on vector drawings.
    
    It detects filled rectangles that are significantly longer than they are wide 
    (based on ratio_threshold) and converts them into a single center-line stroke.
    
    Args:
        drawings (List[Dict]): Output from page.get_drawings().
        ratio_threshold (float): How many times longer a side must be compared 
                                 to the other to count as a "line". 
                                 Default 3.0 means length must be > 3 * width.

    Returns:
        List[Dict]: The list with long, thin fills converted to strokes.
    """
    
    skeletonized = []

    for path in drawings:
        # Shallow copy to preserve original list structure
        new_path = path.copy()
        
        # --- FILTERING ---
        
        # 1. We only care about filled shapes ('f') or filled-only paths
        # If it already has a stroke ('s'), we usually leave it alone or handle complexly.
        if new_path["type"] != "f":
            skeletonized.append(new_path)
            continue
            
        items = new_path.get("items", [])
        
        # 2. We only process single Rectangles ("re").
        # Complex paths ("c") or multi-item paths are not simple bars.
        if len(items) != 1 or items[0][0] != "re":
            skeletonized.append(new_path)
            continue

        # Extract the rectangle
        rect = items[0][1] # type: fitz.Rect
        
        # Dimensions
        w = rect.width
        h = rect.height
        
        # Avoid division by zero
        if w == 0 or h == 0:
            skeletonized.append(new_path)
            continue

        # --- LOGIC: ORIENTATION DETECTION ---
        
        is_horizontal_bar = (w / h) > ratio_threshold
        is_vertical_bar = (h / w) > ratio_threshold

        # If it's a square or a fat box, it's not a line. Keep as fill.
        if not (is_horizontal_bar or is_vertical_bar):
            skeletonized.append(new_path)
            continue

        # --- TRANSFORMATION ---
        
        # Prepare coordinates for the new center line
        p1 = fitz.Point()
        p2 = fitz.Point()
        stroke_width = 0.0

        if is_horizontal_bar:
            # Center Y = Average of top and bottom
            # Line goes from Left to Right
            center_y = (rect.y0 + rect.y1) / 2
            p1.x, p1.y = rect.x0, center_y
            p2.x, p2.y = rect.x1, center_y
            stroke_width = h  # The height becomes the line thickness

        elif is_vertical_bar:
            # Center X = Average of left and right
            # Line goes from Top to Bottom
            center_x = (rect.x0 + rect.x1) / 2
            p1.x, p1.y = center_x, rect.y0
            p2.x, p2.y = center_x, rect.y1
            stroke_width = w  # The width becomes the line thickness

        # --- MUTATE THE OBJECT ---
        
        # 1. Change Type: Fill ('f') -> Stroke ('s')
        new_path["type"] = "s"
        
        # 2. Update Geometry: Rect -> Line
        new_path["items"] = [("l", p1, p2)]
        
        # 3. Swap Colors: The old Fill Color becomes the new Stroke Color
        fill_color = new_path.get("fill")
        new_path["color"] = fill_color  # Set stroke color
        new_path["fill"] = None         # Remove fill color
        
        # 4. Set the new stroke width
        new_path["width"] = stroke_width
        
        # 5. Update Line Caps (Optional but recommended)
        # 'butt' (0) cap is best for recreating exact rectangle geometry.
        # 'round' (1) or 'square' (2) might extend the line length visually.
        new_path["lineCap"] = 0 

        skeletonized.append(new_path)

    return skeletonized


#########################################################################################

'''
Key Logic Explanations

1. Aspect Ratio (ratio_threshold):
  This is the brain of the function.
  If width is 100 and height is 5, Ratio = 20. This is clearly a horizontal line.
  If width is 20 and height is 20, Ratio = 1. This is a square/box. We skip it.
  Recommended Value: 3.0 or 5.0. (A line is usually at least 3x longer than it is thick).


2. Center Calculation:
  For a horizontal bar, the "skeleton" sits exactly at y = (top + bottom) / 2
  For a vertical bar, the "skeleton" sits exactly at x=(left+right)/2

3. Property Swapping:
  Fill -> Color: A filled black rectangle (fill=(0,0,0)) must become a black stroked line (color=(0,0,0)).
  Height -> Width: For a horizontal bar, the visual "height" of the rectangle becomes the width (thickness) of the pen stroke.

4. Edge Case - lineCap:
  I set new_path["lineCap"] = 0 (Butt Cap).
  Why? In PDF, a stroke with a "Square Cap" extends beyond the endpoints. A "Butt Cap" stops exactly at the endpoints. Since we are converting a rectangle x0 -> x1, we want the line to stop exactly at x0 and x1, not stick out.


Workflow Integration
If you are processing a PDF to extract tables or underlines, you should usually run the previous Noise Reduction function first, and then this Skeletonization:

    # 1. Get raw data
    drawings = page.get_drawings()
    
    # 2. Clean Noise (from your previous prompt)
    clean_drawings = get_clean_page_drawings(page, drawings)
    
    # 3. Normalize Lines (The function above)
    skeleton_drawings = skeletonize_fills_to_strokes(clean_drawings)
    
    # Now 'skeleton_drawings' contains only true lines and squares, 
    # making it much easier to detect table grids.

###################################################################################

