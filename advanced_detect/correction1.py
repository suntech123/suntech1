class PageProcessor:
    def __init__(self, page: fitz.Page):
        self.page = page
        self.width = page.rect.width
        self.height = page.rect.height
        
        # Lazy loaders
        self._lines: List[VisualLine] = None
        self._spans: List[TextSpan] = None
        self._words: List[PDFWord] = None
        self._xml: str = None
        self._images: List[dict] = None

    @property
    def lines(self):
        if self._lines is None:
            raw = self.page.get_drawings()
            self._lines = []
            for p in raw:
                r = p['rect']
                
                # 1. Classification logic (Orientation)
                if r.width > r.height * 5: 
                    ori = 'H'
                elif r.height > r.width * 5: 
                    ori = 'V'
                else: 
                    ori = 'RECT'
                
                # 2. Fill Logic (Fix for your error)
                # p['type'] is 'f' for fill, 's' for stroke
                is_fill_val = (p['type'] == 'f') 

                # 3. Append with ALL required arguments
                self._lines.append(VisualLine(
                    r.x0, 
                    r.y0, 
                    r.x1, 
                    r.y1, 
                    ori, 
                    1.0,          # Thickness
                    is_fill_val   # <--- This was missing!
                ))
        return self._lines

    @property
    def spans(self):
        if self._spans is None:
            self._spans = []
            # Flatten get_text("dict")
            for b in self.page.get_text("dict")["blocks"]:
                if b["type"] == 0:
                    for l in b["lines"]:
                        for s in l["spans"]:
                            self._spans.append(TextSpan(
                                s["bbox"][0], s["bbox"][1], s["bbox"][2], s["bbox"][3],
                                s["text"], s["font"], s["size"], s["flags"]
                            ))
        return self._spans

    @property
    def words(self):
        if self._words is None:
            raw = self.page.get_text("words")
            self._words = [PDFWord(w[0], w[1], w[2], w[3], w[4]) for w in raw]
        return self._words

    @property
    def xml(self):
        if self._xml is None:
            self._xml = self.page.get_text("xml")
        return self._xml

    # --- Detection Strategies (Same as before) ---
    
    def detect_grid_table(self) -> float:
        """Returns confidence (0.0 to 1.0) based on grid lines."""
        h_lines = [l.y0 for l in self.lines if l.orientation == 'H']
        v_lines = [l.x0 for l in self.lines if l.orientation == 'V']
        
        unique_h = get_unique_axes(h_lines)
        unique_v = get_unique_axes(v_lines)
        
        if unique_h >= 3 and unique_v >= 3: return 1.0
        if unique_h >= 2 and unique_v >= 2: return 0.6
        return 0.0

    def detect_semantic_table(self) -> float:
        keywords = ["Description", "Qty", "Quantity", "Price", "Amount", "Total", "Date"]
        found_keywords = []
        for kw in keywords:
            rects = self.page.search_for(kw, hit_max=1)
            if rects: found_keywords.append(rects[0])
        
        if len(found_keywords) < 2: return 0.0
            
        y_coords = [r.y0 for r in found_keywords]
        unique_rows = get_unique_axes(y_coords, tolerance=5.0)
        
        if unique_rows == 1: return 0.9 
        return 0.3 

    def detect_structure_or_image(self) -> str:
        if "<Table" in self.xml or "<TR" in self.xml: return "TAGGED_TABLE"
        
        images = self.page.get_image_info()
        for img in images:
            bbox = img['bbox']
            area = (bbox[2]-bbox[0]) * (bbox[3]-bbox[1])
            page_area = self.width * self.height
            if (area / page_area) > 0.15: return "IMAGE_TABLE"
        return "NONE"