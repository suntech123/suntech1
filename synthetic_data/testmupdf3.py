import fitz  # PyMuPDF
import sys
import os

def extract_rich_text(pdf_path):
    try:
        doc = fitz.open(pdf_path)
    except Exception as e:
        print(f"Error opening file '{pdf_path}': {e}")
        return

    # Process the first page (or loop over doc for all pages)
    page = doc[0]

    # 1. Define Extraction Flags
    # TEXT_DEHYPHENATE: Joins words split across lines (e.g. "amaz-\ning" -> "amazing")
    # TEXT_PRESERVE_LIGATURES: Keeps combined characters like "fi" as one glyph
    extract_flags = fitz.TEXT_DEHYPHENATE | fitz.TEXT_PRESERVE_LIGATURES

    # 2. Get the Dictionary
    # We use "dict" to get the hierarchical structure: Block -> Line -> Span
    # sort=True ensures we read in visual order (top-down, left-right)
    data = page.get_text("dict", flags=extract_flags, sort=True)

    print(f"File: {pdf_path}")
    print(f"Page Dimensions: {page.rect}")
    print("=" * 60)

    for block in data["blocks"]:
        
        # Check if this block contains text (type 0) or image (type 1)
        if block["type"] == 0: 
            
            for line in block["lines"]:
                
                for span in line["spans"]:
                    # --- THIS IS WHERE THE RICH INFO LIVES ---
                    text = span["text"]
                    
                    # Skip empty whitespace spans to reduce noise
                    if not text.strip():
                        continue

                    font_size = span["size"]
                    font_name = span["font"]
                    font_flags = span["flags"]
                    text_color = span["color"]  # Integer sRGB
                    
                    # Decoding Flags
                    # Note: fitz constants help decode the bitwise integer
                    is_bold = (font_flags & fitz.TEXT_FONT_BOLD) > 0
                    is_italic = (font_flags & fitz.TEXT_FONT_ITALIC) > 0
                    is_mono = (font_flags & fitz.TEXT_FONT_MONOSPACED) > 0
                    is_superscript = (font_flags & fitz.TEXT_FONT_SUPERSCRIPT) > 0
                    
                    # Decoding Color (Integer -> Hex string)
                    hex_color = f"#{text_color:06x}"

                    # Construct Style String
                    properties = []
                    if is_bold: properties.append("BOLD")
                    if is_italic: properties.append("ITALIC")
                    if is_mono: properties.append("MONO")
                    if is_superscript: properties.append("SUPERSCRIPT")
                    
                    props_str = ", ".join(properties) if properties else "Normal"

                    # Print Output
                    print(f"Text: '{text.strip()}'")
                    print(f" - Size:  {font_size:.2f} pt")
                    print(f" - Font:  {font_name}")
                    print(f" - Style: {props_str}")
                    print(f" - Color: {hex_color}")
                    print(f" - BBox:  {span['bbox']}") # (x0, y0, x1, y1)
                    print("-" * 40)

if __name__ == "__main__":
    # --- UPDATE THIS PATH TO YOUR PDF FILE ---
    input_file_path = "document.pdf" 
    
    if os.path.exists(input_file_path):
        extract_rich_text(input_file_path)
    else:
        print(f"File not found: {input_file_path}")
        print("Please update 'input_file_path' in the script to point to a valid PDF.")
