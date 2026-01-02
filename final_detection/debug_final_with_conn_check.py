import cv2
import numpy as np

def extract_table_structure_final(image_path_or_array, save_path=None):
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None: raise ValueError("Image could not be loaded")

    # 1. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # 2. Line Detection
    h_scale = int(img.shape[1] / 40)
    v_scale = int(img.shape[0] / 40)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_scale))

    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 3. Line Validation
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)

    def is_valid_line(contour, is_h):
        x, y, w, h = cv2.boundingRect(contour)
        if is_h:
            if w < (img.shape[1] * 0.05): return False 
            if h > (img.shape[0] * 0.02): return False 
            if w / h < 10: return False
        else:
            if h < (img.shape[0] * 0.02): return False 
            if w > (img.shape[1] * 0.02): return False
            if h / w < 10: return False
        
        roi = thresh[y:y+h, x:x+w]
        density = cv2.countNonZero(roi) / (w * h)
        return density > 0.75

    # Draw Valid Lines
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=True):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=False):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 4. CLUSTERING
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    # Using a 2% vertical smear to connect rows, but keeping horizontal tighter
    cluster_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, int(img.shape[0]*0.02)))
    rough_clustering = cv2.morphologyEx(grid_structure, cv2.MORPH_CLOSE, cluster_kernel)
    candidates, _ = cv2.findContours(rough_clustering, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    final_mask = np.zeros_like(grid_structure)
    total_h = 0
    total_v = 0
    tables_found = 0

    for cnt in candidates:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Extract lines inside this candidate
        roi_h = clean_h[y:y+h, x:x+w]
        roi_v = clean_v[y:y+h, x:x+w]
        
        local_h_cnts, _ = cv2.findContours(roi_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        local_v_cnts, _ = cv2.findContours(roi_v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        n_h = len(local_h_cnts)
        n_v = len(local_v_cnts)
        
        # Rule A: Empty Box Rejection
        has_internal_structure = (n_h >= 3) or (n_v >= 3)
        
        # Rule B: List Table Logic (No Verticals)
        relative_width = w / img.shape[1]
        is_list_table = (n_v < 2) and (n_h >= 3) and (relative_width > 0.5)
        
        # Rule C: Grid Table Logic (Intersections)
        roi_intersect = cv2.bitwise_and(roi_h, roi_v)
        joints_cnts, _ = cv2.findContours(roi_intersect, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        num_joints = len(joints_cnts)
        
        # --- Rule D: CONNECTIVITY CHECK (The Fix for Stacked Boxes) ---
        # If it's a Grid Table, the columns (vertical lines) should span most of the height.
        # If we have two stacked boxes, the max vertical line height will be small 
        # (approx 50% of the cluster height).
        is_connected = True
        if num_joints >= 4 and n_v >= 2:
            # Find the tallest vertical line in this cluster
            max_v_len = 0
            for v_c in local_v_cnts:
                _, _, _, v_h = cv2.boundingRect(v_c)
                if v_h > max_v_len: max_v_len = v_h
            
            # If the tallest line is shorter than 70% of the cluster height, 
            # the structure is likely broken (stacked boxes).
            if max_v_len < (h * 0.7): 
                is_connected = False
        
        # Note: We don't apply connectivity check to List Tables because they naturally lack verticals.

        is_grid_table = (num_joints >= 4) and has_internal_structure and is_connected

        if is_grid_table or is_list_table:
            # Draw valid lines
            cv2.drawContours(final_mask, local_h_cnts, -1, 255, -1, offset=(x,y))
            cv2.drawContours(final_mask, local_v_cnts, -1, 255, -1, offset=(x,y))
            
            total_h += n_h
            total_v += n_v
            tables_found += 1

    final_output = cv2.bitwise_not(final_mask)
    
    stats = {
        "has_table": tables_found > 0,
        "h_lines": total_h,
        "v_lines": total_v
    }

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats
