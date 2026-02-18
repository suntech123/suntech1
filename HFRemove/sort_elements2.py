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