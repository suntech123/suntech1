import cv2
import numpy as np

def extract_table_structure_validated(image_path_or_array, save_path=None):
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded")

    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # 3. Morphological Extraction
    # Divisor 40 ensures we catch shorter table lines; validation filters noise later.
    horizontal_scale = int(img.shape[1] / 40) 
    vertical_scale = int(img.shape[0] / 40)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 4. Line Filtering (Density & Ratio)
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)
    
    # Initialize Counters
    h_count = 0
    v_count = 0
    
    def is_valid_line(contour, is_h):
        x, y, w, h = cv2.boundingRect(contour)
        
        # Geometry Check
        if is_h:
            if w < (img.shape[1] * 0.05): return False 
            if h > (img.shape[0] * 0.015): return False 
            if w / h < 10: return False
        else:
            if h < (img.shape[0] * 0.02): return False 
            if w > (img.shape[1] * 0.015): return False
            if h / w < 10: return False

        # Density Check
        roi = thresh[y:y+h, x:x+w]
        density = cv2.countNonZero(roi) / (w * h)
        return density > 0.75

    # Filter Horizontal
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=True):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)
            h_count += 1  # Increment Horizontal Counter

    # Filter Vertical
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=False):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)
            v_count += 1  # Increment Vertical Counter

    # 5. Structure Validation
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    intersection_mask = cv2.bitwise_and(clean_h, clean_v)
    intersection_mask = cv2.dilate(intersection_mask, np.ones((3,3), np.uint8)) 
    joints_contours, _ = cv2.findContours(intersection_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    num_joints = len(joints_contours)

    # Calculate bounding box of the entire detected grid
    total_contours, _ = cv2.findContours(grid_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    has_table = False
    table_area_pct = 0.0
    
    if total_contours:
        all_points = np.concatenate(total_contours)
        x, y, w, h = cv2.boundingRect(all_points)
        
        page_area = img.shape[0] * img.shape[1]
        grid_area = w * h
        table_area_pct = round(grid_area / page_area, 3)
        relative_width = w / img.shape[1]

        # Heuristics
        is_grid_table = (num_joints >= 4) and (table_area_pct > 0.05)
        is_list_table = (num_joints < 4) and (relative_width > 0.6)
        
        if is_grid_table or is_list_table:
            has_table = True
        else:
            has_table = False
            # If rejected, we effectively clear the image and zero out counts
            # (Optional: you can keep the counts if you want to know what was rejected)
            grid_structure = np.zeros_like(grid_structure)
            # h_count = 0  <-- Uncomment if you want to report 0 lines when table is rejected
            # v_count = 0

    final_output = cv2.bitwise_not(grid_structure)

    # 6. Return Stats including Line Counts
    stats = {
        "has_table": has_table,
        "h_lines": h_count,
        "v_lines": v_count,
        "num_joints": num_joints,
        "table_area_pct": table_area_pct
    }

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats
