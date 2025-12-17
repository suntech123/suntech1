def detect_grid_table(self) -> float:
        """
        Returns confidence (0.0 to 1.0) based on grid lines.
        Logic: Distinguishes 'Text Boxes' (L-junctions) from 'Tables' (T/+ junctions).
        """
        # 1. Separate H and V lines
        h_lines = [l for l in self.lines if l.orientation == 'H']
        v_lines = [l for l in self.lines if l.orientation == 'V']
        
        # If we don't have enough lines for a basic box, it's not a table
        if len(h_lines) < 2 or len(v_lines) < 2:
            return 0.0

        # 2. Count "Grid Intersections" (T-junctions and Cross-junctions)
        # A simple text box has 4 corners (L-junctions). 
        # A table has internal lines, creating T or + junctions.
        grid_intersection_count = 0
        
        # Tolerance for lines "touching"
        tol = 3.0 

        for h in h_lines:
            for v in v_lines:
                # Check if they intersect geometrically
                # H line spans X range; V line must be within that X range
                # V line spans Y range; H line must be within that Y range
                
                has_x_overlap = (h.x0 - tol <= v.x0 <= h.x1 + tol)
                has_y_overlap = (v.y0 - tol <= h.y0 <= v.y1 + tol)
                
                if has_x_overlap and has_y_overlap:
                    # They intersect. Now checks IF it is a "Grid" intersection.
                    
                    # Is the intersection strictly INSIDE the Horizontal line? (Not at the tip)
                    # e.g.   |
                    #      --+--  (Cross) or --+  (T-junction)
                    #        |
                    is_vertically_internal = (h.x0 + tol < v.x0 < h.x1 - tol)
                    
                    # Is the intersection strictly INSIDE the Vertical line?
                    is_horizontally_internal = (v.y0 + tol < h.y0 < v.y1 - tol)

                    # If it's internal to EITHER line, it's a grid structure.
                    # Text Box Corners fail this (they are at the ends of both lines).
                    if is_vertically_internal or is_horizontally_internal:
                        grid_intersection_count += 1

        # 3. Decision Threshold
        # A table with 1 header row and columns needs at least 2 T-junctions 
        # (where the header line meets the left and right borders).
        if grid_intersection_count >= 2:
            return 1.0
        
        # Fallback: If no T-junctions, but massive amount of lines (e.g. borderless grid)
        unique_h = get_unique_axes([l.y0 for l in h_lines])
        unique_v = get_unique_axes([l.x0 for l in v_lines])
        
        # Require 3+ cols AND 4+ rows to accept a non-intersecting grid
        if unique_v > 3 and unique_h > 4:
            return 0.8
            
        return 0.0