import xml.etree.ElementTree as ET
from collections import Counter
import io

def get_pdf_headings_dict(xml_file_path):
    """
    Parses PDF-to-XML output to identify headings based on:
    1. Font Size > Body Text Size
    2. Font Size == Body Text Size BUT Text is Bold (via font family or <b> tag)
    
    Returns:
        dict: { page_number (int): "Header 1\nHeader 2..." }
    """
    
    # --- XML Parsing ---
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        return {0: f"Error parsing XML: {e}"}

    # --- Step 1: Build Font Info Map ---
    # format: { 'font_id': {'size': int, 'is_bold_font': bool} }
    font_info = {}
    
    for fontspec in root.findall('.//fontspec'):
        f_id = fontspec.get('id')
        size = fontspec.get('size')
        family = fontspec.get('family', '').lower()
        
        if f_id and size:
            # Check if font family implies boldness (e.g., "Arial,Bold")
            is_bold_font = "bold" in family
            font_info[f_id] = {
                'size': int(size),
                'is_bold_font': is_bold_font
            }

    # --- Step 2: Initialize Result Dictionary ---
    headings_by_page = {}

    # --- Step 3: Process Each Page ---
    for page in root.findall('.//page'):
        try:
            page_num = int(page.get('number'))
        except (ValueError, TypeError):
            continue # Skip if page number is invalid

        text_blocks = [] # List of dicts: {'text': str, 'size': int, 'is_bold': bool}
        all_sizes = []   # List of ints to find the mode (body size)

        # Iterate all text nodes in the page
        for text_node in page.findall('text'):
            font_id = text_node.get('font')
            
            # Get font details (default to size 0, non-bold if missing)
            info = font_info.get(font_id, {'size': 0, 'is_bold_font': False})
            size = info['size']
            
            # Check for boldness:
            # 1. Font definition has "Bold"
            # 2. XML text node has a child <b> tag
            font_is_bold = info['is_bold_font']
            tag_is_bold = any(child.tag == 'b' for child in text_node)
            is_bold = font_is_bold or tag_is_bold

            # Extract text (handling nested tags like <b>, <i>)
            raw_text = "".join(text_node.itertext()).strip()
            
            if raw_text:
                text_blocks.append({
                    'text': raw_text,
                    'size': size,
                    'is_bold': is_bold
                })
                all_sizes.append(size)

        # If page has no text, store empty string or skip
        if not all_sizes:
            headings_by_page[page_num] = ""
            continue

        # --- Step 4: Determine Body Size (Mode) ---
        size_counts = Counter(all_sizes)
        # The most common font size is assumed to be body text
        body_font_size = size_counts.most_common(1)[0][0]

        # --- Step 5: Filter Headings ---
        page_headers = []
        
        for block in text_blocks:
            txt_size = block['size']
            txt_bold = block['is_bold']
            text = block['text']

            # Logic: It is a heading if:
            # A) Strictly larger than body text
            # B) Equal to body text, but Bold
            if txt_size > body_font_size:
                page_headers.append(text)
            elif txt_size == body_font_size and txt_bold:
                page_headers.append(text)

        # --- Step 6: Combine and Store ---
        # Joining with a newline "\n" ensures headers are distinct strings 
        # inside the value. Change to " " if you want a continuous sentence.
        combined_header_text = "\n".join(page_headers)
        
        headings_by_page[page_num] = combined_header_text

    return headings_by_page

# --- Execution Example ---
if __name__ == "__main__":
    # Replace with your actual XML file path
    xml_file = 'output.xml' 
    
    final_dict = get_pdf_headings_dict(xml_file)
    
    # Pretty print the dictionary
    print("{")
    for page, headers in final_dict.items():
        # repr() helps show the \n characters as literals for debugging
        print(f"  {page}: {repr(headers)},")
    print("}")