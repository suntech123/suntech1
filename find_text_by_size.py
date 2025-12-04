import xml.etree.ElementTree as ET

def extract_text_by_font_size(xml_root, target_font_sizes):
    """
    Extracts text content from an XML root for specific font sizes.
    
    Args:
        xml_root (xml.etree.ElementTree.Element): The root element of the parsed XML.
        target_font_sizes (list): A list of font sizes (floats) to extract. 
                                  e.g., [27.0, 16.0]
    
    Returns:
        list[dict]: A list of dictionaries containing the extracted text and metadata.
                    Format: [{'page': 1, 'text': 'Some text', 'size': 27.0}, ...]
    """
    
    # 1. Pre-process target sizes into a set for fast lookup
    # We round input sizes to 1 decimal place to avoid floating point mismatch issues
    target_set = {round(float(s), 1) for s in target_font_sizes}
    
    extracted_data = []

    # 2. Iterate through each page
    for page in xml_root.findall('page'):
        page_num = page.get('number')
        
        # 3. Build a Font Map for the current Page
        # Map: {'0': 16.0, '1': 27.0, ...}
        font_map = {}
        for fspec in page.findall('fontspec'):
            fid = fspec.get('id')
            fsize = fspec.get('size')
            
            if fid and fsize:
                # Store size as float rounded to 1 decimal
                font_map[fid] = round(float(fsize), 1)

        # 4. Iterate through Text elements
        for text_node in page.findall('text'):
            font_ref = text_node.get('font')
            
            # Get the size for this text node
            current_size = font_map.get(font_ref)
            
            # 5. Check if this size matches what the user requested
            if current_size in target_set:
                
                # IMPORTANT: Use itertext() to handle <b>, <i>, etc.
                # Example: <text><b>Certificate</b></text> -> "Certificate"
                full_text_content = "".join(text_node.itertext()).strip()
                
                if full_text_content: # Only add if not empty
                    extracted_data.append({
                        'page': page_num,
                        'size': current_size,
                        'text': full_text_content
                    })

    return extracted_data

# ============================================
# EXAMPLE USAGE
# ============================================

# 1. Setup: Assume 'root' is your parsed XML object from the previous step
# root = tree.getroot()

# 2. Define the sizes you want (e.g., The Headers)
# You can get this list from the clustering function we wrote earlier
wanted_sizes = [27.0, 21.0, 16.0] 

# 3. Run Extraction
results = extract_text_by_font_size(root, wanted_sizes)

# 4. Print Results
print(f"Found {len(results)} text blocks matching sizes {wanted_sizes}\n")

for item in results:
    print(f"[Page {item['page']} | Size {item['size']}] : {item['text']}")