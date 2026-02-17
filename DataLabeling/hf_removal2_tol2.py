# --- 1. Identify Candidates (Top 2 and Bottom 2) ---

                # Sort by y0 (Top)
                by_top = sorted(valid_blocks, key=lambda b: b[1])

                # Check Table Overlap logic
                table_range = self.tables_y_coords.get(page_idx)

                top_blk = by_top[0]
                top_plus_1_blk = by_top[1] if len(by_top) > 1 else None

                if table_range:
                    table_start_y = table_range[0]
                    
                    # LOGIC FIX 1: Check the FIRST block
                    # If the bottom of the text (b[3]) is below the table start, it's inside the table.
                    if top_blk and top_blk[3] > table_start_y:
                        top_blk = None
                        top_plus_1_blk = None
                    
                    # LOGIC FIX 2: Check the SECOND block independently
                    # This is the step missing in your previous attempts.
                    # Even if 'MEDICAL' (top) is valid, 'COMPARING COVERAGE' (top+1) might be in the table.
                    elif top_plus_1_blk and top_plus_1_blk[3] > table_start_y:
                        top_plus_1_blk = None

                # Sort by y1 descending (Bottom)
                by_bot = sorted(valid_blocks, key=lambda b: b[3], reverse=True)
                # ... (rest of the code remains the same)