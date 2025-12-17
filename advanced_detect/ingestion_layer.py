class PageProcessor:
    def __init__(self, page: fitz.Page):
        self.page = page
        self.width = page.rect.width
        self.height = page.rect.height
        
        # Lazy loaders (populated only when needed)
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
                # Basic Classification logic
                if r.width > r.height * 5: ori = 'H'
                elif r.height > r.width * 5: ori = 'V'
                else: ori = 'RECT'
                self._lines.append(VisualLine(r.x0, r.y0, r.x1, r.y1, ori, 1.0))
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