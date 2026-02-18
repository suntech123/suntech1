def get_block_details(self, block_dict):
    """
    Extracts text, average font size, and bold status from a dictionary block.
    """
    text_content = []
    sizes = []
    is_bold = False
    
    # Iterate through lines and spans
    for line in block_dict.get("lines", []):
        for span in line.get("spans", []):
            text_content.append(span["text"])
            sizes.append(span["size"])
            
            # Check for bold:
            # 1. PyMuPDF 'flags': bit 4 (16) usually indicates bold
            # 2. Font name: sometimes contains 'Bold' or 'Medi'
            if (span["flags"] & 16) or ("bold" in span["font"].lower()):
                is_bold = True

    full_text = " ".join(text_content).strip()
    
    # Calculate representative size (Max or Average)
    # Using Max is usually safer for Headers as they might have mixed content
    avg_size = round(max(sizes), 2) if sizes else 0.0

    return full_text, avg_size, is_bold





#### here

# ... inside extract_headers_footers ...

doc = fitz.open(self.file_path)
self.number_of_pages = len(doc)

for page_idx in range(self.number_of_pages):
    page = doc[page_idx]
    
    # CHANGE 1: Use "dict" instead of "blocks"
    # This returns a dictionary containing a list of blocks
    page_dict = page.get_text("dict")
    raw_blocks = page_dict.get("blocks", [])

    valid_blocks = []
    
    for b in raw_blocks:
        # Filter for text blocks only (type 0 = text, 1 = image)
        if b.get("type") == 0:
            # Use the helper method to extract details
            text, size, is_bold = self.get_block_details(b)
            
            if text.strip():
                # We extend the block dictionary with our parsed data
                # Structure: [x0, y0, x1, y1, text, size, is_bold]
                bbox = b["bbox"]
                valid_blocks.append({
                    "bbox": bbox,
                    "text": text,
                    "size": size,
                    "is_bold": is_bold,
                    "y0": bbox[1], # for sorting
                    "y1": bbox[3]  # for sorting
                })

    if not valid_blocks:
        page_data[page_idx] = {}
        self._fill_empty_candidates(candidates)
        continue

    # --- 1. Identify Candidates (Top 2 and Bottom 2) ---

    # Sort by y0 (Top)
    by_top = sorted(valid_blocks, key=lambda x: x["y0"])

    # Check Table Overlap logic
    table_range = self.tables_y_coords.get(page_idx)

    top_blk = by_top[0]
    top_plus_1_blk = by_top[1] if len(by_top) > 1 else None

    # Sort by y1 descending (Bottom)
    by_bot = sorted(valid_blocks, key=lambda x: x["y1"], reverse=True)
    bot_blk = by_bot[0]
    bot_minus_1_blk = by_bot[1] if len(by_bot) > 1 else None

    # --- 2. Process Blocks & Generate Signatures ---
    
    def process_block(key, block_obj):
        if block_obj:
            raw_text = block_obj["text"].strip().replace('\n', ' ')
            sig = self.get_frequency_signature(raw_text)
            
            # NOW YOU HAVE FONT INFO HERE
            font_size = block_obj["size"]
            is_bold = block_obj["is_bold"]

            # You can now use these variables to filter logic
            # Example: Only count as header if size > 10
            
            candidates[key].append(sig)
            # Store data...
            # ...