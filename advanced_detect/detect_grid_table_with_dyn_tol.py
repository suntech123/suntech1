def detect_grid_table(self) -> float:
        """
        Returns confidence (0.0 to 1.0) based on grid lines using Dynamic Tolerance.
        """
        # 1. Retrieve Dynamic Tolerances
        # 'intersect' is tighter (for touching lines)
        # 'cluster' is looser (for grouping rows)
        tols = self.tolerances 
        i_tol = tols['intersect']
        c_tol = tols['cluster']

        # 2. Separate H and V lines
        h_lines = [l for l in self.lines if l.orientation == 'H']
        v_lines = [l for l in self.lines if l.orientation == 'V']
        
        if len(h_lines) < 2 or len(v_lines) < 2:
            return 0.0

        # 3. Count "Grid Intersections" using Dynamic Tolerance
        grid_intersection_count = 0
        
        for h in h_lines:
            for v in v_lines:
                # Check for geometric intersection using dynamic 'i_tol'
                # We expand the range of the line by the tolerance to catch 'near misses'
                has_x_overlap = (h.x0 - i_tol <= v.x0 <= h.x1 + i_tol)
                has_y_overlap = (v.y0 - i_tol <= h.y0 <= v.y1 + i_tol)
                
                if has_x_overlap and has_y_overlap:
                    # They intersect. Now checks IF it is a "Grid" intersection (T or +).
                    # We check if the intersection is 'internal' (not at the exact tip).
                    # We use i_tol here to ensure we aren't confusing a thick corner for a T.
                    
                    is_vertically_internal = (h.x0 + i_tol < v.x0 < h.x1 - i_tol)
                    is_horizontally_internal = (v.y0 + i_tol < h.y0 < v.y1 - i_tol)

                    if is_vertically_internal or is_horizontally_internal:
                        grid_intersection_count += 1

        # 4. Decision Threshold
        if grid_intersection_count >= 2:
            return 1.0
        
        # 5. Fallback: Massive Lines (Borderless/Open Grid)
        # We use 'cluster_tol' here because we are grouping visual rows, 
        # which requires a looser tolerance than intersection.
        unique_h = get_unique_axes([l.y0 for l in h_lines], tolerance=c_tol)
        unique_v = get_unique_axes([l.x0 for l in v_lines], tolerance=c_tol)
        
        if unique_v > 3 and unique_h > 4:
            return 0.8
            
        return 0.0