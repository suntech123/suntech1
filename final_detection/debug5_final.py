'''
Here is the complete code. I have added the get_pages_with_tables function which acts as the main controller.
It handles the necessary conversion between the PIL Image (returned by the renderer) and the NumPy Array (expected by the OpenCV detector), and handles the iteration through the PDF.
'''

import pypdfium2 as pdfium
from PIL import Image
import cv2
import numpy as np
import os

# --- YOUR PROVIDED FUNCTIONS ---

def render_page_for_detection(pdf_path, page_num):
    # 1. Load the PDF
    pdf = pdfium.PdfDocument(pdf_path)
    page = pdf[page_num]
    
    # 2. Render the page to a high-quality image (e.g., 300 DPI)
    # scale=4 roughly equals 300 DPI (72 * 4 ≈ 288)
    bitmap = page.render(scale=4, rotation=0)
    
    # 3. Convert to PIL Image
    pil_image = bitmap.to_pil()
    
    return pil_image


def extract_table_structure(image_path_or_array, save_path=None):
    """
    Analyzes a document image to extract ONLY the horizontal and vertical grid lines.
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
    thresh = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, 
                                   cv2.THRESH_BINARY_INV, 15, 5)

    # 3. Define Kernels (Dynamic Scaling)
    horizontal_scale = int(img.shape[1] / 30)
    vertical_scale = int(img.shape[0] / 30)

    # Create structural elements
    h_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_scale, 1))
    v_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, vertical_scale))

    # 4. Morphological Extraction (Get raw candidates)
    h_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, h_kernel)
    v_candidates = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, v_kernel)

    # 5. Smart Filtering (Aspect Ratio & Thickness)
    clean_h = np.zeros_like(thresh)
    clean_v = np.zeros_like(thresh)
    
    h_count = 0
    v_count = 0

    # --- Filter Horizontal Lines ---
    contours, _ = cv2.findContours(h_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = w / float(h) if h > 0 else 0
        
        if aspect_ratio > 10 and h < (img.shape[0] * 0.02):
            cv2.drawContours(clean_h, [cnt], -1, 255, -1)
            h_count += 1

    # --- Filter Vertical Lines ---
    contours, _ = cv2.findContours(v_candidates, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for cnt in contours:
        x, y, w, h = cv2.boundingRect(cnt)
        aspect_ratio = h / float(w) if w > 0 else 0
        
        if aspect_ratio > 10 and w < (img.shape[1] * 0.02):
            cv2.drawContours(clean_v, [cnt], -1, 255, -1)
            v_count += 1

    # 6. Combine and Post-Process
    grid_structure = cv2.bitwise_or(clean_h, clean_v)
    
    kernel_small = np.ones((2, 2), np.uint8)
    grid_structure = cv2.dilate(grid_structure, kernel_small, iterations=1)

    # Invert to get Document Look
    final_output = cv2.bitwise_not(grid_structure)

    # 7. Statistics
    stats = {
        "has_table": (h_count >= 2 and v_count >= 2), 
        "h_lines": h_count,
        "v_lines": v_count
    }

    if save_path:
        cv2.imwrite(save_path, final_output)

    return final_output, stats


# --- NEW MAIN CONTROLLER FUNCTION ---

def get_pages_with_tables(pdf_path):
    """
    Scans a PDF document page by page to detect tables using grid analysis.
    
    Args:
        pdf_path (str): Path to the PDF file.
        
    Returns:
        list: List of 0-based page indices containing tables.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # Open PDF once just to get the page count
    temp_doc = pdfium.PdfDocument(pdf_path)
    num_pages = len(temp_doc)
    temp_doc.close() # Close it, as render_page_for_detection opens its own instance

    print(f"Analyzing {num_pages} pages in: {pdf_path} ...")
    
    pages_with_tables = []

    for page_num in range(num_pages):
        try:
            # 1. Render Page (Returns PIL Image)
            pil_image = render_page_for_detection(pdf_path, page_num)
            
            # 2. Convert PIL Image (RGB) to OpenCV Image (BGR/Grayscale Compatible)
            # np.array(pil_image) returns RGB. 
            # We convert to BGR to be standard for OpenCV, though the grayscale 
            # conversion in the next function handles RGB inputs fine too.
            open_cv_image = np.array(pil_image) 
            open_cv_image = open_cv_image[:, :, ::-1].copy() # RGB to BGR

            # 3. Detect Tables
            # We don't save the image to disk (save_path=None) to keep it fast
            _, stats = extract_table_structure(open_cv_image, save_path=None)
            
            # 4. Check results
            if stats['has_table']:
                print(f"  [+] Table detected on Page {page_num + 1} (H-lines: {stats['h_lines']}, V-lines: {stats['v_lines']})")
                pages_with_tables.append(page_num)
            else:
                print(f"  [-] No table on Page {page_num + 1}")

        except Exception as e:
            print(f"  [!] Error processing page {page_num}: {e}")
            continue

    return pages_with_tables


# --- EXECUTION BLOCK ---
if __name__ == "__main__":
    # Replace with your actual PDF file path
    input_pdf = "sample_document.pdf" 
    
    # Run the detection
    try:
        detected_pages = get_pages_with_tables(input_pdf)
        
        print("\n" + "="*40)
        print(f"FINAL RESULT: List of pages having tables: {detected_pages}")
        print("="*40)
        
    except Exception as e:
        print(f"Execution failed: {e}")
