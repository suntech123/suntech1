from dataclasses import dataclass

@dataclass(slots=True)
class PDFWord:
    x0: float
    y0: float
    x1: float
    y1: float
    text: str
    block_no: int
    line_no: int
    word_no: int

    @property
    def center_x(self):
        return (self.x0 + self.x1) / 2

    @property
    def height(self):
        return self.y1 - self.y0

# --- How to populate it ---
# raw_output is the list from page.get_text("words")
structured_data = [PDFWord(*w) for w in raw_output]

# --- How an algorithm uses it ---
# Example: Sort by vertical position (Y) then horizontal (X)
structured_data.sort(key=lambda w: (w.y0, w.x0))

# Example: Check if two words are on the same line
if abs(word_a.y0 - word_b.y0) < 3.0:
    print("Same Row")