import xml.etree.ElementTree as ET
from collections import Counter
import sys
import os

def sanitize_pdf_xml(input_file, output_file):
    """
    Reads pdftohtml XML, learns the layout globally, removes 
    headers/footers/sidebars, and saves clean XML.
    """
    
    if not os.path.exists(input_file):
        print(f"Error: Input file '{input_file}' not found.")
        return

    print(f"Processing: {input_file} ...")
    
    # Parse the XML
    tree = ET.parse(input_file)
    root = tree.getroot()
    all_pages = root.findall('page')
    
    if not all_pages:
        print("Error: No pages found in XML.")
        return

    # ==========================================
    # PHASE 1: GLOBAL STATISTICAL LEARNING
    # ==========================================
    
    # Configuration
    BIN_SIZE = 5  # px binning to handle scanner jitter
    page_height = int(all_pages[0].attrib.get('height', 1000))
    page_width = int(all_pages[0].attrib.get('width', 800))
    total_pages = len(all_pages)

    y_bins = []
    x_bins = []
    
    # 1. Collect coordinates from EVERY page
    for page in all_pages:
        for text in page.findall('text'):
            # Ignore empty elements
            if text.text is None and len(list(text)) == 0:
                continue
                
            try:
                top = int(text.attrib.get('top', 0))
                left = int(text.attrib.get('left', 0))
                
                # Round coordinates to nearest BIN_SIZE
                y_bins.append(round(top / BIN_SIZE) * BIN_SIZE)
                x_bins.append(round(left / BIN_SIZE) * BIN_SIZE)
            except ValueError:
                continue

    if not x_bins:
        print("No text data found to analyze.")
        return

    # 2. Compute Horizontal Cutoffs (Sidebars)
    x_counts = Counter(x_bins)
    
    # Find the "Main Body" Left Margin
    # The most frequent X-coordinate is statistically the start of the paragraph lines.
    main_x_mode = x_counts.most_common(1)[0][0]
    
    # Left Cutoff: Allow 30px variance for bullet points/indentation
    left_cutoff = main_x_mode - 30
    
    # Right Cutoff: Detect Right Sidebar
    # Check for a high-frequency text start in the right 30% of the page
    right_cutoff = page_width  # Default: Include everything to the right
    
    possible_right_sidebars = [x for x in x_counts.keys() if x > (page_width * 0.70)]
    if possible_right_sidebars:
        # Find the most frequent column start on the right side
        right_mode = max(possible_right_sidebars, key=lambda k: x_counts[k])
        
        # If this right-side column appears frequently (avg > 1 line per page)
        if x_counts[right_mode] > total_pages: 
             # It's a sidebar. Cut slightly before it starts.
             right_cutoff = right_mode - 10 

    # 3. Compute Vertical Cutoffs (Header/Footer)
    y_counts = Counter(y_bins)
    sorted_y = sorted(y_counts.keys())
    
    # Header: Scan top 20% of page
    header_cutoff = 0
    for y in sorted_y:
        if y > (page_height * 0.20): 
            break
        # Logic: If a line at this Y appears on > 25% of pages, it's likely a header
        if y_counts[y] > (total_pages * 0.25):
            header_cutoff = y
    
    # Add buffer to ensure we cut *below* the header text
    header_cutoff += 15 

    # Footer: Scan bottom 20% of page (bottom-up)
    footer_cutoff = page_height
    for y in sorted(sorted_y, reverse=True):
        if y < (page_height * 0.80): 
            break
        if y_counts[y] > (total_pages * 0.25):
            footer_cutoff = y
            
    # Add buffer to ensure we cut *above* the footer text
    footer_cutoff -= 15

    print("--- Layout Detected ---")
    print(f"X-Axis (Sidebars) : Keep text between X={left_cutoff} and X={right_cutoff}")
    print(f"Y-Axis (Head/Foot): Keep text between Y={header_cutoff} and Y={footer_cutoff}")
    print(f"Main Body Start   : X={main_x_mode}")

    # ==========================================
    # PHASE 2: FILTERING & SANITIZATION
    # ==========================================
    
    removed_count = 0
    
    for page in all_pages:
        # We assume standard extraction where text nodes are direct children of page
        # Create a list copy so we can remove items from the parent while iterating
        for text in list(page):
            if text.tag != 'text':
                continue
            
            try:
                top = int(text.attrib.get('top', 0))
                left = int(text.attrib.get('left', 0))
                height = int(text.attrib.get('height', 0))
                
                # Check 1: Is it a Header or Footer?
                # We check bottom edge for header (top + height) to be safe, 
                # and top edge for footer.
                if (top < header_cutoff) or (top > footer_cutoff):
                    page.remove(text)
                    removed_count += 1
                    continue
                
                # Check 2: Is it a Sidebar?
                if (left < left_cutoff) or (left >= right_cutoff):
                    page.remove(text)
                    removed_count += 1
                    continue
                    
            except ValueError:
                continue

    # ==========================================
    # PHASE 3: SAVE OUTPUT
    # ==========================================
    
    tree.write(output_file, encoding="UTF-8", xml_declaration=True)
    print(f"-----------------------------------")
    print(f"Done! Removed {removed_count} noise elements.")
    print(f"Sanitized XML saved to: {output_file}")

# --- USAGE EXAMPLE ---
if __name__ == "__main__":
    # 1. Provide your input file path
    input_xml = "output.xml"   # Generated via: pdftohtml -xml input.pdf output.xml
    output_xml = "sanitized.xml"
    
    sanitize_pdf_xml(input_xml, output_xml)