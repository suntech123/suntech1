def get_adi_results_optimized(file_path: str):
    d = get_form_recognizer_read_result(file_path, "prebuilt-layout")
    
    page_numbers_y_coords = {}
    tables_y_coords = {}
    INCH_TO_POINT = 72

    # 1. Page Numbers (Same as above)
    for p in d.get('paragraphs', []):
        if p.get('role') == 'pageNumber':
            region = p['boundingRegions'][0]
            # Use slicing [1::2] to get every 2nd element starting at index 1 (the Ys)
            page_numbers_y_coords[region['pageNumber']] = min(region['polygon'][1::2]) * INCH_TO_POINT

    # 2. Tables (Direct Bounding Box Access)
    for table in d.get('tables', []):
        # Most modern Azure results provide the bounding region for the whole table
        if 'boundingRegions' in table:
            for region in table['boundingRegions']:
                page_num = region['pageNumber']
                y_coords = region['polygon'][1::2]
                
                t_min = min(y_coords) * INCH_TO_POINT
                t_max = max(y_coords) * INCH_TO_POINT
                
                if page_num in tables_y_coords:
                    # Expand existing box to include this new table
                    tables_y_coords[page_num][0] = min(tables_y_coords[page_num][0], t_min)
                    tables_y_coords[page_num][1] = max(tables_y_coords[page_num][1], t_max)
                else:
                    tables_y_coords[page_num] = [t_min, t_max]
        
        # Fallback: If 'boundingRegions' is missing on the table object, use the cell logic here
        else:
            # Insert the cell iteration logic from Approach A here
            pass

    return page_numbers_y_coords, tables_y_coords


import fitz  # PyMuPDF
import re
import heapq
from collections import Counter
from typing import List, Dict, Tuple, Optional, Any

class PDFHeaderFooterExtractor:
    """
    Optimized class to extract headers, footers, and their positions from PDFs.
    """

    # --- Constants & Regex (Compiled once for performance) ---
    INCH_TO_POINT = 72
    
    # Pattern to identify Page Numbers (Roman, standard, "Page X of Y")
    PAGE_NUM_PATTERN = re.compile(
        r'(?:^\d+(?:/\d+)?\s*$)|(?:^\s*[\d+]\s*$)|(?:^\s*\d+\s*$)|(?:^\s*-\s*\d+\s*-\s*$)',
        re.IGNORECASE
    )
    
    # Cleaning patterns (removing numbers, dates, special chars to find common text)
    # 1. Start: numbers/dates
    PAT_START = re.compile(r'^\d+(?:/\d+)?\s*') 
    # 2. Middle: numbers surrounded by spaces
    PAT_MID = re.compile(r'\s+\d+(?:/\d+)?\s+') 
    # 3. Brackets: [123]
    PAT_BRACKET = re.compile(r'\s*\[\d+\]')
    # 4. End: numbers
    PAT_END = re.compile(r'\s*\d+\s*$')
    # 5. Dash patterns: - 12 -
    PAT_DASH = re.compile(r'\s*-\s*\d+\s*-\s*$')

    def __init__(self, file_path: str, tables_y_coords: Dict[int, List[float]] = None):
        self.file_path = file_path
        # Expecting tables_y_coords as {page_index: [min_y, max_y]}
        self.tables_y_coords = tables_y_coords if tables_y_coords else {}
        
        # Results
        self.headers: List[str] = []
        self.footers: List[str] = []
        self.cleaned_headers: List[str] = []
        self.cleaned_footers: List[str] = []
        self.number_of_pages: int = 0
        
        # Final Coordinate Map: {page_index: [header_bbox, footer_bbox]}
        self.page_wise_coords: Dict[int, List[Any]] = {}

    # --- Helper Methods ---

    def clean_text(self, text: str) -> str:
        """Removes page numbers and variable digits to normalize text for frequency analysis."""
        if not text: return ""
        text = self.PAT_START.sub('', text)
        text = self.PAT_BRACKET.sub('', text)
        text = self.PAT_END.sub('', text)
        text = self.PAT_DASH.sub('', text)
        return text.strip().replace('\n', ' ')

    @staticmethod
    def get_most_common(data: List[str], n: int = 2) -> List[Tuple[str, int]]:
        """Efficiently gets top N most common elements excluding empty strings."""
        # Filter empty strings before counting to save processing
        valid_items = [x for x in data if x]
        return Counter(valid_items).most_common(n)

    # --- Main Extraction Logic ---

    def extract_headers_footers(self):
        """
        Main driver function. Opens PDF, extracts blocks, analyzes frequencies, 
        and maps final coordinates.
        """
        # Temporary storage for analysis
        # Structure: {page_index: {'top': block, 'top+1': block, 'bot': block, 'bot-1': block}}
        page_data = {} 
        
        # Lists for frequency counting
        candidates = {
            'top': [], 'top+1': [],
            'bot': [], 'bot-1': []
        }

        try:
            doc = fitz.open(self.file_path)
            self.number_of_pages = len(doc)
            
            for page_idx in range(self.number_of_pages):
                page = doc[page_idx]
                # get_text("blocks") returns: (x0, y0, x1, y1, "text", block_no, block_type)
                blocks = page.get_text("blocks")
                
                # Filter: remove empty blocks and non-text
                # Also clean internal newlines for consistency
                valid_blocks = []
                for b in blocks:
                    text = b[4].strip()
                    if text:
                        valid_blocks.append(b)

                if not valid_blocks:
                    # Handle empty page
                    page_data[page_idx] = {}
                    self._fill_empty_candidates(candidates)
                    continue

                # --- 1. Identify Candidates (Optimization: use nsmallest/nlargest) ---
                # Sort by y0 (top)
                # We only need the top 2 and bottom 2, no need to sort the whole list if N is large.
                # However, for typical PDFs (N < 100 blocks), sorted() is extremely fast.
                by_top = sorted(valid_blocks, key=lambda b: b[1])
                
                # Check Table Overlap logic
                # If the top block starts AFTER a table starts, it's likely body text, not header.
                table_range = self.tables_y_coords.get(page_idx)
                
                top_blk = by_top[0]
                top_plus_1_blk = by_top[1] if len(by_top) > 1 else None
                
                # Table overlap check (Top)
                if table_range and top_blk[1] > table_range[0]:
                    # The 'top' block is actually below the table start -> Invalid Header
                    top_blk = None
                    top_plus_1_blk = None
                
                # Bottom blocks (Sort by y1 descending)
                by_bot = sorted(valid_blocks, key=lambda b: b[3], reverse=True)
                bot_blk = by_bot[0]
                bot_minus_1_blk = by_bot[1] if len(by_bot) > 1 else None
                
                # Table overlap check (Bottom) - if bottom block ends BEFORE table ends? 
                # (Logic usually checks if footer is inside table, but we'll stick to basic existence)

                # --- 2. Store Raw & Cleaned Text ---
                # We store the cleaned version for frequency analysis, 
                # but keep the block (with coords) for final extraction.
                
                p_store = {}
                
                if top_blk:
                    c_text = self.clean_text(top_blk[4])
                    candidates['top'].append(c_text)
                    p_store['top'] = {'text': top_blk[4], 'clean': c_text, 'bbox': top_blk[:4]}
                else:
                    candidates['top'].append('')

                if top_plus_1_blk:
                    c_text = self.clean_text(top_plus_1_blk[4])
                    candidates['top+1'].append(c_text)
                    p_store['top+1'] = {'text': top_plus_1_blk[4], 'clean': c_text, 'bbox': top_plus_1_blk[:4]}
                else:
                    candidates['top+1'].append('')

                if bot_blk:
                    c_text = self.clean_text(bot_blk[4])
                    candidates['bot'].append(c_text)
                    p_store['bot'] = {'text': bot_blk[4], 'clean': c_text, 'bbox': bot_blk[:4]}
                else:
                    candidates['bot'].append('')

                if bot_minus_1_blk:
                    c_text = self.clean_text(bot_minus_1_blk[4])
                    candidates['bot-1'].append(c_text)
                    p_store['bot-1'] = {'text': bot_minus_1_blk[4], 'clean': c_text, 'bbox': bot_minus_1_blk[:4]}
                else:
                    candidates['bot-1'].append('')
                
                page_data[page_idx] = p_store

            # --- 3. Frequency Analysis & Winner Selection ---
            
            # Helper to get max freq
            def get_freq(key):
                common = self.get_most_common(candidates[key], 1)
                return common[0][1] if common else 0

            top_freq = get_freq('top')
            top_p1_freq = get_freq('top+1')
            bot_freq = get_freq('bot')
            bot_m1_freq = get_freq('bot-1')

            # --- Header Logic ---
            # Default: use 'top'
            header_source = 'top'
            
            # Logic from Image 9: 
            # If Top+1 is frequent and difference between Top and Top+1 freq is small (<=15%), 
            # prefer Top+1 (often the real title below a changing date/page num).
            if top_freq > 0 and top_p1_freq > 0:
                diff = abs(top_freq - top_p1_freq)
                ratio = diff / max(top_freq, top_p1_freq) # Using max as base for safety
                if ratio <= 0.15:
                    header_source = 'top+1'
            
            # --- Footer Logic ---
            footer_source = 'bot'
            if bot_freq > 0 and bot_m1_freq > 0:
                diff = abs(bot_freq - bot_m1_freq)
                ratio = diff / max(bot_freq, bot_m1_freq)
                if ratio <= 0.15:
                    footer_source = 'bot-1'
            
            # Edge case (Image 2): if footer_max_val == 0 and bottom_minus_1 != 0...
            if bot_freq == 0 and bot_m1_freq > 0:
                # Check consistency ratio
                if (bot_m1_freq / self.number_of_pages) > 0.7:
                    footer_source = 'bot-1'

            # --- 4. Final Construction ---
            for i in range(self.number_of_pages):
                data = page_data.get(i, {})
                
                # Retrieve Header
                h_data = data.get(header_source)
                if h_data:
                    self.headers.append(h_data['text'])
                    self.cleaned_headers.append(h_data['clean'])
                    h_bbox = h_data['bbox']
                else:
                    self.headers.append('')
                    self.cleaned_headers.append('')
                    h_bbox = []

                # Retrieve Footer
                f_data = data.get(footer_source)
                if f_data:
                    self.footers.append(f_data['text'])
                    self.cleaned_footers.append(f_data['clean'])
                    f_bbox = f_data['bbox']
                    
                    # Image 5 Logic: Adjust footer bbox for redaction/visuals?
                    # "rect.y0 + 15" implies expanding or shifting the box. 
                    # We store the raw block bbox here. 
                    # If specific modification is needed:
                    if f_bbox:
                         # Example adjustment based on Image 5
                         f_bbox = list(f_bbox) # make mutable
                         # f_bbox[1] += 15 # y0
                         # f_bbox[3] += 15 # y1
                else:
                    self.footers.append('')
                    self.cleaned_footers.append('')
                    f_bbox = []

                # Store result
                # Format from Image 2: [header_rect, footer_rect]
                # If missing, store empty string or list
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

# Usage Example
# extractor = PDFHeaderFooterExtractor("doc.pdf")
# headers, footers, coords = extractor.extract_headers_footers()