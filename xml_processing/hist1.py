import xml.etree.ElementTree as ET
from collections import Counter

def analyze_and_extract_global(xml_file):
    tree = ET.parse(xml_file)
    root = tree.getroot()
    
    all_pages = root.findall('page')
    total_pages = len(all_pages)
    
    # --- STEP 1: GLOBAL STATISTICAL TRAINING ---
    # We collect every 'top' and 'left' coordinate from the whole document.
    
    y_occurrences = [] # List of all Y coordinates found
    x_occurrences = [] # List of all X coordinates found
    
    # We use a bin size to handle slight jitter (e.g., y=30 vs y=31)
    BIN_SIZE = 5 
    
    print(f"Analyzing {total_pages} pages globally...")

    for page in all_pages:
        for text in page.findall('text'):
            if not text.text or not text.text.strip():
                continue
            
            try:
                top = int(text.attrib.get('top', 0))
                left = int(text.attrib.get('left', 0))
                
                # Round to nearest bin
                binned_y = round(top / BIN_SIZE) * BIN_SIZE
                binned_x = round(left / BIN_SIZE) * BIN_SIZE
                
                y_occurrences.append(binned_y)
                x_occurrences.append(binned_x)
            except ValueError:
                continue

    # --- STEP 2: IDENTIFY ZONES ---
    
    # Frequency of Y positions (How many pages have text at this height?)
    # Note: This is an approximation. Ideally, we count *unique pages* per Y.
    # But strictly counting occurrences works well for heavy headers.
    y_counts = Counter(y_occurrences)
    
    # Determine Header/Footer Cutoffs
    # We look for the "First Safe Body Line" and "Last Safe Body Line"
    
    # Heuristic: The body text is usually the most frequent Y range, 
    # but distributed evenly. Headers/Footers are clumps at the extremes.
    
    sorted_y = sorted(y_counts.keys())
    page_height = int(all_pages[0].attrib.get('height', 1000)) # Estimate
    
    # Find Header Cutoff:
    # Iterate from top (y=0) down. If a Y-position is present on > 50% of pages,
    # it is likely a header. Stop when frequency drops.
    
    header_cutoff = 0
    # Scan top 20% of page
    for y in sorted_y:
        if y > (page_height * 0.2): 
            break
        
        # If this Y position appears extremely often relative to page count
        # (e.g. it appears > 30% as often as there are pages)
        # We assume it's a recurring element.
        if y_counts[y] > (total_pages * 0.3):
            header_cutoff = y

    # Add a safety buffer (e.g., +20px) to skip the header completely
    header_cutoff += 20
    
    # Find Footer Cutoff (similar logic, scanning from bottom up)
    footer_cutoff = page_height
    for y in sorted(sorted_y, reverse=True):
        if y < (page_height * 0.8):
            break
        if y_counts[y] > (total_pages * 0.3):
            footer_cutoff = y
            
    footer_cutoff -= 20 # Safety buffer

    print(f"Detected Global Safe Zone: Y={header_cutoff} to Y={footer_cutoff}")

    # --- STEP 3: IDENTIFY SIDEBARS (Horizontal) ---
    x_counts = Counter(x_occurrences)
    
    # The most common X is the main paragraph indentation
    main_x_margin = x_counts.most_common(1)[0][0]
    
    # Anything starting significantly left of the main margin is a sidebar
    sidebar_cutoff = main_x_margin - 20
    
    print(f"Detected Main Margin at X={main_x_margin}. Excluding X < {sidebar_cutoff}")

    # --- STEP 4: EXTRACT CONTENT USING GLOBAL RULES ---
    
    full_document_text = []
    
    for page in all_pages:
        page_text = []
        for text in page.findall('text'):
            if not text.text or not text.text.strip():
                continue
                
            top = int(text.attrib.get('top', 0))
            left = int(text.attrib.get('left', 0))
            height = int(text.attrib.get('height', 0))
            
            # CHECK 1: Vertical Safe Zone
            if top < header_cutoff or (top + height) > footer_cutoff:
                continue # Skip Header/Footer
            
            # CHECK 2: Horizontal Safe Zone
            if left < sidebar_width: # Variable from logic above
                continue # Skip Left Sidebar
                
            # Optional: Skip Right Sidebar (if left > page_width * 0.8)
            
            page_text.append(text.text)
            
        full_document_text.append("\n".join(page_text))
        
    return "\n\n".join(full_document_text)

# usage
# clean_text = analyze_and_extract_global("output.xml")