import xml.etree.ElementTree as ET
from collections import Counter
import io

def extract_headings_from_xml(xml_file_path):
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error reading file: {e}")
        return

    # --- STEP 1: Parse Font Specifications ---
    # Create a dictionary to look up font sizes by their ID
    # Format: { '0': 16, '1': 27, ... }
    font_sizes = {}
    
    for fontspec in root.findall('.//fontspec'):
        f_id = fontspec.get('id')
        size = fontspec.get('size')
        if f_id and size:
            font_sizes[f_id] = int(size)

    # --- STEP 2: Process Each Page ---
    for page in root.findall('.//page'):
        page_num = page.get('number')
        print(f"\n--- Processing Page {page_num} ---")

        text_blocks = []
        all_sizes = []

        # Iterate over all text nodes in the page
        for text_node in page.findall('text'):
            font_id = text_node.get('font')
            
            # 1. Get the font size for this block
            # Default to 0 if font_id not found
            size = font_sizes.get(font_id, 0) 
            
            # 2. Extract text content
            # We use "".join(node.itertext()) because the text might be inside 
            # <b> (bold) or <i> (italic) tags as seen in your image.
            raw_text = "".join(text_node.itertext()).strip()
            
            if raw_text:
                # Store tuple: (font_size, text_content)
                text_blocks.append((size, raw_text))
                all_sizes.append(size)

        # If page is empty, skip
        if not all_sizes:
            continue

        # --- STEP 3: Determine "Body" vs "Heading" ---
        # Logic: The most common font size is the Body Text. 
        # Anything larger than that is a Heading.
        
        size_counts = Counter(all_sizes)
        # generic_size is the most frequent font size (Body text)
        body_font_size = size_counts.most_common(1)[0][0]

        found_headings = False
        
        for size, text in text_blocks:
            # You can adjust the logic here. 
            # E.g., strictly greater (>), or at least 2px larger (+2)
            if size > body_font_size:
                print(f"[Heading | Size {size}]: {text}")
                found_headings = True
        
        if not found_headings:
            print("No headings detected on this page (all text is same size).")

# --- Usage ---
# Replace 'output.xml' with your actual file path
if __name__ == "__main__":
    # Note: Ensure your file path is correct
    xml_file = 'output.xml' 
    extract_headings_from_xml(xml_file)