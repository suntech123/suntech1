import statistics

def calculate_dynamic_tolerances(lines: list['VisualLine']) -> dict:
    if not lines:
        return {'intersect': 3.0, 'cluster': 3.0} # Fallback defaults

    # 1. Extract thicknesses (Stroke widths)
    # We filter out 0.0 or extremely thin lines which might be artifacts
    thicknesses = [l.thickness for l in lines if l.thickness > 0.1]
    
    if not thicknesses:
        base_thickness = 1.0
    else:
        # Use Median to avoid outliers (like a massive thick banner border)
        base_thickness = statistics.median(thicknesses)

    # --- Tolerance 1: Intersection (Touch) ---
    # Logic: If two lines are within 50% of their own thickness of each other,
    # visual bleed makes them look connected.
    # We add a floor (0.5) for floating point errors.
    intersect_tol = max(0.5, base_thickness * 1.5)

    # --- Tolerance 2: Clustering (Row Grouping) ---
    # Logic: Rows are usually separated by whitespace.
    # We want to group lines that are basically on top of each other.
    # Usually slightly looser than intersection.
    cluster_tol = max(1.0, base_thickness * 2.0)

    return {
        'intersect': intersect_tol,
        'cluster': cluster_tol
    }




#≠===================

class PageProcessor:
    def __init__(self, page: fitz.Page):
        # ... existing init ...
        self._tolerances = None

    @property
    def tolerances(self):
        if self._tolerances is None:
            # Calculate based on the lines we extracted
            self._tolerances = calculate_dynamic_tolerances(self.lines)
        return self._tolerances

    def detect_grid_table(self) -> float:
        # Get dynamic value
        tol = self.tolerances['intersect'] 
        
        h_lines = [l for l in self.lines if l.orientation == 'H']
        v_lines = [l for l in self.lines if l.orientation == 'V']

        # ... (rest of logic) ...
        
        # Use dynamic 'tol' in your loop
        has_x_overlap = (h.x0 - tol <= v.x0 <= h.x1 + tol)
        has_y_overlap = (v.y0 - tol <= h.y0 <= v.y1 + tol)
        
        # ...