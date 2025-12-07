def parse_lines_to_table(filename: str, 
                         page_num: int, 
                         lines: List[TextLine], 
                         font_map: Dict[str, FontSpec]) -> List[Dict]:
    
    # 1. Determine Roles (H1, H2, Body)
    role_map = determine_font_roles(font_map, lines)
    
    # 2. Initialize State
    context = HeaderContext(filename, page_num)
    text_buffer = [] # Accumulates body text lines
    rows = []

    def flush_buffer():
        """Helper to write the accumulated text to a row."""
        if not text_buffer:
            return
        
        # Join lines with space (or newline if you prefer)
        full_text = " ".join(text_buffer)
        
        # Create the row using the CURRENT header context
        rows.append(context.to_dict(full_text))
        
        # Clear the buffer
        text_buffer.clear()

    # 3. Iterate Lines
    for i, line in enumerate(lines):
        first_frag = line.fragments[0]
        fid = first_frag.font_id
        text_content = line.get_text_content()
        
        # Get role (default to body)
        role = role_map.get(fid, 'body')

        if role in ['h1', 'h2', 'h3']:
            # --- HEADER DETECTED ---
            
            # 1. CRITICAL: Save any previous body text BEFORE changing headers
            flush_buffer()
            
            # 2. Update the Header Context
            context.update_header(role, text_content)
            
        else:
            # --- BODY TEXT DETECTED ---
            
            # Check for Paragraph Break (Vertical Gap Logic)
            # If this line is far below the previous line, flush the previous paragraph first
            if i > 0:
                prev_line = lines[i-1]
                gap = line.top - prev_line.bottom
                
                # Get font size for heuristic (e.g., gap > 50% of font size)
                current_font_size = font_map.get(fid).size if fid in font_map else 10
                
                if gap > (current_font_size * 0.6):
                    flush_buffer()

            # Add current line to buffer
            text_buffer.append(text_content)

    # 4. Final Flush (Don't forget the text at the bottom of the page!)
    flush_buffer()
    
    return rows