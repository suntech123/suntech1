import pypdfium2 as pdfium
import google.generativeai as genai
from PIL import ImageOps
import os
import json

def preprocess_and_trim(pil_img):
    """
    Minimizes image size by converting to grayscale and trimming all white margins.
    """
    # 1. Convert to grayscale to drop unnecessary color channels (minimizes size)
    gray_img = pil_img.convert("L")
    
    # 2. Invert image (white background becomes black, dark text becomes white)
    # This allows us to find the bounding box of the actual content.
    inverted_img = ImageOps.invert(gray_img)
    
    # 3. Get the bounding box of the non-black (non-background) regions
    bbox = inverted_img.getbbox()
    
    # 4. Crop the image to the bounding box if content exists
    if bbox:
        trimmed_img = gray_img.crop(bbox)
        return trimmed_img
    
    # Return original grayscale if page is entirely blank
    return gray_img

def extract_toc_with_gemini(pdf_path, max_pages=30, zoom_level=2):
    """
    Reads a PDF, extracts & preprocesses up to `max_pages`, and uses Gemini 
    to extract the Table of Contents into a dictionary.
    """
    # Configure Gemini API
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not found. Please set it.")
    
    genai.configure(api_key=api_key)
    # Using gemini-1.5-flash as it is extremely fast and great for multimodal tasks
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    pdf = pdfium.PdfDocument(pdf_path)
    num_pages_to_process = min(len(pdf), max_pages)
    
    print(f"Extracting and preprocessing {num_pages_to_process} pages at {zoom_level}x zoom...")
    
    # This list will hold alternating strings (Page numbers) and PIL Images
    gemini_payload = []
    
    for i in range(num_pages_to_process):
        page_number = i + 1
        page = pdf[i]
        
        # 1. Render to image with 2x zoom
        bitmap = page.render(scale=zoom_level)
        pil_image = bitmap.to_pil()
        
        # 2. Preprocess: Grayscale and Trim White Space
        processed_img = preprocess_and_trim(pil_image)
        
        # 3. Add to our Gemini payload
        gemini_payload.append(f"Page {page_number}")
        gemini_payload.append(processed_img)
        
    print("Sending preprocessed images to Gemini to extract the Table of Contents...")
    
    # Construct the instruction prompt
    prompt = """
    I have provided images of the first few pages of a document, labeled with their physical page numbers.
    Your task is to:
    1. Identify which of these pages contain the Table of Contents (ToC).
    2. Extract the text of the Table of Contents.
    3. Output the result strictly as a JSON dictionary.
    
    The JSON dictionary should use the document's physical page number (as an integer string) as the key, 
    and the extracted Table of Contents text found on that specific page as the value. 
    If a page does not contain a Table of Contents, do not include it in the dictionary.
    
    Example output format:
    {
      "3": "1. Introduction... 1\n 2. Methodology... 5",
      "4": "3. Results... 10\n 4. Conclusion... 15"
    }
    """
    gemini_payload.append(prompt)
    
    # Call Gemini API
    # Enforcing application/json ensures Gemini returns a clean, parseable JSON string
    response = model.generate_content(
        gemini_payload,
        generation_config={"response_mime_type": "application/json"}
    )
    
    try:
        # Parse the JSON response returned by Gemini into a Python Dictionary
        toc_dictionary = json.loads(response.text)
        return toc_dictionary
    except json.JSONDecodeError:
        print("Failed to decode JSON. Raw output from Gemini:")
        print(response.text)
        return {}

if __name__ == "__main__":
    pdf_file = "input.pdf"  # Replace with your actual PDF file path
    
    try:
        toc_data = extract_toc_with_gemini(pdf_file, max_pages=30, zoom_level=2)
        
        if not toc_data:
            print("No Table of Contents found in the provided pages.")
        else:
            print("\n✅ Successfully Extracted Table of Contents:")
            for page_num, toc_text in toc_data.items():
                print(f"\n--- ToC Content on Page {page_num} ---")
                print(toc_text)
                
    except Exception as e:
        print(f"\nAn error occurred: {e}")