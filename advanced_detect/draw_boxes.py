import fitz

def draw_visual_lines(doc: fitz.Document, page_num: int, lines: list['VisualLine'], output_path: str):
    """
    Draws colored bounding boxes around VisualLine objects on the PDF.
    Red   = Horizontal Lines
    Blue  = Vertical Lines
    Green = Rectangles/Backgrounds
    """
    page = doc[page_num]
    
    # 1. Create a Shape object (More efficient for batch drawing)
    shape = page.new_shape()
    
    for line in lines:
        # Create a PyMuPDF Rect from your VisualLine coordinates
        rect = fitz.Rect(line.x0, line.y0, line.x1, line.y1)
        
        # 2. Pick Color based on Orientation
        if line.orientation == 'H':
            color = (1, 0, 0)  # Red (RGB)
        elif line.orientation == 'V':
            color = (0, 0, 1)  # Blue (RGB)
        else:
            color = (0, 1, 0)  # Green (RGB) for RECTs
            
        # 3. Draw the Rectangle
        # width=0.5 makes a thin hairline border so you can see precision
        shape.draw_rect(rect)
        shape.finish(color=color, width=0.5)

        # Optional: If you want to see the 'Fill' logic
        # You could fill rectangles that were originally 'fills' with light yellow
        if line.is_fill:
             shape.draw_rect(rect)
             shape.finish(fill=(1, 1, 0), fill_opacity=0.3, stroke_opacity=0)

    # 4. Commit changes to the page
    shape.commit()
    
    # 5. Save
    doc.save(output_path)
    print(f"Debug PDF saved to: {output_path}")

# --- Usage ---
# Assuming you have 'doc', 'lines' (your sorted list), and a page number
# draw_visual_lines(doc, 0, lines, "debug_output.pdf")