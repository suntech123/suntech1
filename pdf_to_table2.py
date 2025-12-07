def parse_page_to_data_rows(filename: str, page_num: int, 
                            lines: List[TextLine], font_map: Dict[str, FontSpec]) -> List[Dict]:
    """
    Advanced State Machine handling:
    1. Multi-line Headers (Merging H1 split across lines).
    2. Buffered Body Text (Merging paragraphs).
    3. Hierarchical Context (H1 -> H2 -> Text).
    """
    
    # 1. Determine Roles
    role_map = determine_font_roles(font_map, lines)
    
    # 2. State & Buffers
    context = HeaderContext(filename, page_num)
    
    body_buffer = []      # Accumulates body text
    header_buffer = []    # Accumulates multi-line header text
    active_header_role = None # Tracks if we are currently reading 'h1', 'h2', etc.
    
    rows = []

    # --- HELPER FUNCTIONS ---
    def commit_body():
        """Writes accumulated body text to a row using CURRENT headers."""
        if not body_buffer: return
        full_text = " ".join(body_buffer)
        rows.append(context.to_dict(full_text))
        body_buffer.clear()

    def commit_header():
        """Updates the Context with the accumulated header text."""
        if not active_header_role or not header_buffer: return
        
        full_header_text = " ".join(header_buffer)
        
        # Update the state machine (e.g., Set H1 = "Certificate of Coverage")
        context.update_header(active_header_role, full_header_text)
        
        # Reset header accumulators
        header_buffer.clear()
        # Note: We do NOT reset active_header_role here; we reset it when logic switches to body

    # --- MAIN LOOP ---
    for i, line in enumerate(lines):
        first_frag = line.fragments[0]
        fid = first_frag.font_id
        text_content = line.get_text_content()
        
        # Determine current line's role
        curr_role = role_map.get(fid, 'body')
        
        # CHECK: Are we continuing the SAME header? (e.g. H1 -> H1)
        if active_header_role and curr_role == active_header_role:
            header_buffer.append(text_content)
            continue # Skip to next line, keep accumulating header
            
        # CHECK: Did we just finish a header? (e.g. H1 -> Body or H1 -> H2)
        if active_header_role and curr_role != active_header_role:
            commit_header() # Save the H1 we were building
            active_header_role = None # We are no longer building that specific header
            
        # NOW: Handle the new role
        if curr_role in ['h1', 'h2', 'h3']:
            # We encountered a NEW header (e.g. Body -> H1, or H1 -> H2)
            
            # 1. If we have leftover body text from the previous section, save it now.
            commit_body()
            
            # 2. Start building the new header
            active_header_role = curr_role
            header_buffer.append(text_content)
            
        else:
            # We are in BODY text
            
            # Check for Paragraph Breaks (Vertical Gap)
            if i > 0 and body_buffer:
                prev_line = lines[i-1]
                gap = line.top - prev_line.bottom
                font_size = font_map[fid].size if fid in font_map else 12
                
                # Heuristic: Gap > 60% of font size = New Paragraph
                if gap > (font_size * 0.6):
                    commit_body() # Write the previous paragraph
            
            body_buffer.append(text_content)

    # --- FINAL FLUSH ---
    # We reached end of page.
    # 1. Did we end on a header line? (Rare, but possible)
    if active_header_role:
        commit_header()
        
    # 2. Did we have body text pending?
    commit_body()
    
    return rows