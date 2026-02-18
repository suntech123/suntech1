import fitz
from itertools import groupby
from typing import List, Dict

# Assuming PageElement and PageParser are defined as discussed previously...

def analyze_document(pdf_path: str):
    doc = fitz.open(pdf_path)
    all_elements: List[PageElement] = []

    # --- PHASE 1: INGESTION ---
    for page in doc:
        # Extract raw elements (unsorted)
        page_elems = PageParser.extract_elements(page)
        all_elements.extend(page_elems)

    # --- PHASE 2: GLOBAL SORTING ---
    # We sort by:
    # 1. Page Number (Keep pages distinct)
    # 2. Vertical Position (Rounded to nearest int to handle float jitter)
    # 3. Horizontal Position (Left-to-Right reading order)
    
    all_elements.sort(key=lambda e: (e.page_num, round(e.rect.y0), e.rect.x0))

    # --- PHASE 3: ANALYSIS (Per Page) ---
    # Now that data is sorted, we can group it efficiently.
    
    # Group by Page Number first
    for page_num, page_group in groupby(all_elements, key=lambda e: e.page_num):
        print(f"\n=== Processing Page {page_num + 1} ===")
        
        # Convert iterator to list for multiple passes
        page_items = list(page_group)
        
        # --- STRATEGY A: Line-by-Line Analysis (Clustering) ---
        # Since we already sorted by 'y0', we can group elements into "Visual Lines".
        # This is CRITICAL for healthcare docs where a header row might contain:
        # [Logo (Left)] ... [Title (Center)] ... [Doc ID (Right)]
        
        rows = []
        # Group items that share roughly the same Y position (within 1-2 pixels)
        for y_val, row_items in groupby(page_items, key=lambda e: round(e.rect.y0)):
            rows.append(list(row_items))

        # Inspect the top 5 rows (Header Zone candidates)
        for i, row in enumerate(rows[:5]):
            # Combine text from all elements in this row
            row_text = " | ".join([e.text for e in row if e.text])
            
            # Calculate the full width of this row (First item left to Last item right)
            row_rect = fitz.Rect(row[0].rect.x0, row[0].rect.y0, row[-1].rect.x1, row[-1].rect.y1)
            
            print(f"  [Row {i}] Y={row_rect.y0:.1f} | Content: {row_text}")

            # Example Logic: Detect Header Row
            # If row is at the very top AND contains "Policy" or "Page"
            if row_rect.y0 < 50: 
                has_keyword = any(x in row_text.lower() for x in ["policy", "page", "effective"])
                if has_keyword:
                    print(f"    >>> DETECTED HEADER ROW TO REMOVE <<<")

    doc.close()

# Usage
# analyze_document("hospital_policy.pdf")