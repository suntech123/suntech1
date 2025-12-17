@property
    def lines(self):
        if self._lines is None:
            raw = self.page.get_drawings()
            self._lines = []
            for p in raw:
                r = p['rect']
                
                # 1. Determine Orientation
                if r.width > r.height * 5: 
                    ori = 'H'
                elif r.height > r.width * 5: 
                    ori = 'V'
                else: 
                    ori = 'RECT'
                
                # 2. Determine Fill vs Stroke
                # PyMuPDF types: 's' (stroke), 'f' (fill), 'fs' (fill+stroke)
                draw_type = p.get('type', 's') 
                is_fill = 'f' in draw_type

                # 3. Calculate Real Visual Thickness
                if is_fill:
                    # For fills, the 'thickness' is the thin dimension of the rectangle
                    if ori == 'H':
                        thickness = r.height
                    elif ori == 'V':
                        thickness = r.width
                    else:
                        # For a box, thickness is ambiguous, take the smaller dim
                        thickness = min(r.width, r.height)
                else:
                    # For strokes, use the explicit pen width from PDF
                    # Default to 1.0 if None (rare)
                    thickness = p.get('width') or 1.0

                # 4. Append to list
                self._lines.append(VisualLine(
                    x0=r.x0, 
                    y0=r.y0, 
                    x1=r.x1, 
                    y1=r.y1, 
                    orientation=ori, 
                    thickness=thickness,  # <--- Now dynamically calculated
                    is_fill=is_fill
                ))
        return self._lines