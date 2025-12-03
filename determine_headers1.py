import xml.etree.ElementTree as ET
from collections import Counter
import io

def extract_headings_with_boldness(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # --- STEP 1: Parse Font Specifications ---
    # We now store a dictionary containing both size and a boolean for boldness
    # Format: { '0': {'size': 16, 'is_bold_font': False}, ... }
    font_info = {}
    
    for fontspec in root.findall('.//fontspec'):
        f_id = fontspec.get('id')
        size = fontspec.get('size')
        family = fontspec.get('family', '').lower() # Get font family name
        
        if f_id and size:
            # Check if "bold" appears in the font family name (e.g., "Arial,Bold")
            is_bold_font = "bold" in family
            font_info[f_id] = {
                'size': int(size),
                'is_bold_font': is_bold_font
            }

    # --- STEP 2: Process Each Page ---
    for page in root.findall('.//page'):
        page_num = page.get('number')
        print(f"\n--- Processing Page {page_num} ---")

        text_blocks = []
        all_sizes = []

        for text_node in page.findall('text'):
            font_id = text_node.get('font')
            info = font_info.get(font_id, {'size': 0, 'is_bold_font': False})
            
            size = info['size']
            
            # --- Check Boldness (Crucial Update) ---
            # 1. Is the font family defined as bold?
            font_is_bold = info['is_bold_font']
            
            # 2. Is there a <b> tag explicitly inside the text node?
            # We look for any child named 'b'
            tag_is_bold = any(child.tag == 'b' for child in text_node)
            
            # Final Bold Status: True if either the font is bold OR it has a <b> tag
            is_bold = font_is_bold or tag_is_bold

            # Extract clean text (handling nested <b>, <i>, etc.)
            raw_text = "".join(text_node.itertext()).strip()
            
            if raw_text:
                text_blocks.append({
                    'size': size,
                    'is_bold': is_bold,
                    'text': raw_text
                })
                all_sizes.append(size)

        if not all_sizes:
            continue

        # --- STEP 3: Determine Headings ---
        # 1. Determine Body Size (Mode)
        size_counts = Counter(all_sizes)
        body_font_size = size_counts.most_common(1)[0][0]

        # 2. Filter Headings
        found_headings = False
        
        for block in text_blocks:
            txt_size = block['size']
            txt_bold = block['is_bold']
            text = block['text']

            # LOGIC:
            # It is a heading if:
            # A) The text is physically larger than body text
            # OR
            # B) The text is the same size (or larger), but it is BOLD
            
            is_heading = False
            
            if txt_size > body_font_size:
                is_heading = True
                reason = f"Larger Size ({txt_size})"
            elif txt_size == body_font_size and txt_bold:
                is_heading = True
                reason = f"Bolded Body Size ({txt_size})"

            if is_heading:
                print(f"[Heading found | {reason}]: {text}")
                found_headings = True
        
        if not found_headings:
            print("No headings detected.")

if __name__ == "__main__":
    xml_file = 'output.xml' # Replace with your file path
    extract_headings_with_boldness(xml_file)