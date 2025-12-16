import fitz  # PyMuPDF
from typing import List, Tuple

def count_unique_coords(coords: List[float], tolerance: float = 3.0) -> int:
    """
    Clusters coordinates that are close to each other (within tolerance)
    and returns the count of unique cluster centers (lines).
    """
    if not coords:
        return 0
    
    # Sort coordinates to handle them sequentially
    coords.sort()
    
    unique_count = 0
    # Initialize with a value far lower than any possible PDF coordinate
    current_cluster_ref = -100.0
    
    for c in coords:
        # If the current coordinate is far from the reference, it's a new line
        if abs(c - current_cluster_ref) > tolerance:
            unique_count += 1
            current_cluster_ref = c
            
    return unique_count

def page_has_grid(page: fitz.Page) -> bool:
    """
    Analyzes vector graphics to determine if a page contains a table-like grid.
    """
    # 1. Get all vector drawings (lines, rectangles, fills)
    paths = page.get_drawings()
    
    horizontal_y_coords = []
    vertical_x_coords = []
    
    for path in paths:
        rect = path["rect"]
        
        # Calculate aspect ratio
        width = rect.width
        height = rect.height
        
        # 2. Classify shapes
        # Heuristic: A horizontal line is much wider than it is tall
        # We use a factor of 5 to be safe (width > 5x height)
        if width > height * 5 and height < 5: 
            # It's a horizontal line (separator)
            # We store the Y coordinate
            horizontal_y_coords.append(rect.y0)
            
        # Heuristic: A vertical line is much taller than it is wide
        elif height > width * 5 and width < 5:
            # It's a vertical line (column border)
            # We store the X coordinate
            vertical_x_coords.append(rect.x0)
            
        # Note: If it's a proper stroked rectangle (box), PyMuPDF 
        # breaks it down into lines or we can extract the borders.
        # For simplicity, we assume tables are made of line segments.

    # 3. Count unique visual lines
    # We use a tolerance of 2 pixels to group overlapping/close segments
    h_count = count_unique_coords(horizontal_y_coords, tolerance=2.0)
    v_count = count_unique_coords(vertical_x_coords, tolerance=2.0)
    
    print(f"Page {page.number + 1}: Found {h_count} Horizontal Lines, {v_count} Vertical Lines.")

    # 4. Define Threshold for a "Grid"
    # A minimal table usually needs:
    # - At least 3 horizontal lines (Top border, Header separator, Bottom border)
    # - At least 3 vertical lines (Left border, Middle separator, Right border)
    has_grid = h_count >= 3 and v_count >= 3
    
    return has_grid

# --- Usage Example ---
if __name__ == "__main__":
    pdf_path = "sample_with_tables.pdf"
    
    try:
        doc = fitz.open(pdf_path)
        
        for page in doc:
            if page_has_grid(page):
                print(f"✅ Page {page.number + 1} contains a table grid.")
            else:
                print(f"❌ Page {page.number + 1} has no significant grid.")
                
    except Exception as e:
        print(f"Error processing PDF: {e}")