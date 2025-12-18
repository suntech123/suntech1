def detect_grid_table(self) -> float:
        """
        Smart Grid Detection:
        Distinguishes 'Text Boxes' (L-Junctions) from 'Tables' (T-Junctions/Crosses).
        """
        tols = self.tolerances 
        i_tol = tols['intersect'] # Use the safe floor (e.g., 3.0)

        h_lines = [l for l in self.lines if l.orientation == 'H']
        v_lines = [l for l in self.lines if l.orientation == 'V']
        
        if len(h_lines) < 2 or len(v_lines) < 2:
            return 0.0

        # Counters for specific intersection types
        t_junctions = 0      # Strong Table Signal
        cross_junctions = 0  # Strong Table Signal
        l_junctions = 0      # Box Signal (Weak)

        for h in h_lines:
            for v in v_lines:
                # 1. Check for physical connection (Overlap)
                has_x_overlap = (h.x0 - i_tol <= v.x0 <= h.x1 + i_tol)
                has_y_overlap = (v.y0 - i_tol <= h.y0 <= v.y1 + i_tol)
                
                if has_x_overlap and has_y_overlap:
                    # They touch. Now, WHAT KIND of connection is it?
                    
                    # Check if V is "strictly inside" H (not at the tips)
                    # We use i_tol as a buffer to ensure we aren't at the corner
                    v_is_inside_h = (v.x0 > h.x0 + i_tol) and (v.x0 < h.x1 - i_tol)
                    
                    # Check if H is "strictly inside" V
                    h_is_inside_v = (h.y0 > v.y0 + i_tol) and (h.y0 < v.y1 - i_tol)

                    if v_is_inside_h and h_is_inside_v:
                        cross_junctions += 1 # It's a (+)
                    elif v_is_inside_h or h_is_inside_v:
                        t_junctions += 1     # It's a (T)
                    else:
                        l_junctions += 1     # It's a Corner (L)

        # --- THE DECISION LOGIC ---

        # Case 1: The Strong Table
        # A table almost always has internal dividers.
        # Even a simple 2x2 table has a central cross or T-junctions at the header.
        # We require at least 2 internal intersections (T or +) to call it a grid.
        if (t_junctions + cross_junctions) >= 2:
            return 1.0

        # Case 2: The "Text Box" Trap
        # If we have only L-junctions (Corners) and NO internal dividers, 
        # it is a Text Box. Return 0.0.
        if l_junctions > 0 and (t_junctions + cross_junctions) == 0:
            return 0.0
            
        # Case 3: The "Row List" / Borderless Fallback
        # ONLY trigger this if we didn't find specific box corners.
        # If we found 4 corners and nothing else, Case 2 kills it.
        # This fallback is for when lines don't touch at all.
        
        # Danger: Your previous fallback (unique_v > 3 and unique_h > 4) 
        # causes false positives on pages with multiple boxes.
        # Fix: We require High Density of H-lines relative to V-lines.
        
        c_tol = tols['cluster']
        unique_h = get_unique_axes([l.y0 for l in h_lines], tolerance=c_tol)
        unique_v = get_unique_axes([l.x0 for l in v_lines], tolerance=c_tol)
        
        # A list-style table usually has MANY rows (5+) but few cols (2-3).
        # We increase the threshold to avoid picking up 3 scattered boxes.
        if unique_h >= 6 and unique_v >= 2:
            return 0.8
            
        return 0.0