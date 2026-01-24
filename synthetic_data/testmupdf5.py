import fitz  # PyMuPDF
import csv
import sys
from collections import Counter

def get_span_key(span):
    """
    Returns a tuple representing the style: (rounded_font_size, is_bold)
    """
    size = round(span["size"])
    # Check flag 16 (Bold) or font name containing 'Bold'
    is_bold = (span["flags"] & 16) > 0 or "Bold" in span["font"]
    return (size, is_bold)

def analyze_structure(doc):
    """
    Pass 1: Determine what is Body text and what are Headers.
    Returns:
        - body_style: (size, bold) tuple for body text
        - header_map: dict mapping {(size, bold) -> level_index (0=H1, 1=H2...)}
        - max_depth: Total number of header columns needed
    """
    style_counts = Counter()

    # 1. Count characters for every style
    for page in doc:
        blocks = page.get_text("dict")["blocks"]
        for block in blocks:
            if block["type"] == 0:  # Text
                for line in block["lines"]:
                    for span in line["spans"]:
                        if not span["text"].strip(): continue
                        key = get_span_key(span)
                        style_counts[key] += len(span["text"])

    if not style_counts:
        raise ValueError("Document contains no text.")

    # 2. Identify Body Text (The most frequent style)
    # most_common(1) returns [((size, bold), count)]
    body_style = style_counts.most_common(1)[0][0]
    body_size = body_style[0]

    # 3. Identify Header Levels
    # Rules:
    # - Size > Body Size
    # - Size == Body Size BUT Bold is True
    header_styles = []
    
    for style in style_counts.keys():
        size, is_bold = style
        
        # Rule 1: Larger than body
        if size > body_size:
            header_styles.append(style)
        
        # Rule 2: Same size as body, but Bold (and Body is not bold)
        elif size == body_size and is_bold and not body_style[1]:
            header_styles.append(style)

    # Sort headers: Largest size first. If sizes equal, Bold comes before non-bold (rare).
    # We sort descending on size.
    header_styles.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Create a map: {Style_Tuple : Index}
    # Example: (24, True) -> 0 (H1), (18, True) -> 1 (H2)...
    header_map = {style: i for i, style in enumerate(header_styles)}
    
    return body_style, header_map, len(header_styles)

def pdf_to_hierarchical_csv(pdf_path, output_csv):
    """
    Pass 2: Extract text maintaining hierarchy state.
    """
    doc = fitz.open(pdf_path)
    filename = pdf_path.split("/")[-1]

    # --- Phase 1: Analyze ---
    print("Analyzing Document Structure...")
    body_style, header_map, max_depth = analyze_structure(doc)
    
    print(f"Body Style: Size {body_style[0]}, Bold: {body_style[1]}")
    print(f"Detected {max_depth} Header Levels.")

    # --- Phase 2: Extract ---
    # State variable to hold current headers: ["", "", ""] for H1, H2, H3
    current_headers = [""] * max_depth
    
    # Prepare CSV
    with open(output_csv, mode='w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, delimiter='|')
        
        # Write CSV Header
        # e.g. Filename | H1 | H2 | H3 | Text
        header_row = ["Filename"] + [f"Header_{i+1}" for i in range(max_depth)] + ["Text"]
        writer.writerow(header_row)

        for page in doc:
            blocks = page.get_text("dict", sort=True)["blocks"]
            
            for block in blocks:
                if block["type"] == 0: # Text Block
                    
                    # We process spans individually to detect style changes
                    # But we want to group "Body Text" into paragraphs for the CSV
                    
                    # Flatten block into a list of spans to process sequentially
                    all_spans = [span for line in block["lines"] for span in line["spans"]]
                    
                    block_text_buffer = []

                    for span in all_spans:
                        text = span["text"].strip()
                        if not text: continue
                        
                        style = get_span_key(span)
                        
                        # CHECK 1: Is this a Header?
                        if style in header_map:
                            # If we have buffered body text, write it out before changing header context
                            if block_text_buffer:
                                full_text = " ".join(block_text_buffer)
                                row = [filename] + current_headers + [full_text]
                                writer.writerow(row)
                                block_text_buffer = [] # Clear buffer

                            # Update Hierarchy
                            level = header_map[style]
                            current_headers[level] = text # Set new header
                            
                            # Reset all deeper levels (e.g. If H1 changes, H2 and H3 become empty)
                            for i in range(level + 1, max_depth):
                                current_headers[i] = ""
                                
                        # CHECK 2: Is it Body Text? (Or unknown style treated as body)
                        else:
                            # Append to buffer
                            block_text_buffer.append(text)
                    
                    # End of Block: Write any remaining body text
                    if block_text_buffer:
                        full_text = " ".join(block_text_buffer)
                        row = [filename] + current_headers + [full_text]
                        writer.writerow(row)

    print(f"Extraction Complete. Data saved to: {output_csv}")

# --- EXECUTION ---
if __name__ == "__main__":
    input_pdf = "your_document.pdf"  # <--- REPLACE WITH YOUR FILE
    output_file = "output_hierarchy.csv"
    
    try:
        pdf_to_hierarchical_csv(input_pdf, output_file)
    except Exception as e:
        print(f"Error: {e}")
