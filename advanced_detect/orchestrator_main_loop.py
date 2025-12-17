def analyze_page_for_tables(doc: fitz.Document, page_num: int):
    page = doc[page_num]
    proc = PageProcessor(page)
    
    print(f"--- Analyzing Page {page_num + 1} ---")

    # 1. Check Explicit Tags (Fastest & Most Accurate)
    structure_type = proc.detect_structure_or_image()
    if structure_type == "TAGGED_TABLE":
        return "Table Detected (Source: Tagged PDF Structure)"
    
    # 2. Check Visual Grid (Most Common)
    grid_confidence = proc.detect_grid_table()
    if grid_confidence > 0.8:
        return "Table Detected (Source: Vector Grid Lines)"
        
    # 3. Check Semantic Headers (Borderless Tables)
    semantic_confidence = proc.detect_semantic_table()
    if semantic_confidence > 0.8:
        return "Table Detected (Source: Semantic Headers)"
    
    # 4. Fallback Checks
    if structure_type == "IMAGE_TABLE":
        return "Potential Table (Source: Large Image - Needs OCR)"
        
    if grid_confidence > 0.5 or semantic_confidence > 0.4:
        return "Uncertain (Possible weak table structure)"

    return "No Table Detected"

# --- Usage ---
if __name__ == "__main__":
    doc = fitz.open("sample.pdf")
    for i in range(len(doc)):
        result = analyze_page_for_tables(doc, i)
        print(result)