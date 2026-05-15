'''
​Method 1: Using Text Flags (Recommended)
​Most modern PDFs store formatting information in the flags integer of a text span. The bit for strikethrough is 8 (2^3).
'''

import fitz

def find_strikethrough(pdf_path):
    doc = fitz.open(pdf_path)
    for page in doc:
        # Get text in dictionary format
        dict_text = page.get_text("dict")
        for block in dict_text["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        # Check if the 4th bit (value 8) is set
                        if span["flags"] & 8:
                            print(f"Strikethrough detected: '{span['text']}'")
    doc.close()

find_strikethrough("example.pdf")