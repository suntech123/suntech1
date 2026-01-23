import fitz  # PyMuPDF

def analyze_font_sizes(pdf_path):
    doc = fitz.open(pdf_path)
    page = doc[0]  # Analyze first page

    # Get the dictionary structure
    blocks = page.get_text("dict")["blocks"]

    print(f"{'SIZE (pt)':<10} | {'TYPE GUESS':<12} | {'TEXT CONTENT'}")
    print("-" * 60)

    for block in blocks:
        if "lines" in block:  # Ignore image blocks
            for line in block["lines"]:
                for span in line["spans"]:
                    
                    text = span["text"].strip()
                    size = span["size"]
                    
                    # Skip empty spaces or tiny artifacts
                    if not text:
                        continue

                    # --- LOGIC TO CLASSIFY TEXT ---
                    # Common standard: Body text is usually 10-12pt.
                    # Anything larger is often a Header.
                    if size > 14:
                        text_type = "HEADER"
                    elif size < 9:
                        text_type = "Small/Note"
                    else:
                        text_type = "Body Text"

                    # Print with 2 decimal places for size
                    print(f"{size:<10.2f} | {text_type:<12} | {text}")

if __name__ == "__main__":
    # Replace with your PDF
    input_pdf = "your_file.pdf"
    
    try:
        analyze_font_sizes(input_pdf)
    except Exception as e:
        print(f"Error: {e}")
