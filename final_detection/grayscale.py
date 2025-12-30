'''This approach uses Morphological Transformations, which is the industry-standard technique for document layout analysis (specifically for separating non-text structural elements like lines from text).
Here is the complete solution using opencv-python.
The Logic Pipeline
Grayscale & Invert: Convert image to grayscale.
Adaptive Thresholding: Binarize the image to handle varying lighting/contrast. We invert it so lines become white pixels on a black background.
Morphological Opening:
To find Horizontal Lines: We create a structural element that is a long, thin rectangle (e.g., 50x1 pixels). We "erode" the image with this. Text characters (which are short) disappear, but long lines remain.
To find Vertical Lines: We do the same with a tall, thin rectangle (e.g., 1x50 pixels).
Contour Detection: We count the remaining shapes.'''

import cv2
import numpy as np

def detect_grid_lines(image_path_or_array):
    """
    Analyzes an image to detect significant horizontal and vertical grid lines.
    
    Args:
        image_path_or_array: Path to image string OR a numpy array (from pypdfium2).
        
    Returns:
        dict: {'has_horizontal': bool, 'has_vertical': bool, 'horizontal_count': int, 'vertical_count': int}
    """
    
    # 1. Load Image
    if isinstance(image_path_or_array, str):
        img = cv2.imread(image_path_or_array)
    else:
        # Assuming input is from pypdfium2/PIL converted to numpy
        img = image_path_or_array

    if img is None:
        raise ValueError("Image could not be loaded.")

    # 2. Preprocessing (Standard Noise Removal & Binarization)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Apply Adaptive Thresholding (Industry standard for documents)
    # This keeps lines distinct even if there are shadows or fading.
    # We create a negative (lines are white, background black)
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, -2)

    # 3. Define Structural Elements (Kernels)
    # The size of the kernel determines the sensitivity.
    # Lines shorter than 'scale' will be treated as noise (text).
    horizontal_scale = int(img.shape[1] / 30) # ~3.3% of image width
    vertical_scale = int(img.shape[0] / 30)   # ~3.3% of image height

    # Kernel for Horizontal Lines (Wide and Short)
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    
    # Kernel for Vertical Lines (Tall and Narrow)
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Morphological Operations to Extract Lines
    # "Open" operation = Erosion followed by Dilation.
    # This removes bright regions (text) that don't match the kernel shape.
    
    # Detect Horizontal
    h_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    
    # Detect Vertical
    v_mask = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. Validation (Count Contours)
    # We find contours on the specific masks.
    h_contours, _ = cv2.findContours(h_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    v_contours, _ = cv2.findContours(v_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Filter out extremely small remaining noise (optional but recommended)
    valid_h_lines = [cnt for cnt in h_contours if cv2.contourArea(cnt) > 50 or cv2.arcLength(cnt, True) > horizontal_scale]
    valid_v_lines = [cnt for cnt in v_contours if cv2.contourArea(cnt) > 50 or cv2.arcLength(cnt, True) > vertical_scale]

    # 6. Determine Presence
    has_horizontal = len(valid_h_lines) >= 2 # At least 2 lines to imply a "section" or "table"
    has_vertical = len(valid_v_lines) >= 2

    return {
        "has_horizontal": has_horizontal,
        "has_vertical": has_vertical,
        "horizontal_count": len(valid_h_lines),
        "vertical_count": len(valid_v_lines)
    }

# --- How to use with pypdfium2 ---
if __name__ == "__main__":
    # Example simulation of loading an image
    # In real usage: img = np.array(page.render().to_pil())
    
    # Using a dummy path for demonstration
    try:
        result = detect_grid_lines("page_image.jpg")
        
        print("Analysis Result:")
        print(f"Horizontal Lines Detected: {result['has_horizontal']} (Count: {result['horizontal_count']})")
        print(f"Vertical Lines Detected:   {result['has_vertical']} (Count: {result['vertical_count']})")
        
        if result['has_horizontal'] and result['has_vertical']:
            print("Conclusion: Page likely contains a GRID structure (Table).")
        elif result['has_horizontal']:
             print("Conclusion: Page contains lined separators (List or Rows).")
        else:
            print("Conclusion: Page is likely plain text.")
            
    except Exception as e:
        print(e)


###############################################################################

'''
Explanation of Techniques Used
Adaptive Thresholding (ADAPTIVE_THRESH_MEAN_C):
Unlike a simple fixed threshold (e.g., >127 is white), adaptive calculates the threshold for small regions of the image. This is critical for scanned documents where the paper might be slightly darker in corners.
THRESH_BINARY_INV: We invert the result because OpenCV morphological operations work on white foreground pixels.
getStructuringElement:
This creates a matrix of 1s and 0s.
For horizontal lines, we create a matrix like [1, 1, 1, 1, ...] (50 pixels wide, 1 pixel tall).
For vertical lines, we create a matrix like [[1], [1], [1], ...] (1 pixel wide, 50 pixels tall).
morphologyEx (MORPH_OPEN):
This is the "magic" step. It slides the kernel over the image.
If the image has a text character like "A", it is roughly 10x10 pixels.
When the 50x1 horizontal kernel passes over "A", the "A" does not fit inside the kernel shape (it's too short width-wise). The erosion step deletes the "A".
When the kernel passes over a table line (which is 200x2 pixels), the kernel fits inside. The line is preserved.
horizontal_scale:
I set this dynamically based on image width (img.shape[1] / 30). This ensures the code works on high-res (300 DPI) and low-res (72 DPI) images alike. You can adjust the / 30 factor (lower it to / 20 to require longer lines, raise it to / 50 to detect shorter lines).
'''
