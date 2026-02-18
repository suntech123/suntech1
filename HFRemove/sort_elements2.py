import fitz
from itertools import groupby
from typing import List, Dict, Any

# Ensure you have your PageElement class and PageParser imported/defined
# from your_module import PageElement, PageParser

def analyze_document_structured(pdf_path: str) -> List[Dict[int, List[List['PageElement']]]]:
    """
    Analyzes a PDF and returns structured data.
    
    Returns:
        A list of dictionaries. Each dictionary represents a page.
        Format: [ { page_num: [ [row_1_elements], [row_2_elements], ... ] }, ... ]
    """
    doc = fitz.open(pdf_path)
    all_elements = []

    # --- 1. INGESTION ---
    for page in doc:
        all_elements.extend(PageParser.extract_elements(page))
    
    doc.close()

    # --- 2. GLOBAL SORTING ---
    # Sort hierarchy:
    # 1. Page Number (Ascending)
    # 2. Vertical Y Position (Rounded to nearest int to group lines)
    # 3. Horizontal X Position (Left to Right reading order)
    all_elements.sort(key=lambda e: (e.page_num, round(e.rect.y0), e.rect.x0))

    structured_results = []

    # --- 3. GROUPING BY PAGE ---
    for page_num, page_group in groupby(all_elements, key=lambda e: e.page_num):
        
        # Convert iterator to list so we can iterate it multiple times
        page_items = list(page_group)
        
        # --- 4. GROUPING BY ROW (VISUAL LINES) ---
        page_rows = []
        
        # Group items that share roughly the same Y position
        # We use round() to handle float jitter (e.g., 10.0 vs 10.001)
        for y_val, row_items in groupby(page_items, key=lambda e: round(e.rect.y0)):
            # Convert the row iterator to a list (This is one "Visual Line")
            row_list = list(row_items)
            page_rows.append(row_list)

        # Append to results
        # Key: Page Number (1-based for human readability, or keep 0-based)
        # Value: The list of rows
        structured_results.append({
            page_num + 1: page_rows 
        })

    return structured_results

######

def print_structured_report(data: List[Dict[int, List[List['PageElement']]]]):
    """
    Parses the structured return value and prints it nicely to the console.
    """
    print(f"Total Pages Analyzed: {len(data)}")
    
    for page_entry in data:
        # Extract key and value (there is only one key per dict in this structure)
        for page_num, rows in page_entry.items():
            print(f"\n{'='*40}")
            print(f"📄 PAGE {page_num} (Total Rows: {len(rows)})")
            print(f"{'='*40}")
            
            # Loop through the first 5 rows (Header Zone) and last 3 (Footer Zone)
            # to keep the output clean
            
            print("--- [TOP 5 ROWS] ---")
            for i, row in enumerate(rows[:5]):
                # Join text of all elements in this row
                row_text = " | ".join([e.text for e in row])
                y_pos = row[0].rect.y0
                print(f" Row {i+1} (y={y_pos:.1f}): {row_text}")

            if len(rows) > 10:
                print(f"... (Skipping {len(rows) - 8} body rows) ...")

            print("--- [BOTTOM 3 ROWS] ---")
            for i, row in enumerate(rows[-3:]):
                row_text = " | ".join([e.text for e in row])
                y_pos = row[0].rect.y0
                # Calculate original row index
                orig_idx = len(rows) - 3 + i + 1
                print(f" Row {orig_idx} (y={y_pos:.1f}): {row_text}")

#####

# 1. Run the analysis
results = analyze_document_structured("medical_policy.pdf")

# 2. Print the verification report
print_structured_report(results)

# 3. Accessing data programmatically (Logic Layer)
# Example: Get Page 1, Row 0 (The very top line)
first_page_dict = results[0]      # { 1: [[row], [row]] }
page_num_key = list(first_page_dict.keys())[0] # Gets '1'
rows = first_page_dict[page_num_key]

top_row = rows[0] # List of PageElements
print(f"\nTop Left Item: {top_row[0].text}")

# Example Logic: Loop through all pages to find a specific header
for page_entry in results:
    for p_num, rows in page_entry.items():
        # Check the first row of every page
        first_row_text = " ".join([e.text for e in rows[0]]).lower()
        
        if "confidential" in first_row_text:
            print(f"⚠️ Alert: Page {p_num} starts with Confidential marker!")