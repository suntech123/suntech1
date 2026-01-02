import cv2
import numpy as np

def extract_table_structure_extended(image_path_or_array, save_path=None):
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None: raise ValueError("Image could not be loaded")

    # 1. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Preservation: Keep relaxed threshold (C=4) for faint gray headers/zebra rows
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 4)

    # Preservation: Keep Sobel to detect edges of colored blocks
    sobel_y = cv2.Sobel(gray, cv2.CV_8U, 0, 1, ksize=3)
    _, edges_h = cv2.threshold(sobel_y, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    sobel_x = cv2.Sobel(gray, cv2.CV_8U, 1, 0, ksize=3)
    _, edges_v = cv2.threshold(sobel_x, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    combined_raw = cv2.bitwise_or(thresh, edges_h)
    combined_raw = cv2.bitwise_or(combined_raw, edges_v)

    # 2. Line Detection
    h_scale = int(img.shape[1] / 40)
    v_scale = int(img.shape[0] / 40)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (h_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, v_scale))

    h_candidates = cv2.morphologyEx(combined_raw, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(combined_raw, cv2.MORPH_OPEN, v_kernel)

    # 3. Line Validation
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)

    def is_valid_line(contour, is_h):
        x, y, w, h = cv2.boundingRect(contour)
        if is_h:
            if w < (img.shape[1] * 0.05): return False 
            if h > (img.shape[0] * 0.05): return False 
            if w / h < 5: return False 
        else:
            if h < (img.shape[0] * 0.02): return False 
            if w > (img.shape[1] * 0.02): return False
            if h / w < 10: return False
        
        roi = combined_raw[y:y+h, x:x+w]
        density = cv2.countNonZero(roi) / (w * h)
        return density > 0.50

    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=True): cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=False): cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 4. CLUSTERING
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    # Using 1% vertical smear to keep separate text boxes from merging,
    # but relying on new logic to handle broken lines within a cluster.
    cluster_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, int(img.shape[0]*0.01)))
    rough_clustering = cv2.morphologyEx(grid_structure, cv2.MORPH_CLOSE, cluster_kernel)
    candidates, _ = cv2.findContours(rough_clustering, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    final_mask = np.zeros_like(grid_structure)
    total_h = 0
    total_v = 0
    tables_found = 0

    for cnt in candidates:
        x, y, w, h = cv2.boundingRect(cnt)
        
        roi_h = clean_h[y:y+h, x:x+w]
        roi_v = clean_v[y:y+h, x:x+w]
        
        local_h_cnts, _ = cv2.findContours(roi_h, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        local_v_cnts, _ = cv2.findContours(roi_v, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        n_h = len(local_h_cnts)
        n_v = len(local_v_cnts)

        # Count Spanning Lines (> 85% width of cluster)
        spanning_h_count = 0
        for h_c in local_h_cnts:
            _, _, lw, _ = cv2.boundingRect(h_c)
            if lw > (w * 0.85): spanning_h_count += 1
        
        # Count Joints
        roi_intersect = cv2.bitwise_and(roi_h, roi_v)
        joints_cnts, _ = cv2.findContours(roi_intersect, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        num_joints = len(joints_cnts)

        # --- LOGIC RULES ---

        # 1. Internal Structure (Base Requirement)
        has_structure = (spanning_h_count >= 3) or (n_v >= 3)
        
        # 2. Connectivity Check (Standard)
        is_connected = True
        if n_v >= 2:
            max_v_len = 0
            for v_c in local_v_cnts:
                _, _, _, v_h = cv2.boundingRect(v_c)
                if v_h > max_v_len: max_v_len = v_h
            if max_v_len < (h * 0.4): is_connected = False
        
        # --- NEW RULES FOR EDGE CASES ---

        # Rule E: Comparison Table (2-Column)
        # Matches Image 3 (Itemized Bill) and Image 2 (Emergency)
        # 1 Vertical line + 3 Spanning H-lines + 3 Joints (Top, Mid, Bot)
        is_comparison_table = (n_v == 1) and (spanning_h_count >= 3) and (num_joints >= 3)

        # Rule F: Row-Density Trust (Zebra Striping)
        # Matches Image 1 (CDHP Options)
        # If we have MANY rows (e.g., > 5), we trust it's a table even if verticals are broken
        # or implied. We bypass the strict 'is_connected' check here.
        is_row_dense = (n_h >= 6) and (n_v >= 1)

        # Rule B: List Table (No Verticals)
        relative_width = w / img.shape[1]
        is_list_table = (n_v < 1) and (spanning_h_count >= 3) and (relative_width > 0.5)

        # Rule C: Standard Grid Table
        is_standard_grid = (num_joints >= 4) and has_structure and is_connected

        # Final Decision
        if is_standard_grid or is_list_table or is_comparison_table or is_row_dense:
            cv2.drawContours(final_mask, local_h_cnts, -1, 255, -1, offset=(x,y))
            cv2.drawContours(final_mask, local_v_cnts, -1, 255, -1, offset=(x,y))
            total_h += n_h
            total_v += n_v
            tables_found += 1

    final_output = cv2.bitwise_not(final_mask)
    stats = {"has_table": tables_found > 0, "h_lines": total_h, "v_lines": total_v}
    
    if save_path: cv2.imwrite(save_path, final_output)
    return final_output, stats
