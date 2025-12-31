def extract_clean_grid(image_path_or_array, save_path=None):
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded")
        
    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Threshold
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, -2)

    # 3. Dynamic Scales
    # We increase the divisor slightly to make sure we catch longer lines
    horizontal_scale = int(img.shape[1] / 20) 
    vertical_scale = int(img.shape[0] / 20)

    # 4. Morphological Extraction
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # Detect raw candidates
    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. FILTERING STEP (The Fix)
    # We create empty black masks to draw only the "good" lines
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)

    # --- Filter Horizontal Lines ---
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # CRITICAL CHECK: 
        # 1. It must be wide enough (width > horizontal_scale)
        # 2. It must be THIN enough (height < 15 pixels). Text blocks are usually >15px.
        if w > horizontal_scale and h < 15:
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    # --- Filter Vertical Lines ---
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        # CRITICAL CHECK:
        # 1. It must be tall enough
        # 2. It must be THIN enough (width < 15 pixels).
        if h > vertical_scale and w < 15:
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 6. Combine
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # Optional: Dilate to fix gaps at intersections
    grid_structure = cv2.dilate(grid_structure, np.ones((2, 2), np.uint8), iterations=1)

    # Invert to get Black Lines on White Background
    final_output = cv2.bitwise_not(grid_structure)

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output
