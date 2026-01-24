import fitz  # PyMuPDF
from collections import Counter

def analyze_pdf_typography(pdf_path):
    doc = fitz.open(pdf_path)
    
    # Counter to store {font_size: character_count}
    font_counts = Counter()
    
    # 1. DATA GATHERING
    # Iterate through pages to collect statistics
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_DEHYPHENATE)["blocks"]
        
        for block in blocks:
            if block["type"] == 0:  # Text block
                for line in block["lines"]:
                    for span in line["spans"]:
                        text = span["text"].strip()
                        if not text: continue
                        
                        # Round size to nearest integer to group 11.99 and 12.01 together
                        size = round(span["size"])
                        
                        # We count characters, not spans. 
                        # (A heading span is 1 item, a paragraph span is 1 item, 
                        # but the paragraph has more characters, giving it more weight).
                        font_counts[size] += len(text)

    # 2. IDENTIFY BODY TEXT
    # The size with the most characters is almost certainly the body text
    if not font_counts:
        print("No text found.")
        return

    # most_common returns [(size, count), (size, count)...]
    body_size_data = font_counts.most_common(1)[0]
    body_size = body_size_data[0]
    
    print(f"--- TYPOGRAPHY ANALYSIS FOR: {pdf_path} ---")
    print(f"Detected Body Text Size: {body_size} pt (Count: {body_size_data[1]} chars)")
    print("-" * 50)

    # 3. CLASSIFY OTHER SIZES
    # Sort all sizes found in descending order
    sorted_sizes = sorted(font_counts.keys(), reverse=True)
    
    styles_map = {} # To store {size: "Role"}

    header_counter = 1
    
    print(f"{'SIZE (pt)':<10} | {'ROLE GUESS':<15} | {'FREQ (Chars)'}")
    print("-" * 50)

    for size in sorted_sizes:
        count = font_counts[size]
        role = ""
        
        # Logic to assign roles
        if size == body_size:
            role = "BODY (P)"
        elif size > body_size:
            # If it's larger than body, it's a header
            # We assign H1 to the largest, H2 to the next, etc.
            role = f"HEADING H{header_counter}"
            header_counter += 1
        elif size < body_size:
            # If it's smaller, it's likely footnotes or captions
            role = "SMALL / CAPTION"

        # Store for return/usage
        styles_map[size] = role
        
        print(f"{size:<10} | {role:<15} | {count}")
    
    return styles_map, body_size

# --- USAGE ---
# This function analyzes the PDF and returns a map you can use later
pdf_file = "your_document.pdf"

try:
    # 1. Analyze the global styles
    style_map, body_sz = analyze_pdf_typography(pdf_file)
    
    print("\n--- TEST: Reading Page 1 with Detected Styles ---")
    
    # 2. Use the map to tag content on a specific page
    doc = fitz.open(pdf_file)
    page = doc[0]
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block["type"] == 0:
            for line in block["lines"]:
                for span in line["spans"]:
                    text = span["text"].strip()
                    if not text: continue
                    
                    # Look up the role based on size
                    size = round(span["size"])
                    role = style_map.get(size, "Unknown")
                    
                    # Only print Headers to demonstrate it works
                    if "HEADING" in role:
                        print(f"[{role}] {text}")

except Exception as e:
    print(f"Error: {e}")
