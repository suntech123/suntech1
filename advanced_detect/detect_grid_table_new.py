def detect_grid_table(self) -> float:
        """
        Robust Grid Detection:
        1. Uses Dynamic Tolerance to bridge PDF gaps.
        2. Uses Connection Counting to distinguish Boxes from Tables.
        """
        # 1. Get the dynamic tolerances
        tols = self.tolerances 
        i_tol = tols['intersect'] # This will be at least 3.0
        c_tol = tols['cluster']

        h_lines = [l for l in self.lines if l.orientation == 'H']
        v_lines = [l for l in self.lines if l.orientation == 'V']
        
        # Need at least a basic box structure to continue
        if len(h_lines) < 2 or len(v_lines) < 2:
            return 0.0

        # 2. Count Connections (Topology Check)
        # We track how many perpendicular lines each line touches.
        h_connections = [0] * len(h_lines)
        v_connections = [0] * len(v_lines)

        for i, h in enumerate(h_lines):
            for j, v in enumerate(v_lines):
                # USE DYNAMIC TOLERANCE HERE (i_tol)
                # If i_tol is 3.0, we catch gaps up to 3 pixels wide.
                # This is safe because we aren't checking for "Internal/External" anymore,
                # just "Connected vs Not Connected".
                
                has_x_overlap = (h.x0 - i_tol <= v.x0 <= h.x1 + i_tol)
                has_y_overlap = (v.y0 - i_tol <= h.y0 <= v.y1 + i_tol)
                
                if has_x_overlap and has_y_overlap:
                    h_connections[i] += 1
                    v_connections[j] += 1

        # 3. The Decision Logic
        max_h_conn = max(h_connections) if h_connections else 0
        max_v_conn = max(v_connections) if v_connections else 0

        # A Box has max 2 connections per line.
        # A Grid (Table) has at least one line with 3+ connections.
        if max_h_conn > 2 or max_v_conn > 2:
            return 1.0
            
        # 4. Fallback (Massive Borderless Grids)
        # Use the Clustering Tolerance (c_tol) here
        unique_h = get_unique_axes([l.y0 for l in h_lines], tolerance=c_tol)
        unique_v = get_unique_axes([l.x0 for l in v_lines], tolerance=c_tol)
        
        if unique_v > 3 and unique_h > 4:
            return 0.8
            
        return 0.0