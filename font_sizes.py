import xml.etree.ElementTree as ET

def extract_font_sizes_from_xml(xml_file_path):
    """
    Parses pdftoxml output and returns a list of all font sizes 
    associated with every text element found.
    """
    try:
        tree = ET.parse(xml_file_path)
        root = tree.getroot()
    except Exception as e:
        return f"Error parsing XML: {e}"

    all_font_sizes = []

    # Iterate through each page individually
    # (Font IDs are often local to the specific page in poppler/pdftoxml output)
    for page in root.findall('page'):
        
        # 1. Build a map of font_id -> font_size for the current page
        # Example from image: <fontspec id="1" size="27" ... />
        font_map = {}
        for fspec in page.findall('fontspec'):
            f_id = fspec.get('id')
            f_size = fspec.get('size')
            if f_id is not None and f_size is not None:
                font_map[f_id] = float(f_size) # Use float to handle sizes like 11.5

        # 2. Iterate through all text elements on this page
        # Example from image: <text ... font="1"><b>Certificate...</b></text>
        for text_node in page.findall('text'):
            font_ref = text_node.get('font')
            
            # Look up the size using the font reference ID
            if font_ref in font_map:
                size = font_map[font_ref]
                all_font_sizes.append(size)
            else:
                # Handle cases where font ID might be missing (rare)
                pass

    return all_font_sizes

# ==========================================
# Example Usage
# ==========================================
# Assuming you saved the XML content to 'output.xml'
# sizes_list = extract_font_sizes_from_xml('output.xml')

# Printing the first 20 extracted sizes to verify
# print(f"Extracted {len(sizes_list)} font sizes.")
# print(f"First 20 sizes: {sizes_list[:20]}")