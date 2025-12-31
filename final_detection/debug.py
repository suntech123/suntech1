def detect_and_visualize_grid(image_path_or_array):
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded.")

    # Ensure we have a BGR image for colored drawing
    # (If input was grayscale, convert it back to BGR so we can draw red/green lines)
    if len(img.shape) == 2:
        debug_img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    else:
        debug_img = img.copy()

    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, -2)

    # 3. Define Kernels
    horizontal_scale = int(img.shape[1] / 30)
    vertical_scale = int(img.shape[0] / 30)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Morphological Operations
    h_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. Find Contours
    h_contours, _ = cv2.findContours(h_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    v_contours, _ = cv2.findContours(v_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter noise
    valid_h_lines = [cnt for cnt in h_contours if cv2.contourArea(cnt) > 50 or cv2.arcLength(cnt, True) > horizontal_scale]
    valid_v_lines = [cnt for cnt in v_contours if cv2.contourArea(cnt) > 50 or cv2.arcLength(cnt, True) > vertical_scale]

    # --- VISUALIZATION STEP ---
    
    # Draw Horizontal Lines in RED (BGR: 0, 0, 255)
    # Thickness = 2
    cv2.drawContours(debug_img, valid_h_lines, -1, (0, 0, 255), 2)

    # Draw Vertical Lines in GREEN (BGR: 0, 255, 0)
    cv2.drawContours(debug_img, valid_v_lines, -1, (0, 255, 0), 2)

    # 6. Determine Presence
    has_horizontal = len(valid_h_lines) >= 2
    has_vertical = len(valid_v_lines) >= 2

    return {
        "has_horizontal": has_horizontal,
        "has_vertical": has_vertical,
        "counts": (len(valid_h_lines), len(valid_v_lines)),
        "debug_image": debug_img, # <--- We return the visualized image here
        "h_mask": h_mask,         # <--- Optional: See the raw binary mask
        "v_mask": v_mask          # <--- Optional: See the raw binary mask
    }
