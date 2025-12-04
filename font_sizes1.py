def extract_font_sizes_per_page(root):
    """
    Parses pdftoxml output and returns a dictionary mapping page numbers 
    to a list of font sizes found on that page.
    
    Structure: { int_page_num : [float_size, float_size, ...] }
    """
    pages_font_dict = {}

    # Iterate through each page individually
    for page in root.findall('page'):
        
        # Extract page number (convert to integer)
        # XML format is usually <page number="1" ...>
        pg_num_str = page.get('number')
        if not pg_num_str:
            continue # Skip if no page number found
        
        pg_num = int(pg_num_str)

        # 1. Build a map of font_id -> font_size for the current page
        font_map = {}
        for fspec in page.findall('fontspec'):
            f_id = fspec.get('id')
            f_size = fspec.get('size')
            if f_id is not None and f_size is not None:
                font_map[f_id] = float(f_size) 

        # Initialize list specifically for this page
        current_page_sizes = []

        # 2. Iterate through all text elements on this page
        for text_node in page.findall('text'):
            font_ref = text_node.get('font')

            # Look up the size using the font reference ID
            if font_ref in font_map:
                size = font_map[font_ref]
                current_page_sizes.append(size)
        
        # Assign the collected sizes to the dictionary key
        pages_font_dict[pg_num] = current_page_sizes

    return pages_font_dict