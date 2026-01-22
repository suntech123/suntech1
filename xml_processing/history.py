import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import sys
import os

def analyze_pdf_xml(xml_file, page_number=1, bin_size=5):
    """
    Parses pdftohtml XML and plots layout histograms.
    
    Args:
        xml_file (str): Path to the .xml file
        page_number (int): The page number to analyze (1-based index)
        bin_size (int): Grouping pixels for smoother histograms (default 5px)
    """
    
    if not os.path.exists(xml_file):
        print(f"Error: File '{xml_file}' not found.")
        return

    tree = ET.parse(xml_file)
    root = tree.getroot()

    # Find the specific page
    # pdftohtml pages are usually 1-indexed in the 'number' attribute
    target_page = None
    for page in root.findall('page'):
        if int(page.attrib.get('number', 0)) == page_number:
            target_page = page
            break
    
    if target_page is None:
        print(f"Error: Page {page_number} not found in XML.")
        return

    # Get Page Dimensions
    page_width = int(target_page.attrib.get('width', 0))
    page_height = int(target_page.attrib.get('height', 0))

    # Collect Coordinates
    x_starts = []  # Left attribute
    y_starts = []  # Top attribute
    widths = []    # To visualize text length in scatter plot

    for text in target_page.findall('text'):
        # Skip empty text tags
        if text.text is None or not text.text.strip():
            continue

        try:
            left = int(text.attrib.get('left', 0))
            top = int(text.attrib.get('top', 0))
            w = int(text.attrib.get('width', 0))
            
            x_starts.append(left)
            y_starts.append(top)
            widths.append(w)
        except ValueError:
            continue

    if not x_starts:
        print("No text found on this page.")
        return

    # --- Plotting ---
    fig = plt.figure(figsize=(15, 10))
    grid = plt.GridSpec(2, 2, width_ratios=[1, 3], height_ratios=[1, 3], wspace=0.1, hspace=0.1)

    # 1. Top Right: X-Axis Histogram (Horizontal Distribution)
    ax_top = fig.add_subplot(grid[0, 1])
    ax_top.hist(x_starts, bins=range(0, page_width, bin_size), color='skyblue', edgecolor='black', alpha=0.7)
    ax_top.set_xlim(0, page_width)
    ax_top.set_title("Horizontal Alignment (Left Coordinate)", fontsize=10)
    ax_top.set_ylabel("Frequency")
    # Hide X labels to share with main plot
    plt.setp(ax_top.get_xticklabels(), visible=False)

    # 2. Bottom Left: Y-Axis Histogram (Vertical Distribution)
    ax_left = fig.add_subplot(grid[1, 0])
    # orientation='horizontal' makes bars go sideways
    ax_left.hist(y_starts, bins=range(0, page_height, bin_size), orientation='horizontal', color='salmon', edgecolor='black', alpha=0.7)
    ax_left.set_ylim(page_height, 0) # Invert Y axis to match PDF coordinates (0 is top)
    ax_left.set_xlabel("Frequency")
    ax_left.set_title("Vertical Position (Top Coordinate)", fontsize=10)
    # Hide Y labels to share with main plot
    # plt.setp(ax_left.get_yticklabels(), visible=False)

    # 3. Bottom Right: The Page Scatter Plot (Recreating the Page View)
    ax_main = fig.add_subplot(grid[1, 1], sharex=ax_top, sharey=ax_left)
    
    # Plot text blocks as horizontal lines
    # We use 'left' as start and 'left + width' to draw a line mimicking text
    for x, y, w in zip(x_starts, y_starts, widths):
        ax_main.plot([x, x + w], [y, y], color='gray', linewidth=2, alpha=0.5)
        # Add a dot at the start to emphasize alignment
        ax_main.scatter(x, y, s=10, color='blue', alpha=0.6)

    ax_main.set_xlim(0, page_width)
    ax_main.set_ylim(page_height, 0) # Invert Y axis
    ax_main.grid(True, linestyle='--', alpha=0.3)
    ax_main.set_title(f"Visualized Text Layout (Page {page_number})", fontsize=12)

    # Add interpretation guide lines
    # Detect roughly where the header/footer might be based on 10% thresholds
    ax_left.axhline(page_height * 0.1, color='red', linestyle='--', alpha=0.5, label='10% Margin')
    ax_left.axhline(page_height * 0.9, color='red', linestyle='--', alpha=0.5)
    ax_left.legend(loc='upper right', fontsize='small')

    plt.suptitle(f"Layout Analysis for PDF Page {page_number}\n(Input: {os.path.basename(xml_file)})", fontsize=14)
    plt.show()

# --- USAGE ---
# Generate XML first: pdftohtml -xml -stdout input.pdf > output.xml
# Then run this script:
if __name__ == "__main__":
    # Replace with your actual XML filename
    xml_filename = "output.xml" 
    
    # You can change the page number here
    analyze_pdf_xml(xml_filename, page_number=1)