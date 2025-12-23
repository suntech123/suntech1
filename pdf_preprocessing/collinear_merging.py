'''
Prompt: Now next to implement is collinear merging. Implement it with most optimized technique
'''

'''
This is the most computationally intensive step if done incorrectly. A naive approach compares every line against every other line (O(N2)).
For a page with 1,000 dashed lines (common in Excel exports), this freezes the CPU.

The optimized solution uses a Bucketing + Sorting (O(NlogN)) approach:

  1. Bucket: Group lines by their static axis (e.g., all lines at y=100).
  2. Sort: Sort lines in that bucket by their dynamic axis (e.g., by x start).
  3. Sweep: Iterate once to merge overlapping or close intervals.
'''

#############################################################################################################################

import fitz  # PyMuPDF
from collections import defaultdict
from typing import List, Dict, Any, Tuple

def merge_collinear_lines(drawings: List[Dict[str, Any]], 
                          gap_tolerance: float = 2.0) -> List[Dict[str, Any]]:
    """
    Merges collinear line segments that are touching or close to each other.
    
    Algorithm:
    1. Separates Horizontal and Vertical lines.
    2. Groups them by their static coordinate (Y for horizontal, X for vertical).
    3. Sorts segments within each group.
    4. Merges overlapping or close segments (within gap_tolerance).
    
    Args:
        drawings (List[Dict]): Output from orthogonalize_lines().
        gap_tolerance (float): Max distance between two lines to merge them.
                               Use ~2.0 for dashed lines, ~0.5 for solid lines.

    Returns:
        List[Dict]: A compact list of merged drawings.
    """
    
    # We will rebuild the list. Keep non-lines as they are.
    merged_drawings = []
    
    # Buckets to hold line segments.
    # Key = Static Coordinate (rounded to 1 decimal place to handle float jitter)
    # Value = List of (start, end, original_dict_properties)
    # We store properties to preserve color/width of the first segment.
    h_buckets = defaultdict(list)
    v_buckets = defaultdict(list)

    # 1. CLASSIFY & BUCKET
    for path in drawings:
        items = path.get("items", [])
        
        # Pass through non-lines or complex paths immediately
        if not items or len(items) != 1 or items[0][0] != "l":
            merged_drawings.append(path)
            continue
            
        p1 = items[0][1]
        p2 = items[0][2]
        
        # Determine orientation (Assuming orthogonalized input)
        # We use a tiny epsilon just in case previous step missed a micro-fraction
        is_vertical = abs(p1.x - p2.x) < 0.1
        is_horizontal = abs(p1.y - p2.y) < 0.1
        
        if is_horizontal:
            # Normalise: start is min x, end is max x
            start, end = min(p1.x, p2.x), max(p1.x, p2.x)
            key = round(p1.y, 1) # Group by Y
            h_buckets[key].append((start, end, path))
            
        elif is_vertical:
            # Normalise: start is min y, end is max y
            start, end = min(p1.y, p2.y), max(p1.y, p2.y)
            key = round(p1.x, 1) # Group by X
            v_buckets[key].append((start, end, path))
            
        else:
            # Diagonal lines - keep as is
            merged_drawings.append(path)

    # 2. SORT & MERGE LOGIC (Helper Function)
    def process_buckets(buckets, is_horz):
        results = []
        
        for coord, segments in buckets.items():
            # Sort by start position. This is CRITICAL for O(N) merging.
            # x[0] is the start coordinate.
            segments.sort(key=lambda x: x[0])
            
            # Start the sweep
            if not segments: continue
            
            # Current active segment
            curr_start, curr_end, curr_props = segments[0]
            
            for next_start, next_end, next_props in segments[1:]:
                # Check Overlap or Proximity
                # If the next line starts before (or shortly after) the current ends
                if next_start <= curr_end + gap_tolerance:
                    # MERGE: Extend the current end to the max of both
                    curr_end = max(curr_end, next_end)
                    # Note: We keep 'curr_props' (attributes of the left-most segment)
                else:
                    # NO MERGE: The gap is too big. 
                    # 1. Save the finished segment
                    results.append(create_merged_path(curr_start, curr_end, coord, is_horz, curr_props))
                    # 2. Start a new active segment
                    curr_start, curr_end, curr_props = next_start, next_end, next_props
            
            # Append the final straggler
            results.append(create_merged_path(curr_start, curr_end, coord, is_horz, curr_props))
            
        return results

    # 3. RECONSTRUCTION HELPER
    def create_merged_path(start, end, static_coord, is_horz, template_path):
        """Creates a new PyMuPDF dict from merged coordinates."""
        new_path = template_path.copy()
        
        if is_horz:
            p1 = fitz.Point(start, static_coord)
            p2 = fitz.Point(end, static_coord)
            # Update rect for horizontal line (x0, y-w, x1, y+w)
            # We construct a precise rect
            w = template_path.get("width", 1.0) or 1.0 # default width if 0
            new_path["rect"] = fitz.Rect(start, static_coord - w, end, static_coord + w)
        else:
            p1 = fitz.Point(static_coord, start)
            p2 = fitz.Point(static_coord, end)
            w = template_path.get("width", 1.0) or 1.0
            new_path["rect"] = fitz.Rect(static_coord - w, start, static_coord + w, end)
            
        new_path["items"] = [("l", p1, p2)]
        return new_path

    # Execute Merge
    merged_drawings.extend(process_buckets(h_buckets, is_horz=True))
    merged_drawings.extend(process_buckets(v_buckets, is_horz=False))
    
    return merged_drawings

################################################################################################################################

'''
Why this is Optimized

1. Dictionary Bucketing (O(N)):
  Instead of comparing a line at y=100 with a line at y=500, we immediately group them. We never compare lines that aren't on the same axis.

2. Sorting (O(NlogN)):
  By sorting the segments by their start point, we solve the "overlap" problem in a single linear pass. We don't need to check "Does Line A overlap Line Z?". We only check "Does Line A overlap its immediate neighbor Line B?".

3. Format Preservation:
  The function captures curr_props (the properties of the first line in a chain). This ensures that if you merge a dashed line, the resulting long line keeps the color and width of the original first segment.

Understanding gap_tolerance
  -- 0.1: Only merges lines that actually touch or overlap. Good for strict layouts.
  -- 2.0 (Recommended): Merges dotted/dashed lines into solid lines. This is excellent for Table Detection, as dotted borders are often used in tables.
  -- 5.0+: Aggressive. Will merge two columns of text underlines into one long line. Use with caution.

The Full Pipeline Execution
Here is how you call the entire stack we have built:

      # 1. Clean
      clean = get_clean_page_drawings(page, edge_tolerance=15)
      
      # 2. Skeletonize (Rects -> Lines)
      skeleton = skeletonize_fills_to_strokes(clean)
      
      # 3. Orthogonalize (Deskew)
      ortho = orthogonalize_lines(skeleton)
      
      # 4. Merge (Stitch segments)
      final_layout_lines = merge_collinear_lines(ortho, gap_tolerance=2.0)
      
      print(f"Reduced {len(clean)} raw objects to {len(final_layout_lines)} semantic lines.")

'''
