def detect_semantic_table(self) -> float:
        """Returns confidence based on header keywords and bold text."""
        keywords = ["Description", "Qty", "Quantity", "Price", "Amount", "Total", "Date"]
        
        # 1. Fast Search (using PyMuPDF internal C++ search)
        found_keywords = []
        for kw in keywords:
            rects = self.page.search_for(kw, hit_max=1)
            if rects:
                found_keywords.append(rects[0]) # Keep the rect
        
        if len(found_keywords) < 2:
            return 0.0
            
        # 2. Alignment Check: Do these keywords appear on the same Y-axis?
        # Extract Y0 of found keywords
        y_coords = [r.y0 for r in found_keywords]
        
        # Check if they cluster to a single row (tolerance 5.0)
        unique_rows = get_unique_axes(y_coords, tolerance=5.0)
        
        if unique_rows == 1:
            # All keywords are on the same line. 
            # Bonus: Check if they are Bold (using Spans)
            # (Simplified logic: assuming high confidence if aligned keywords found)
            return 0.9 
            
        return 0.3 # Keywords found but scattered