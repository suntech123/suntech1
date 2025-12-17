def detect_semantic_table(self) -> float:
        keywords = ["Description", "Qty", "Quantity", "Price", "Amount", "Total", "Date"]
        found_keywords = []
        
        for kw in keywords:
            # FIX: Remove 'hit_max=1'. 
            # search_for() now returns a list of all occurrences.
            rects = self.page.search_for(kw)
            
            # We just take the first one if it exists
            if rects:
                found_keywords.append(rects[0])
        
        if len(found_keywords) < 2: 
            return 0.0
            
        y_coords = [r.y0 for r in found_keywords]
        # Check if keywords align on the same row (tolerance 5.0)
        unique_rows = get_unique_axes(y_coords, tolerance=5.0)
        
        if unique_rows == 1: 
            return 0.9 
        return 0.3