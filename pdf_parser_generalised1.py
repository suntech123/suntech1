def parse_page_to_data_rows(lines: List[TextLine], 
                            font_map: Dict[str, FontSpec], 
                            role_map: Dict[str, Union[int, str]], 
                            context: HeaderContext) -> List[Dict]:

    body_buffer = []
    header_buffer = []

    # active_header_role is now an Integer (or None)
    active_header_role: Optional[int] = None 
    
    # Flag to track if the current header has been associated with body text
    header_has_body_content = False

    rows = []

    def commit_body():
        nonlocal header_has_body_content
        if body_buffer:
            rows.append(context.to_dict(" ".join(body_buffer)))
            body_buffer.clear()
            header_has_body_content = True

    def commit_header():
        if active_header_role is not None and header_buffer:
            context.update_header(active_header_role, " ".join(header_buffer))
            header_buffer.clear()

    def commit_orphan_header():
        """
        If a header finishes and no body text followed it, 
        we create a row with empty text to ensure the header appears in output.
        """
        nonlocal header_has_body_content
        if active_header_role is not None and not header_has_body_content:
            rows.append(context.to_dict("")) # Empty body text
            header_has_body_content = True # Mark handled to prevent duplicate

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')
        
        # Calculate gap from previous line to detect visual breaks
        prev_bottom = lines[i-1].bottom if i > 0 else 0
        gap = line.top - prev_bottom
        current_font_size = font_map[fid].size if fid in font_map else 10

        # === 1. HEADER LOGIC ===
        if isinstance(role, int):

            # Check if this is a CONTINUATION of the same header (Multiline title)
            # OR a NEW header of the same level (Table of Contents item)
            is_same_role = (active_header_role is not None and role == active_header_role)
            
            # If gap is small (< 1.5x font size), treat as continuation. 
            # If gap is large, treat as new header even if font is same (TOC logic).
            is_visual_continuation = gap < (current_font_size * 1.5)

            if is_same_role and is_visual_continuation:
                header_buffer.append(text)
                continue

            # --- New Header Detected (Start of new section or TOC item) ---
            
            # 1. Commit the Header we were just building
            if active_header_role is not None:
                commit_header()
                
            # 2. Commit any body text from previous section
            commit_body()
            
            # 3. CRITICAL FIX: If previous header had NO body, write it as its own row
            commit_orphan_header()

            # 4. Start tracking NEW header
            active_header_role = role
            header_buffer.append(text)
            header_has_body_content = False # Reset for this new header

        # === 2. BODY LOGIC ===
        else:
            # If we were reading a header, commit it now
            if active_header_role is not None:
                commit_header()
                # Do NOT clear active_header_role yet; it stays valid for this body block

            # Paragraph detection (split rows on large gaps in body too)
            if i > 0 and body_buffer:
                if gap > (current_font_size * 0.8): 
                    commit_body()

            body_buffer.append(text)

    # === End of Page Cleanup ===
    if active_header_role is not None:
        commit_header()
    
    commit_body() # Commit pending body
    commit_orphan_header() # Catch the last header if it was a TOC item

    return rows