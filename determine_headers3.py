def process_pdf_spillover(header_dict, content_dict):
    # Sort pages to ensure sequential processing
    sorted_pages = sorted(content_dict.keys())
    
    final_output = {}
    
    # State variable: The header currently "in effect"
    # Initialize with a default in case Page 1 has text before the first header
    current_active_header = "__PREAMBLE__" 

    for page_num in sorted_pages:
        full_text = content_dict[page_num]
        headers = header_dict.get(page_num, [])
        
        # Initialize current page dictionary
        final_output[page_num] = {}
        
        current_idx = 0
        
        # --- SCENARIO 1: Page has NO headers ---
        if not headers:
            # The entire page belongs to the header active from the previous page
            if full_text.strip():
                final_output[page_num][current_active_header] = full_text.strip()
            continue

        # --- SCENARIO 2: Page HAS headers ---
        for i, header in enumerate(headers):
            # Find start of this header (searching only after the previous cursor)
            start_pos = full_text.find(header, current_idx)
            
            if start_pos == -1:
                # Warning: Header in list but not found in text
                continue
            
            # Extract the text segment BEFORE this header starts
            segment_text = full_text[current_idx:start_pos].strip()
            
            if segment_text:
                if i == 0:
                    # This is the "Spillover" text (Start of page -> First Header)
                    # It belongs to the header carried over from the PREVIOUS page
                    final_output[page_num][current_active_header] = segment_text
                else:
                    # This is text between two headers on the SAME page
                    # It belongs to the previous header in this loop
                    prev_header_in_loop = headers[i-1]
                    final_output[page_num][prev_header_in_loop] = segment_text
            
            # Update state: The current header is now active for upcoming text
            # But we don't assign text to it yet; we wait for the next iteration or the tail
            current_active_header = header
            
            # Move cursor past this header
            current_idx = start_pos + len(header)
            
        # --- Handle text AFTER the last header on this page ---
        tail_text = full_text[current_idx:].strip()
        
        if tail_text:
            # This text belongs to the last header we processed on this page
            final_output[page_num][current_active_header] = tail_text

    return final_output

# ==========================================
# Example Usage to Demonstrate Spanning
# ==========================================

# Headers: Note Page 2 and 3 handling
headers_map = {
    1: ["Introduction", "Methodology"],
    2: ["Results"],     # Page 2 has a header halfway through
    3: [],              # Page 3 has NO headers (pure continuation of Results)
    4: ["Conclusion"]
}

# Content:
# - Methodology (Pg1) spills into Pg2 top.
# - Results (Pg2) spills into Pg3 completely.
# - Results (Pg3) spills into Pg4 top.
content_map = {
    1: "Doc Start\nIntroduction\nIntro body.\nMethodology\nMeth body part 1...",
    2: "...Meth body part 2 (on pg2).\nResults\nResults body start.",
    3: "Results body continued entirely on page 3.",
    4: "Results body final part.\nConclusion\nFinal thoughts."
}

result = process_pdf_spillover(headers_map, content_map)

# Print nicely
import json
print(json.dumps(result, indent=4))