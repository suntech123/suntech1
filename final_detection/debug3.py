def extract_lines_robust(image_path_or_array, output_prefix="debug"):
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded")
        
    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # --- TWEAK 1: STRICTER THRESHOLD ---
    # Changed constant from '-2' to '10'. 
    # This forces the algorithm to ignore faint noise and "thins" the text.
    # It helps prevent text lines from fusing into solid blocks.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 5)
    
    cv2.imwrite(f"{output_prefix}_1_thresh.jpg", thresh) # <--- CHECK THIS IMAGE

    # 3. Define Kernels
    # Relaxed scale: Changed divisor from 20 to 30 to catch shorter lines
    horizontal_scale = int(img.shape[1] / 30) 
    vertical_scale = int(img.shape[0] / 30)

    # 4. Morphological Extraction
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # Detect raw candidates
    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)
    
    # Save the "raw" detection before filtering
    # If this image is blank, the 'horizontal_scale' is too big.
    combined_raw = cv2.bitwise_or(h_candidates, v_candidates)
    cv2.imwrite(f"{output_prefix}_2_raw_candidates.jpg", combined_raw) # <--- CHECK THIS IMAGE

    # 5. SMART FILTERING (Aspect Ratio instead of Thickness)
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)

    # --- Filter Horizontal Lines ---
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        # Calculate Aspect Ratio
        aspect_ratio = w / float(h)
        
        # LOGIC:
        # 1. Keep if it's very long (Ratio > 10)
        # 2. AND it's not super thick (pixel thickness < 1% of page height)
        # This handles high-res and low-res images automatically.
        if aspect_ratio > 10 and h < (img.shape[0] * 0.02):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)

    # --- Filter Vertical Lines ---
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        
        aspect_ratio = h / float(w)
        
        # Same logic for vertical
        if aspect_ratio > 10 and w < (img.shape[1] * 0.02):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)

    # 6. Combine
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # Invert for final view
    final_output = cv2.bitwise_not(grid_structure)

    cv2.imwrite(f"{output_prefix}_3_final.jpg", final_output)
    print(f"Debug images saved with prefix: {output_prefix}")
    return final_output
