'''
To handle Big, Bold Text effectively, relying solely on line length (Aspect Ratio) or kernel size is insufficient because a massive headline can mimic the dimensions of a table border.

The most robust way to solve this—irrespective of text size—is to add a Pixel Density (Solidity) Check.

The Logic: "Solid Bar" vs. "Text String"
Table Line: A table line is a solid block of ink. If you draw a bounding box around it, >90% of the pixels inside that box are black (or white, in our inverted binary image).
Text: Even big, bold text like "INVOICE" has gaps (spaces between letters, holes inside 'O', 'A', 'D'). If you draw a bounding box around a word, only ~50-70% of the pixels are ink.

We will use this Pixel Density to reject text.

Updated Function
I have modified the filtering logic to calculate the density of every candidate.
'''

import cv2
import numpy as np

def extract_table_structure_robust(image_path_or_array, save_path=None):
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded")

    # 2. Preprocessing
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Adaptive Thresholding (Strict C=10 to reduce text thickness)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 10)

    # 3. Define Kernels (Dynamic Scaling)
    horizontal_scale = int(img.shape[1] / 30)
    vertical_scale = int(img.shape[0] / 30)

    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Morphological Extraction
    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. --- NEW ROBUST FILTERING ---
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)
    
    h_count = 0
    v_count = 0

    # Helper function to check density
    def is_solid_line(contour, original_thresh_img, is_horizontal):
        x, y, w, h = cv2.boundingRect(contour)
        
        # A. Aspect Ratio Check
        if is_horizontal:
            # Horizontal: Width must be much larger than Height
            if h == 0: return False
            aspect = w / h
            # Strict: Line must be 15x longer than it is tall
            if aspect < 15: return False 
            # Thickness limit: Max 1.5% of page height (Prevents giant banners)
            if h > (img.shape[0] * 0.015): return False
        else:
            # Vertical: Height must be much larger than Width
            if w == 0: return False
            aspect = h / w
            if aspect < 15: return False
            if w > (img.shape[1] * 0.015): return False

        # B. PIXEL DENSITY CHECK (The Anti-Text Magic)
        # Crop the bounding box from the ORIGINAL threshold image
        roi = original_thresh_img[y:y+h, x:x+w]
        
        # Count white pixels in this area
        white_pixels = cv2.countNonZero(roi)
        total_pixels = w * h
        
        density = white_pixels / total_pixels
        
        # Logic: Text has gaps (density ~0.5-0.7). Lines are solid (density > 0.9).
        # We use 0.75 as a safe cutoff to allow for some scanning noise.
        if density < 0.75:
            return False
            
        return True

    # --- Filter Horizontal ---
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_solid_line(cnt, thresh, is_horizontal=True):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)
            h_count += 1

    # --- Filter Vertical ---
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        if is_solid_line(cnt, thresh, is_horizontal=False):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)
            v_count += 1

    # 6. Combine
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    # 7. Statistics
    stats = {
        "has_table": (h_count >= 3 and v_count >= 2), # Increased heuristic slightly
        "h_lines": h_count,
        "v_lines": v_count
    }
    
    # Invert for visual output
    final_output = cv2.bitwise_not(grid_structure)

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats

#############################################################################################################

'''
What Changed?

1. The roi = original_thresh_img[y:y+h, x:x+w] step
  Instead of blindly trusting the morphological output (which might have fused letters together), we look back at the raw binary image inside the bounding box.

2. The Density Calculation (white_pixels / total_pixels)

  Scenario: Big Bold Text
  Even if the text is huge, it has spaces between letters and holes inside letters.
  The density will usually be 50% to 70%.
  The check density < 0.75 will reject it.
  
    Scenario: Table Line
  A table line is a solid rectangle.
  The density will be 90% to 100%.
  The check accepts it.

3. Stricter Thickness Limit
  if h > (img.shape[0] * 0.015): return False

  I reduced the allowed thickness from 0.02 (2%) to 0.015 (1.5%).
  On a 1000px high image, a line cannot be thicker than 15 pixels.
  Giant headers are usually thicker than this.

4. Stricter Aspect Ratio
  if aspect < 15: return False
  
  I increased the aspect ratio requirement from 10 to 15.
    --The word BOLD might have a 4:1 ratio.
    --A real table line usually spans a large portion of the page, easily exceeding 15:1.
'''
