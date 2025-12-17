def detect_grid_table(self) -> float:
        """Returns confidence (0.0 to 1.0) based on grid lines."""
        h_lines = [l.y0 for l in self.lines if l.orientation == 'H']
        v_lines = [l.x0 for l in self.lines if l.orientation == 'V']
        
        unique_h = get_unique_axes(h_lines)
        unique_v = get_unique_axes(v_lines)
        
        # A valid grid usually needs 3+ rows and 2+ cols (3 vertical lines)
        if unique_h >= 3 and unique_v >= 3:
            return 1.0  # High confidence
        if unique_h >= 2 and unique_v >= 2:
            return 0.6  # Medium confidence (maybe a box)
        return 0.0