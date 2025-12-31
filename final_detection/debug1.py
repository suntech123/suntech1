def extract_lines_only(image_path_or_array, save_path=None):
    """
    Returns an image containing ONLY the grid lines, with all text removed.
    """
    # 1. Load and Preprocess
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 2. Adaptive Threshold (Lines become White, Background Black)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, -2)

    # 3. Define Kernels (Same logic as before)
    # Adjust '30' to '40' or '50' if you still see large text appearing
    horizontal_scale = int(img.shape[1] / 30)
    vertical_scale = int(img.shape[0] / 30)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Extract Lines (Morphological Opening)
    # This removes any white pixels that don't fit the kernel shape (i.e., Text)
    h_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. Combine Horizontal and Vertical
    # logical OR: If a pixel is in H OR V, keep it.
    grid_structure = cv2.bitwise_or(h_lines, v_lines)
    
    # 6. Optional: Clean up gaps at intersections
    # Sometimes intersections get gaps. A tiny dilation fixes this.
    kernel_small = np.ones((2, 2), np.uint8)
    grid_structure = cv2.dilate(grid_structure, kernel_small, iterations=1)

    # 7. Invert for "Document Look" (Optional)
    # Current 'grid_structure' is White Lines on Black Background.
    # To get Black Lines on White Background (like a paper), invert it:
    final_output = cv2.bitwise_not(grid_structure)

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output
