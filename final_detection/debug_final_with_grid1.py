import cv2
import numpy as np

def extract_table_structure_generalized(image_path_or_array, save_path=None):
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None: raise ValueError("Image could not be loaded")

    # 1. Preprocessing & Adaptive Thresholding
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # 2. Line Detection (Morphology)
    # Using /40 scale to capture smaller table details
    h_scale = int(img.shape[1] / 40)
    v_scale = int(img.shape[0] / 40)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_scale))

    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 3. Line Validation (Density & Aspect Ratio)
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)

    def is_valid_line(contour, is_h):
        x, y, w, h = cv2.boundingRect(contour)
        if is_h:
            if w < (img.shape[1] * 0.05): return False # Ignore tiny dashes
            if h > (img.shape[0] * 0.02): return False # Ignore thick banners
            if w / h < 10: return False
        else:
            if h < (img.shape[0] * 0.02): return False 
            if w > (img.shape[1] * 0.02): return False
            if h / w < 10: return False
        
        roi = thresh[y:y+h, x:x+w]
        density = cv2.countNonZero(roi) / (w * h)
        return density > 0.75

    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=True):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=False):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 4. GENERALIZED CLUSTERING (The Magic Step)
    # We combine H and V lines, but we also DILATE them to connect 
    # nearby lines (like rows in a list table) into a single "object".
    
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # Dilation Kernel: Connects things that are within ~2% of page height/width of each other
    cluster_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, int(img.shape[0]*0.02)))
    rough_clustering = cv2.morphologyEx(grid_structure, cv2.MORPH_CLOSE, cluster_kernel)
    
    # Find "Candidate Blocks" (Potential Tables or Boxes)
    candidates, _ = cv2.findContours(rough_clustering, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    final_mask = np.zeros_like(grid_structure)
    total_h = 0
    total_v = 0
    tables_found = 0

    for cnt in candidates:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # 5. LOCAL VALIDATION LOOP
        # Extract the actual lines INSIDE this specific candidate block
        # We add a small padding (5px) to ensure we don't clip the borders
        roi_h = clean_h[y:y+h, x:x+w]
        roi_v = clean_v[y:y+h, x:x+w]
        
        # Count lines inside this block
        local_h_cnts, _ = cv2.findContours(roi_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        local_v_cnts, _ = cv2.findContours(roi_v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        n_h = len(local_h_cnts)
        n_v = len(local_v_cnts)
        
        # --- LOGIC RULES ---
        
        # Rule A: Empty Box Rejection
        # A simple frame has 2 H-lines and 2 V-lines. 
        # A table MUST have some internal division (header or column sep).
        # So we require at least 3 lines in ONE direction.
        has_internal_structure = (n_h >= 3) or (n_v >= 3)
        
        # Rule B: List Table Logic (No Verticals)
        # If there are NO vertical lines, it's a List Table ONLY if:
        # 1. It has >= 3 horizontal lines (Header + Rows)
        # 2. It is wide relative to the page (> 50%)
        relative_width = w / img.shape[1]
        is_list_table = (n_v < 2) and (n_h >= 3) and (relative_width > 0.5)
        
        # Rule C: Grid Table Logic
        # Must have significant intersections
        roi_intersect = cv2.bitwise_and(roi_h, roi_v)
        joints_cnts, _ = cv2.findContours(roi_intersect, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        num_joints = len(joints_cnts)
        is_grid_table = (num_joints >= 4) and has_internal_structure

        # Final Decision for this Block
        if is_grid_table or is_list_table:
            # It's a valid table! Add it to the final mask.
            # Note: We draw the ORIGINAL lines (roi_h/v), not the smeared cluster blob.
            cv2.drawContours(final_mask, local_h_cnts, -1, 255, -1, offset=(x,y))
            cv2.drawContours(final_mask, local_v_cnts, -1, 255, -1, offset=(x,y))
            
            total_h += n_h
            total_v += n_v
            tables_found += 1
            
    # Invert for display (Black lines on White)
    final_output = cv2.bitwise_not(final_mask)

    stats = {
        "has_table": tables_found > 0,
        "tables_count": tables_found,
        "h_lines": total_h,
        "v_lines": total_v
    }

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats
