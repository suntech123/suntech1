# Sort by y0 (Top)
                by_top = sorted(valid_blocks, key=lambda b: b[1])

                # Check Table Overlap logic
                table_range = self.tables_y_coords.get(page_idx)

                top_blk = by_top[0]
                top_plus_1_blk = by_top[1] if len(by_top) > 1 else None

                if table_range:
                    table_start_y = table_range[0]
                    # Tolerance (e.g. 5 points) to handle slight misalignments
                    tolerance = 5.0 

                    # CHECK 1: Is the FIRST block inside the table?
                    # We check if the Top (y0) is below the buffer 
                    # OR if the Bottom (y1) penetrates the table start
                    if top_blk and (top_blk[1] > (table_start_y - tolerance) or top_blk[3] > table_start_y):
                        top_blk = None
                        top_plus_1_blk = None # If top is table, everything below is table
                    
                    # CHECK 2: Is the SECOND block inside the table? (THIS WAS MISSING)
                    # This catches cases like: "Header Title" (Valid) -> "Table Row 1" (Invalid)
                    elif top_plus_1_blk and (top_plus_1_blk[1] > (table_start_y - tolerance) or top_plus_1_blk[3] > table_start_y):
                        top_plus_1_blk = None