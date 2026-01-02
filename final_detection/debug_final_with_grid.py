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
                                   cv2.THRESH_BINARY_INV, 15, 10) # Strict threshold

    # 3. Morphological Extraction
    # Note: I increased the divisor to 40 to ensure we catch table lines even if they are short,
    # relying on the VALIDATION step below to filter out the noise/logos.
    horizontal_scale = int(img.shape[1] / 40) 
    vertical_scale = int(img.shape[0] / 40)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 4. Line Filtering (Density & Ratio)
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)
    
    # Helper: Solidity Check
    def is_valid_line(contour, is_h):
        x, y, w, h = cv2.boundingRect(contour)
        
        # Geometry Check
        if is_h:
            if w < (img.shape[1] * 0.05): return False # Ignore tiny dashes (<5% width)
            if h > (img.shape[0] * 0.015): return False # Ignore thick banners
            if w / h < 10: return False
        else:
            if h < (img.shape[0] * 0.02): return False # Ignore tiny vertical dashes
            if w > (img.shape[1] * 0.015): return False
            if h / w < 10: return False

        # Density Check (Solid ink vs Text)
        roi = thresh[y:y+h, x:x+w]
        density = cv2.countNonZero(roi) / (w * h)
        return density > 0.75

    # Filter Horizontal
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=True):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    # Filter Vertical
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_valid_line(cnt, is_h=False):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 5. NEW: STRUCTURE VALIDATION
    # We combine the lines to see the "Grid"
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # Validation A: Find Intersections (Joints)
    # A real table has intersections where H and V meet.
    intersection_mask = cv2.bitwise_and(clean_h, clean_v)
    # We dilate intersections slightly to merge close crossings
    intersection_mask = cv2.dilate(intersection_mask, np.ones((3,3), np.uint8)) 
    joints_contours, _ = cv2.findContours(intersection_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    num_joints = len(joints_contours)

    # Validation B: Grid Bounding Box Area
    # Find the bounding box of EVERYTHING we detected
    total_contours, _ = cv2.findContours(grid_structure, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    has_table = False
    if total_contours:
        # Get the bounding box of all lines combined
        all_points = np.concatenate(total_contours)
        x, y, w, h = cv2.boundingRect(all_points)
        
        # --- THE HEURISTICS ---
        
        # Rule 1: Area Coverage
        # A table usually takes up at least 5% of the page area or has significant width
        page_area = img.shape[0] * img.shape[1]
        grid_area = w * h
        relative_area = grid_area / page_area
        relative_width = w / img.shape[1]

        # Rule 2: Connectivity
        # Logos might have 1 or 2 crossings. Tables usually have 4+ (corners of a cell).
        # Exception: A list with just horizontal lines (we allow this if width is huge)
        
        is_grid_table = (num_joints >= 4) and (relative_area > 0.05)
        is_list_table = (num_joints < 4) and (relative_width > 0.6) # Must be VERY wide if no verticals
        
        if is_grid_table or is_list_table:
            has_table = True
        else:
            # It detected lines, but they are too small/clustered (Likely a Logo)
            has_table = False
            # Clear the output because it's not a table
            grid_structure = np.zeros_like(grid_structure)

    # Invert for visual
    final_output = cv2.bitwise_not(grid_structure)

    stats = {
        "has_table": has_table,
        "num_joints": num_joints,
        "table_area_pct": round((w*h)/(img.shape[0]*img.shape[1]), 3) if total_contours else 0
    }

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats
