# ... inside the loop ...

                # Sort by y0 (Top)
                by_top = sorted(valid_blocks, key=lambda b: b[1])

                # Check Table Overlap logic
                table_range = self.tables_y_coords.get(page_idx)

                top_blk = by_top[0]
                top_plus_1_blk = by_top[1] if len(by_top) > 1 else None

                # --- FIX STARTS HERE ---
                if table_range:
                    table_start_y = table_range[0]
                    # Tolerance for coordinate mismatches (e.g., 5 pixels)
                    tolerance = 5.0 
                    
                    # 1. Check top_blk
                    # If the text starts roughly at or below the table start
                    if top_blk and top_blk[1] >= (table_start_y - tolerance):
                        top_blk = None
                        # If the first block is in the table, the second almost certainly is too
                        top_plus_1_blk = None
                    
                    # 2. Safety Check for top_plus_1 (Edge Case)
                    # If top_blk was valid (e.g. a real header), but top_plus_1 is actually the table start
                    elif top_plus_1_blk and top_plus_1_blk[1] >= (table_start_y - tolerance):
                        top_plus_1_blk = None
                # --- FIX ENDS HERE ---

                # Sort by y1 descending (Bottom)
                # ... rest of code