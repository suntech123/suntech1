def calculate_vertical_merge_tolerance(lines: List[TextLine]) -> float:
    """
    Dynamically calculates how much vertical gap is allowed to consider 
    two lines as part of the same sentence/header.
    Based on the statistical mode of gaps on the page.
    """
    if len(lines) < 2: 
        return 5.0 # Default fallback
        
    # 1. Collect all gaps between adjacent lines
    gaps = []
    for i in range(1, len(lines)):
        gap = lines[i].top - lines[i-1].bottom
        # Filter: ignore negative overlaps or huge distinct section jumps (>50px)
        if 0 <= gap < 50:
            gaps.append(gap)
            
    if not gaps: 
        return 5.0

    # 2. Find the "Standard Line Spacing" (Mode)
    try:
        dom_gap = statistics.mode(gaps)
    except:
        dom_gap = statistics.median(gaps)

    # 3. Calculate Tolerance (Mode + small buffer)
    # If the page is consistent (low stdev), keep tolerance tight.
    if len(gaps) > 1:
        stdev = statistics.stdev(gaps)
        # We allow the standard gap + half a standard deviation
        return dom_gap + (0.5 * stdev)
    
    return dom_gap + 2.0



def parse_page_to_data_rows(lines: List[TextLine], 
                            font_map: Dict[str, FontSpec], 
                            role_map: Dict[str, Union[int, str]], 
                            context: HeaderContext) -> List[Dict]:

    if not lines: return []

    # === DYNAMIC CALCULATION ===
    # Calculate the threshold for this specific page using the helper above
    vertical_merge_limit = calculate_vertical_merge_tolerance(lines)
    
    # Calculate approx page width to detect if a line ended early (for TOC logic)
    page_right_edge = max(l.fragments[-1].right for l in lines) if lines else 0

    body_buffer = []
    header_buffer = []
    active_header_role: Optional[int] = None 
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
        # If a header existed but had no body text, force a write
        nonlocal header_has_body_content
        if active_header_role is not None and not header_has_body_content:
            rows.append(context.to_dict("")) 
            header_has_body_content = True 

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')
        
        # Calculate context from previous line
        prev_line = lines[i-1] if i > 0 else None
        gap = (line.top - prev_line.bottom) if prev_line else 0
        current_font_size = font_map[fid].size if fid in font_map else 10

        # === 1. HEADER LOGIC ===
        if isinstance(role, int):
            
            # A. Check Role Continuity
            is_same_role = (active_header_role is not None and role == active_header_role)
            
            # B. Check Vertical Proximity (Using Dynamic Tolerance)
            is_tight_gap = gap <= vertical_merge_limit

            # C. Check "Line Fill" (CRITICAL FOR TOC)
            # If the previous line ended far from the right edge (> 20% whitespace),
            # it implies the previous line was complete. The current line is likely a NEW item.
            # Exception: If the previous line ended with a hyphen '-', it IS a wrap.
            prev_line_ended_early = False
            if prev_line:
                # 80px buffer or 15% of page width
                if prev_line.fragments[-1].right < (page_right_edge - 80):
                    prev_text = prev_line.fragments[-1].text
                    if not prev_text.endswith('-'):
                        prev_line_ended_early = True

            # DECISION: Merge only if Same Role + Tight Gap + Previous line flowed to end
            if is_same_role and is_tight_gap and not prev_line_ended_early:
                header_buffer.append(text)
                continue

            # --- New Header Detected ---
            if active_header_role is not None:
                commit_header()
            
            commit_body()
            commit_orphan_header() # Handles TOC items with no body text

            active_header_role = role
            header_buffer.append(text)
            header_has_body_content = False 

        # === 2. BODY LOGIC ===
        else:
            if active_header_role is not None:
                commit_header()
                # Do not clear active_header_role; body belongs to it

            # Paragraph detection using dynamic limit * 1.5 (paragraphs have wider gaps)
            if i > 0 and body_buffer:
                if gap > (vertical_merge_limit * 1.5): 
                    commit_body()

            body_buffer.append(text)

    # === End of Page Cleanup ===
    if active_header_role is not None:
        commit_header()
    
    commit_body()
    commit_orphan_header()

    return rows