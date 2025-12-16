from typing import List, Dict, Union, Optional

def parse_page_to_data_rows(lines: List[TextLine], 
                            font_map: Dict[str, FontSpec], 
                            role_map: Dict[str, Union[int, str]], 
                            context: HeaderContext) -> List[Dict]:

    header_buffer = []
    
    # active_header_role is an Integer (or None)
    active_header_role: Optional[int] = None 

    rows = []

    def commit_and_flush_header():
        """
        Updates the context with the accumulated header text and immediately 
        creates a row with empty body text.
        """
        if active_header_role is not None and header_buffer:
            full_header_text = " ".join(header_buffer)
            
            # 1. Update the context state so it knows the current header hierarchy
            context.update_header(active_header_role, full_header_text)
            
            # 2. Create a row immediately. Passing "" ensures no body text is included.
            rows.append(context.to_dict(""))
            
            # 3. Clear the buffer
            header_buffer.clear()

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')

        # === BODY LOGIC ===
        # If the role is not an integer (i.e., it is 'body'), we simply ignore it.
        # We do not reset the header buffer because body text might appear 
        # visually between header lines (rare, but possible in bad layouts), 
        # or we just want to skip over it to find the next header.
        if not isinstance(role, int):
            continue

        # === HEADER LOGIC ===
        
        # Calculate gap to detect if this is a multi-line header
        prev_bottom = lines[i-1].bottom if i > 0 else 0
        gap = line.top - prev_bottom
        current_font_size = font_map[fid].size if fid in font_map else 10

        # Check if this is a CONTINUATION of the same header (Multiline title)
        # OR a NEW header of the same level (Table of Contents item)
        is_same_role = (active_header_role is not None and role == active_header_role)

        # Visual continuation logic:
        # If gap is small (< 1.5x font size), treat as continuation of the same header line.
        is_visual_continuation = gap < (current_font_size * 1.5)

        if is_same_role and is_visual_continuation:
            header_buffer.append(text)
            continue

        # --- New Header Detected ---
        
        # 1. Commit the *previous* header we were building (if any)
        commit_and_flush_header()

        # 2. Start tracking the NEW header
        active_header_role = role
        header_buffer.append(text)

    # === End of Page Cleanup ===
    # Commit the final header sitting in the buffer
    commit_and_flush_header()

    return rows