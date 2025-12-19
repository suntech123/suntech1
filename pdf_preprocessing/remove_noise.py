import fitz  # PyMuPDF

def get_clean_page_drawings(page: fitz.Page, 
                            speck_threshold: float = 2.0, 
                            ignore_white: bool = True):
    """
    Extracts vector drawings from a PyMuPDF page and filters out noise.
    
    Args:
        page (fitz.Page): The page object to process.
        speck_threshold (float): The maximum width/height (in points) to consider a 'speck'.
        ignore_white (bool): If True, filters out white-on-white shapes (common in OCR).

    Returns:
        list: A list of dictionary objects representing valid, clean vector drawings.
    """
    
    # 1. Get all drawings from the page
    raw_drawings = page.get_drawings()
    clean_drawings = []
    
    # Get page boundaries for intersection checks
    page_rect = page.rect

    for path in raw_drawings:
        # --- CRITERIA 1: GEOMETRY VALIDITY ---
        # If a path has no items (lines/curves), it's empty data
        if not path["items"]:
            continue

        rect = path["rect"]
        
        # --- CRITERIA 2: OFF-PAGE NOISE ---
        # If the drawing is completely outside the visible page area
        if not rect.intersects(page_rect):
            continue

        # --- CRITERIA 3: SIZE (SPECKS) ---
        # Identify tiny dots usually resulting from scanning dust.
        # We check if BOTH width and height are below threshold.
        # (We don't filter thin lines like separators which have small height but large width)
        if rect.width < speck_threshold and rect.height < speck_threshold:
            continue

        # --- CRITERIA 4: VISIBILITY (TRANSPARENCY) ---
        # Check opacity. If stroke and fill opacity are effectively zero, it's invisible.
        # path['opacity'] is stroke opacity, path['fill_opacity'] is fill opacity.
        # Note: Some PDF generators use None to imply 1.0, others use floats.
        stroke_op = path.get("opacity", 1.0)
        fill_op = path.get("fill_opacity", 1.0)
        
        # If explicitly set to 0, it's invisible noise
        if stroke_op == 0 and fill_op == 0:
            continue

        # --- CRITERIA 5: COLOR (INVISIBLE OR WHITE-ON-WHITE) ---
        stroke_color = path.get("color") # None means no stroke
        fill_color = path.get("fill")    # None means no fill
        
        # Case A: Totally empty style (No stroke AND No fill)
        if stroke_color is None and fill_color is None:
            continue

        # Case B: White masking (Optional)
        # Often used to hide things in PDFs. If it's a white fill with no border, 
        # it might be considered noise depending on use case.
        if ignore_white:
            is_white_fill = fill_color == (1.0, 1.0, 1.0)
            has_no_border = stroke_color is None or stroke_color == (1.0, 1.0, 1.0)
            
            if is_white_fill and has_no_border:
                continue

        # If it passed all filters, it is valid content
        clean_drawings.append(path)

    return clean_drawings

# ==========================================
# Example Usage
# ==========================================
if __name__ == "__main__":
    # 1. Open Document
    doc = fitz.open("sample.pdf") # Replace with your PDF path
    page = doc[0]

    # 2. Get Cleaned Drawings
    cleaned_vectors = get_clean_page_drawings(page, speck_threshold=1.5)

    print(f"Original paths: {len(page.get_drawings())}")
    print(f"Cleaned paths:  {len(cleaned_vectors)}")

    # 3. (Optional) Visualize the result by drawing them onto a NEW PDF
    # This proves we have isolated the good data.
    out_doc = fitz.open()
    out_page = out_doc.new_page(width=page.rect.width, height=page.rect.height)
    shape = out_page.new_shape()

    for path in cleaned_vectors:
        # Re-construct the drawing from the dictionary
        # We only apply the drawing commands and the stroke/fill
        
        # 1. Apply opacity (simplification for visualization)
        shape.finish(
            color=path["color"], 
            fill=path["fill"], 
            width=path["width"],
            lineJoin=path["lineJoin"],
            lineCap=path["lineCap"],
            closePath=path["closePath"]
        )
        
        # 2. Re-draw the items (lines, curves, rects)
        for item in path["items"]:
            op = item[0] # Operation type: 'l', 'c', 're', 'qu'
            if op == "l": # Line
                shape.draw_line(item[1], item[2])
            elif op == "re": # Rectangle
                shape.draw_rect(item[1])
            elif op == "c": # Cubic Bezier
                shape.draw_bezier(item[1], item[2], item[3], item[4])
            # ... handle other types ('qu') if necessary

        shape.commit()

    # out_doc.save("cleaned_output.pdf")
