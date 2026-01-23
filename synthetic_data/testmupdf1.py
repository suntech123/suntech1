import fitz  # PyMuPDF
import sys

def run_demo(file_path):
    try:
        # 1. Open the existing PDF
        doc = fitz.open(file_path)
        print(f"Successfully opened: {file_path}")
        print(f"Total Pages: {len(doc)}\n")
        
        # Load the first page for demonstration
        page = doc[0] 
    except Exception as e:
        print(f"Error opening file: {e}")
        return

    print("--- 1. Using 'clip' (Extract text only from specific area) ---")
    # Define a rectangle for the top header area (approx top 80 points)
    # rect format: (x0, y0, x1, y1)
    header_area = fitz.Rect(0, 0, page.rect.width, 100) 
    
    text = page.get_text("text", clip=header_area)
    print(f"Clipped Output (Top 100pt): '{text.strip()}'\n")


    print("--- 2. Using 'flags' (Control dehyphenation & whitespace) ---")
    # TEXT_DEHYPHENATE: Joins "hyphen-ated" -> "hyphenated" if found at line ends
    # TEXT_PRESERVE_WHITESPACE: Keeps spaces exactly as is
    my_flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_WHITESPACE
    
    text = page.get_text("text", flags=my_flags)
    # Printing just the first 200 chars to avoid cluttering console
    print(f"Flagged Output (snippet):\n{text[:200]}...\n")


    print("--- 3. Using 'sort' (Force reading order) ---")
    # Without sort, PDF text extraction follows the internal stream order.
    # With sort=True, it orders by Y-coordinate (top-down), then X-coordinate.
    
    unsorted = page.get_text("blocks", sort=False)
    sorted_blocks = page.get_text("blocks", sort=True)
    
    if unsorted and sorted_blocks:
        print(f"Unsorted first block: {unsorted[0][4].strip()[:50]}...")
        print(f"Sorted first block:   {sorted_blocks[0][4].strip()[:50]}...\n")
    else:
        print("No text blocks found on this page.\n")


    print("--- 4. Using 'delimiters' (Custom word splitting) ---")
    # Only works with opt="words"
    # We will use a colon ':' as a delimiter example. 
    # This splits words like "Date:2023" into "Date" and "2023"
    
    words = page.get_text("words", delimiters=":")
    print(f"Total words found using delimiter ':': {len(words)}")
    if words:
        print(f"First 3 words: {[w[4] for w in words[:3]]}")
    print()


    print("--- 5. The 'TextPage' Optimization (For Heavy Processing) ---")
    # If you need to extract text in multiple formats (text, html, json) for the same page,
    # create the TextPage once and reuse it to save processing time.
    
    # Step A: Create the TextPage once
    tp = page.get_textpage(clip=page.rect, flags=fitz.TEXT_INHIBIT_SPACES)
    
    # Step B: Pass 'textpage=tp' to get_text
    out_text = page.get_text("text", textpage=tp)
    out_html = page.get_text("html", textpage=tp)
    out_json = page.get_text("json", textpage=tp)
    
    print("Successfully extracted Text, HTML, and JSON using a single TextPage object.")
    print(f"HTML Snippet: {out_html[:100]}...")

if __name__ == "__main__":
    # --- CHANGE THIS FILE PATH ---
    input_pdf = "your_file.pdf" 
    
    # Simple check to ensure code doesn't crash if file isn't set
    if input_pdf == "your_file.pdf":
        print("Please update the 'input_pdf' variable in the code to your actual file path.")
    else:
        run_demo(input_pdf)
