import pypdfium2 as pdfium
from paddleocr import PaddleOCR
from PIL import ImageEnhance
import numpy as np

def enhance_image_contrast(pil_img, contrast_factor=3.0):
    """
    Converts a PIL image to grayscale and significantly increases its contrast.
    """
    # Convert to grayscale
    gray_img = pil_img.convert("L")
    # Enhance contrast
    enhancer = ImageEnhance.Contrast(gray_img)
    high_contrast_img = enhancer.enhance(contrast_factor)
    return high_contrast_img

def process_pdf(pdf_path, max_pages=30, zoom_level=4):
    """
    Reads a PDF, converts the first `max_pages` to high contrast images at `zoom_level`,
    runs PaddleOCR, and returns a dictionary of page numbers and extracted text.
    """
    # Initialize PaddleOCR (show_log=False suppresses the massive debug output)
    ocr = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
    
    # Load the PDF document
    pdf = pdfium.PdfDocument(pdf_path)
    
    # Determine how many pages to process (handle cases where PDF has less than 30 pages)
    num_pages_to_process = min(len(pdf), max_pages)
    
    output_dict = {}

    print(f"Processing {num_pages_to_process} pages...")

    for i in range(num_pages_to_process):
        # 1. Extract Page
        page = pdf[i]
        
        # 2. Render to image with 4x zoom
        bitmap = page.render(scale=zoom_level)
        pil_image = bitmap.to_pil()
        
        # 3. Apply High Contrast
        high_contrast_img = enhance_image_contrast(pil_image, contrast_factor=3.0)
        
        # PaddleOCR expects a numpy array (RGB/BGR format)
        img_array = np.array(high_contrast_img.convert('RGB'))
        
        # 4. Perform OCR
        # cls=True enables text angle classification
        result = ocr.ocr(img_array, cls=True)
        
        # 5. Extract Text from PaddleOCR output
        page_text = []
        
        # PaddleOCR returns a list containing a list of lines for the image.
        # result[0] holds the detected lines. It can be None if the page is empty/has no text.
        if result and result[0]:
            for line in result[0]:
                # line[1][0] contains the actual recognized text string
                # line[1][1] contains the confidence score, line[0] contains bounding box coordinates
                text = line[1][0]
                page_text.append(text)
        
        # Join lines with a newline character
        full_page_text = "\n".join(page_text)
        
        # Store in dictionary (using 1-based indexing for page numbers)
        page_number = i + 1
        output_dict[page_number] = full_page_text
        print(f"✅ Completed OCR for Page {page_number}")

    return output_dict

if __name__ == "__main__":
    pdf_file = "input.pdf"  # Replace with your actual PDF file path
    
    try:
        extracted_data = process_pdf(pdf_file, max_pages=30, zoom_level=4)
        
        # Print the extracted data
        for page_num, text in extracted_data.items():
            print(f"\n--- Page {page_num} ---")
            print(text)
            
    except Exception as e:
        print(f"An error occurred: {e}")