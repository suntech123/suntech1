import fitz  # PyMuPDF
import re
from collections import Counter
from typing import List, Dict, Any, Tuple, Optional

class PDFHeaderFooterExtractor:
    """
    Optimized class to extract headers, footers, and their positions from PDFs.
    Uses 'Tokenization/Masking' to normalize text for accurate frequency analysis.
    """

    # --- Constants & Regex (Compiled once for performance) ---
    
    # 1. URLs and Emails -> <LINK>
    PAT_LINK = re.compile(r'(?i)\b(?:https?://|www\.)\S+\b|\b[\w\.-]+@[\w\.-]+\.\w+\b')

    # 2. Dates (ISO, US, EU, Text formats) -> <DATE>
    PAT_DATE = re.compile(
        r'(?i)\b(?:\d{1,4}[-./]\d{1,2}[-./]\d{2,4}|'  # Numeric: 2023-10-10, 10/10/23
        r'\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{2,4})\b' # Text: 12 Oct 2023
    )

    # 3. Time -> <TIME>
    PAT_TIME = re.compile(r'\d{1,2}:\d{2}(?::\d{2})?\s*(?:am|pm)?', re.IGNORECASE)

    # 4. Page Numbers (Specific "Page X of Y" formats) -> <PAGE>
    # Matches: "Page 1", "Pg 1", "Page 1 of 10"
    PAT_PAGE_TEXT = re.compile(r'(?i)\b(?:page|pg|p\.?)\s*\d+(?:\s*(?:of|/)\s*\d+)?\b')

    # 5. Generic Pagination "X of Y" -> <PAGINATION>
    # Matches: "1 of 10", "1/50" (isolated)
    PAT_PAGINATION = re.compile(r'\b\d+\s*(?:of|/)\s*\d+\b')

    # 6. Money / Currency -> <MONEY>
    PAT_MONEY = re.compile(r'[$€£]\s?\d+(?:,\d{3})*(?:\.\d+)?')

    # 7. Remaining Generic Numbers -> <NUM>
    # Catches versions (v1.0), years (2023), isolated numbers
    PAT_NUM = re.compile(r'\d+')

    # 8. Visual Separators (Lines, Bars) -> Removed or replaced with space
    PAT_SEPARATORS = re.compile(r'\s*(?:_|-|\*|=){3,}\s*')

    # Pipeline: Order matters! Specific -> Generic
    CLEANING_PIPELINE = [
        (PAT_LINK, ' <LINK> '),
        (PAT_DATE, ' <DATE> '),
        (PAT_TIME, ' <TIME> '),
        (PAT_PAGE_TEXT, ' <PAGE> '),
        (PAT_PAGINATION, ' <PAGINATION> '),
        (PAT_MONEY, ' <MONEY> '),
        (PAT_NUM, ' <NUM> '),
        (PAT_SEPARATORS, ' '), 
    ]

    def __init__(self, file_path: str, tables_y_coords: Dict[int, List[float]] = None):
        self.file_path = file_path
        self.tables_y_coords = tables_y_coords if tables_y_coords else {}
        
        # Results
        self.headers: List[str] = []
        self.footers: List[str] = []
        
        # We store the "signature" (masked text) separately for debugging/analysis
        self.frequency_signatures_headers: List[str] = []
        self.frequency_signatures_footers: List[str] = []
        
        self.number_of_pages: int = 0
        
        # Final Coordinate Map: {page_index: [header_bbox, footer_bbox]}
        self.page_wise_coords: Dict[int, List[Any]] = {}

    # --- Helper Methods ---

    def get_frequency_signature(self, text: str) -> str:
        """
        Transforms raw text into a structural signature for frequency counting.
        Ex: "Report 2023 - Page 1" -> "report <NUM> - <PAGE>"
        """
        if not text: 
            return ""
        
        # 1. Normalize whitespace first
        clean = text.strip()
        
        # 2. Apply Tokenization Pipeline
        for pattern, replacement in self.CLEANING_PIPELINE:
            clean = pattern.sub(replacement, clean)
            
        # 3. Final cleanup
        # Lowercase for case-insensitive matching
        clean = clean.lower()
        # Collapse multiple spaces
        clean = re.sub(r'\s+', ' ', clean).strip()
        
        return clean

    def get_most_common(self, data: List[str], n: int = 2) -> List[Tuple[str, int]]:
        """Efficiently gets top N most common signatures excluding empty strings."""
        valid_items = [x for x in data if x]
        return Counter(valid_items).most_common(n)

    # --- Main Extraction Logic ---

    def extract_headers_footers(self):
        """
        Extracts headers/footers by identifying top/bottom text blocks and 
        comparing their 'frequency signatures' across the document.
        """
        # Data storage: {page_index: {'top': {...}, 'top+1': {...}, ...}}
        page_data = {} 
        
        # Frequency Candidates (Store the *Signatures* here, not raw text)
        candidates = {
            'top': [], 'top+1': [],
            'bot': [], 'bot-1': []
        }

        try:
            doc = fitz.open(self.file_path)
            self.number_of_pages = len(doc)
            
            for page_idx in range(self.number_of_pages):
                page = doc[page_idx]
                blocks = page.get_text("blocks")
                
                # Filter: remove empty blocks and non-text
                valid_blocks = []
                for b in blocks:
                    text = b[4].strip()
                    if text:
                        valid_blocks.append(b)

                if not valid_blocks:
                    page_data[page_idx] = {}
                    self._fill_empty_candidates(candidates)
                    continue

                # --- 1. Identify Candidates (Top 2 and Bottom 2) ---
                
                # Sort by y0 (Top)
                by_top = sorted(valid_blocks, key=lambda b: b[1])
                
                # Check Table Overlap logic
                table_range = self.tables_y_coords.get(page_idx)
                
                top_blk = by_top[0]
                top_plus_1_blk = by_top[1] if len(by_top) > 1 else None
                
                # If top block starts AFTER a table starts, it's body text.
                if table_range and top_blk[1] > table_range[0]:
                    top_blk = None
                    top_plus_1_blk = None
                
                # Sort by y1 descending (Bottom)
                by_bot = sorted(valid_blocks, key=lambda b: b[3], reverse=True)
                bot_blk = by_bot[0]
                bot_minus_1_blk = by_bot[1] if len(by_bot) > 1 else None
                
                # --- 2. Process Blocks & Generate Signatures ---
                
                p_store = {}
                
                def process_block(key, block):
                    if block:
                        raw_text = block[4].strip().replace('\n', ' ')
                        # Create signature (e.g., "page <NUM>")
                        sig = self.get_frequency_signature(raw_text)
                        
                        candidates[key].append(sig)
                        p_store[key] = {
                            'text': raw_text, 
                            'signature': sig, 
                            'bbox': list(block[:4])
                        }
                    else:
                        candidates[key].append('')
                        p_store[key] = None

                process_block('top', top_blk)
                process_block('top+1', top_plus_1_blk)
                process_block('bot', bot_blk)
                process_block('bot-1', bot_minus_1_blk)
                
                page_data[page_idx] = p_store

            # --- 3. Frequency Analysis (on Signatures) ---
            
            def get_freq_count(key):
                # Returns the count of the most common signature for this position
                common = self.get_most_common(candidates[key], 1)
                if not common: return 0, ""
                return common[0][1], common[0][0] # count, signature_text

            top_count, top_sig = get_freq_count('top')
            top_p1_count, top_p1_sig = get_freq_count('top+1')
            
            bot_count, bot_sig = get_freq_count('bot')
            bot_m1_count, bot_m1_sig = get_freq_count('bot-1')

            # --- 4. Logic to Choose Header/Footer Lines ---
            
            # HEADER SELECTION
            # Default to top line
            header_source = 'top'
            
            # Logic: If line 2 is also very frequent (likely a Title under a Date), prefer it?
            # Or if Line 1 is just "<PAGE>" and Line 2 is "Annual Report <NUM>", we might want Line 2 
            # or BOTH (logic below assumes picking one block).
            
            # If 'top+1' is present often (>50% pages) and 'top' is also present
            if top_p1_count > (self.number_of_pages * 0.5):
                # If top+1 is almost as frequent as top (within 15%), it might be the main header
                if top_count > 0:
                    diff = abs(top_count - top_p1_count)
                    ratio = diff / max(top_count, top_p1_count)
                    if ratio <= 0.15:
                        header_source = 'top+1'

            # FOOTER SELECTION
            footer_source = 'bot'
            
            # If bot-1 is frequent
            if bot_m1_count > (self.number_of_pages * 0.5):
                if bot_count > 0:
                    diff = abs(bot_count - bot_m1_count)
                    ratio = diff / max(bot_count, bot_m1_count)
                    if ratio <= 0.15:
                        footer_source = 'bot-1'
            
            # Fallback for Footer: If bottom line is unique (freq=1) but bot-1 is consistent
            if bot_count < (self.number_of_pages * 0.1) and bot_m1_count > (self.number_of_pages * 0.7):
                footer_source = 'bot-1'

            # --- 5. Compile Final Results ---
            for i in range(self.number_of_pages):
                data = page_data.get(i, {})
                
                # HEADER
                h_obj = data.get(header_source)
                # Only accept if the signature matches the "winner" signature
                # (Optional: Or just take whatever is in that slot for the page)
                if h_obj:
                    self.headers.append(h_obj['text'])
                    self.frequency_signatures_headers.append(h_obj['signature'])
                    h_bbox = h_obj['bbox']
                else:
                    self.headers.append('')
                    self.frequency_signatures_headers.append('')
                    h_bbox = []

                # FOOTER
                f_obj = data.get(footer_source)
                if f_obj:
                    self.footers.append(f_obj['text'])
                    self.frequency_signatures_footers.append(f_obj['signature'])
                    f_bbox = f_obj['bbox']
                else:
                    self.footers.append('')
                    self.frequency_signatures_footers.append('')
                    f_bbox = []

                self.page_wise_coords[i] = [
                    h_bbox if h_bbox else [], 
                    f_bbox if f_bbox else []
                ]
            
            return self.headers, self.footers, self.page_wise_coords

        except Exception as e:
            print(f"Error extracting headers/footers: {e}")
            return [], [], {}

    def _fill_empty_candidates(self, candidates_dict):
        for k in candidates_dict:
            candidates_dict[k].append('')
