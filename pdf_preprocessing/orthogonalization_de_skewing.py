'''
Prompt: Now I want to implement fix for skewed lines(de-skewing)/Orthogonalization. Implement an optimized function for the same
'''

'''
This is the final step in the vector preprocessing pipeline. This step corrects lines that are almost horizontal or vertical (e.g., a scanned line that goes from y=100 to y=100.5) and snaps them to a perfect grid.

This is crucial because Table Detection algorithms rely on strict coordinate matching (e.g., does line_a.y == line_b.y?). 
A deviation of 0.1 pixel can cause these checks to fail.
'''

#######################################################################################################################

import fitz  # PyMuPDF
from typing import List, Dict, Any

def orthogonalize_lines(drawings: List[Dict[str, Any]], 
                        skew_tolerance: float = 2.0) -> List[Dict[str, Any]]:
    """
    Snaps slightly skewed lines to be perfectly horizontal or vertical.
    
    It checks the delta between start/end points. If the deviation is within 
    the skew_tolerance, it flattens the line to the average coordinate.

    Args:
        drawings (List[Dict]): Output from page.get_drawings() (or previous steps).
        skew_tolerance (float): Maximum pixel deviation to fix. 
                                Default 2.0 is safe for most scanned docs.
                                Use 0.5-1.0 for digital-born PDFs.

    Returns:
        List[Dict]: The list with lines snapped to the nearest axis.
    """
    
    orthogonalized = []

    for path in drawings:
        new_path = path.copy()
        
        # We only process paths that contain lines ('l'). 
        # We generally skip fills ('f') unless we know they are lines (previous step).
        # However, checking 'items' covers both cases if they use "l" geometry.
        items = new_path.get("items", [])
        
        if not items:
            orthogonalized.append(new_path)
            continue

        has_changes = False
        new_items = []

        for item in items:
            op = item[0]
            
            # We only fix Lines ("l"). 
            # Rects ("re") are by definition orthogonal in PDF (unless rotated via matrix).
            # Curves ("c") cannot be orthogonalized simply.
            if op != "l":
                new_items.append(item)
                continue

            p1 = item[1] # type: fitz.Point
            p2 = item[2] # type: fitz.Point

            # Create new points to avoid mutating shared references unexpectedly
            nx1, ny1 = p1.x, p1.y
            nx2, ny2 = p2.x, p2.y

            # Calculate deltas
            dx = abs(nx1 - nx2)
            dy = abs(ny1 - ny2)

            # --- CHECK 1: IS IT ALMOST HORIZONTAL? ---
            # Condition: deviation in Y is small (skew), but line has length (dx > dy)
            if 0 < dy <= skew_tolerance and dx > dy:
                # Snap Y to the average
                avg_y = (ny1 + ny2) / 2
                ny1 = avg_y
                ny2 = avg_y
                has_changes = True

            # --- CHECK 2: IS IT ALMOST VERTICAL? ---
            # Condition: deviation in X is small (skew), but line has length (dy > dx)
            elif 0 < dx <= skew_tolerance and dy > dx:
                # Snap X to the average
                avg_x = (nx1 + nx2) / 2
                nx1 = avg_x
                nx2 = avg_x
                has_changes = True

            # Append the updated line
            new_items.append(("l", fitz.Point(nx1, ny1), fitz.Point(nx2, ny2)))

        if has_changes:
            # 1. Update items
            new_path["items"] = new_items
            
            # 2. CRITICAL: Recalculate the Bounding Box (Rect)
            # If we straightened the line, the old bounding box is now slightly wrong.
            # We iterate through all points in the new items to find min/max.
            inf = float("inf")
            min_x, min_y = inf, inf
            max_x, max_y = -inf, -inf
            
            for item in new_items:
                # item structure is (op, p1, p2, ...)
                # We check all points in the item tuple
                for pt in item[1:]: 
                    if isinstance(pt, fitz.Point):
                        min_x = min(min_x, pt.x)
                        min_y = min(min_y, pt.y)
                        max_x = max(max_x, pt.x)
                        max_y = max(max_y, pt.y)
            
            # Handle edge case where a path might become empty (rare)
            if min_x != inf:
                new_path["rect"] = fitz.Rect(min_x, min_y, max_x, max_y)

        orthogonalized.append(new_path)

    return orthogonalized

#################################################################################################################

'''
Key Logic & Optimizations

1. The "Average" Approach:
  If a line goes from y = 100 to y=102, simply setting both to 100 might shift the line too much visually.
  Setting both to 101 (the average) ensures the line stays visually centered relative to where it was drawn.

2. Safety Check (dx > dy):
  We verify that the line is actually trending in that direction.
  Without this check, a very short diagonal line (e.g., a slash / in text) might be "flattened" into a dash -, which corrupts the data. We only flatten if the line is mostly long and barely skewed.

3. Rect Recalculation:
  This is the most often missed step.
  path["rect"] is the cached bounding box. If you change the line coordinates inside items but don't update rect, rect.intersects() calls will return false positives/negatives later. The function loops through the new points and tightens the bounding box.

4. Tolerance Tuning:
  2.0: Good for scanned documents or OCR layers where alignment is jittery.
  0.1: Good for "Digital Born" PDFs (Word -> PDF) where slight floating-point errors (100.0001 vs 100.0000) prevent strict equality checks.
'''
