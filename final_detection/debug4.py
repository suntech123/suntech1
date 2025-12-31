'''
Based on the result images you provided, the "Robust" logic with Aspect Ratio Filtering worked perfectly.

    Image 1 shows the thresholding successfully separated text from the background.
    Image 2 shows the Morphological operations (scale / 30) successfully removed all the text, leaving only the table structure.
    Image 3 shows the final clean output with lines preserved.

Here is the Final Production Code. I have cleaned up the debug prints, optimized the parameters based on your successful results, and packaged it into a ready-to-use function.
'''

########################################## [ code ] ##########################################################

import cv2
import numpy as np

def extract_table_structure(image_path_or_array, save_path=None):
    """
    Analyzes a document image to extract ONLY the horizontal and vertical grid lines.
    Removes text and noise using morphological operations and aspect-ratio filtering.
    
    Args:
        image_path_or_array: Path to image string OR a numpy array.
        save_path (str, optional): If provided, saves the result to this path.
        
    Returns:
        tuple: (final_image, stats)
            - final_image: numpy array (Black lines on White background)
            - stats: dict {'has_table': bool, 'h_lines': int, 'v_lines': int}
    """
    
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded")

    # 2. Preprocessing
    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Thresholding
    # Constant '5' (subtracted from mean) was validated in your debug_1_thresh.jpg
    # It keeps the background clean while preserving lines.
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 5)

    # 3. Define Kernels (Dynamic Scaling)
    # Validated: img.shape / 30 successfully removed the text in debug_2.
    horizontal_scale = int(img.shape[1] / 30)
    vertical_scale = int(img.shape[0] / 30)

    # Create structural elements
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Morphological Extraction (Get raw candidates)
    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. Smart Filtering (Aspect Ratio & Thickness)
    # We rebuild the masks to ensure we only keep "line-like" objects
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)
    
    h_count = 0
    v_count = 0

    # --- Filter Horizontal Lines ---
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h) if h > 0 else 0
        
        # Logic: Must be long (ratio > 10) AND not essentially a block (height < 2% of page)
        if aspect_ratio > 10 and h < (img.shape[0] * 0.02):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)
            h_count += 1

    # --- Filter Vertical Lines ---
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = h / float(w) if w > 0 else 0
        
        # Logic: Must be tall (ratio > 10) AND not too wide (width < 2% of page)
        if aspect_ratio > 10 and w < (img.shape[1] * 0.02):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)
            v_count += 1

    # 6. Combine and Post-Process
    # Combine the cleaned horizontal and vertical masks
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # Dilate slightly to fix small gaps at intersections (common in tables)
    # Using a 2x2 kernel to be conservative
    kernel_small = np.ones((2, 2), np.uint8)
    grid_structure = cv2.dilate(grid_structure, kernel_small, iterations=1)

    # Invert to get Document Look (Black lines on White background)
    final_output = cv2.bitwise_not(grid_structure)

    # 7. Statistics
    stats = {
        "has_table": (h_count >= 2 and v_count >= 2), # Heuristic: at least 2 of each implies a grid
        "h_lines": h_count,
        "v_lines": v_count
    }

    if save_path:
        cv2.imwrite(save_path, final_output)
        print(f"Table extracted and saved to: {save_path}")

    return final_output, stats

# --- Example Usage ---
if __name__ == "__main__":
    # input_image = "your_page_image.jpg"
    # result_img, statistics = extract_table_structure(input_image, "final_table_structure.jpg")
    
    # print(f"Detection Stats: {statistics}")
    pass

################################################# [ End code ] ###############################################

'''
Key Features of this Final Code:

1. Adaptive Threshold (C=5): Tuned to your debug_1. It creates a clean binary map without making text blocks too "heavy."
2. Scale Factor (1/30): Tuned to your debug_2. It is the perfect size to erase the paragraph text while keeping the table headers and rows.
3. Aspect Ratio Filter: The logic aspect_ratio > 10 ensures that even if a small piece of text remains (like a long dash), it is ignored unless it is significantly line-like.
4. Dilation: A tiny 2x2 dilation is added at the end. This ensures that if a vertical line and horizontal line almost touch but have a 1-pixel gap (common in scans), they get fused back together into a proper grid.

'''
