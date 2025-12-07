@dataclass
class HeaderContext:
    filename: str
    page_num: int
    h1: Optional[str] = None
    h2: Optional[str] = None
    h3: Optional[str] = None

    def update_page_num(self, new_page_num: int):
        """Updates page number but KEEPS the active headers."""
        self.page_num = new_page_num

    def update_header(self, level: str, text: str):
        if level == 'h1': self.h1, self.h2, self.h3 = text, None, None
        elif level == 'h2': self.h2, self.h3 = text, None
        elif level == 'h3': self.h3 = text

    def to_dict(self, body_text: str) -> Dict:
        return {
            "Filename": self.filename, 
            "PageNo": self.page_num,
            "Header1": self.h1, 
            "Header2": self.h2, 
            "Header3": self.h3,
            "Text": body_text
        }


def parse_page_to_data_rows(lines: List[TextLine], 
                            font_map: Dict[str, FontSpec],
                            context: HeaderContext) -> List[Dict]: # <--- Pass context in
    """
    Processes a single page using a PERSISTENT context.
    """
    role_map = determine_font_roles(font_map, lines)
    
    body_buffer = []
    header_buffer = []
    active_header_role = None
    rows = []

    def commit_body():
        if body_buffer:
            # This writes a row using the CURRENT PageNo and CURRENT Headers
            # inherited from previous pages if none were found here yet.
            rows.append(context.to_dict(" ".join(body_buffer)))
            body_buffer.clear()

    def commit_header():
        if active_header_role and header_buffer:
            context.update_header(active_header_role, " ".join(header_buffer))
            header_buffer.clear()

    for i, line in enumerate(lines):
        fid = line.fragments[0].font_id
        text = line.get_text_content()
        role = role_map.get(fid, 'body')

        # 1. Continue same header (rare but possible across lines)
        if active_header_role and role == active_header_role:
            header_buffer.append(text)
            continue
            
        # 2. End previous header
        if active_header_role and role != active_header_role:
            commit_header()
            active_header_role = None
            
        # 3. New Header start
        if role in ['h1', 'h2', 'h3']:
            commit_body() 
            active_header_role = role
            header_buffer.append(text)
        
        # 4. Body Text
        else:
            # Paragraph Check
            if i > 0 and body_buffer:
                prev_line = lines[i-1]
                gap = line.top - prev_line.bottom
                f_size = font_map[fid].size if fid in font_map else 12
                if gap > (f_size * 0.6):
                    commit_body()
            body_buffer.append(text)

    # End of page cleanup
    if active_header_role: commit_header()
    commit_body()
    
    # NOTE: We do NOT reset context.h1/h2 here. They persist to the next function call.
    return rows


def main(xml_path: str, output_path: str):
    # ... (Loading XML and FontMap code same as before) ...
    root = ET.parse(xml_path).getroot() # ...
    # ...
    
    # --- CRITICAL CHANGE ---
    # Initialize Context ONCE before the loop
    filename = os.path.basename(xml_path)
    # Start at page 0, will update immediately
    persistent_context = HeaderContext(filename, 0) 
    
    all_rows = []
    pages = root.findall('page')
    
    for i, page in enumerate(pages):
        current_page_num = i + 1
        
        # 1. Update the Page Number in the persistent context
        persistent_context.update_page_num(current_page_num)
        
        # 2. Extract Lines
        lines = extract_text_lines(page)
        
        # 3. Process Logic (Passing the existing context)
        # If Page 2 starts with body text, it will use the H1/H2 
        # left over from the end of Page 1 processing.
        page_rows = parse_page_to_data_rows(lines, fmap, persistent_context)
        
        all_rows.extend(page_rows)