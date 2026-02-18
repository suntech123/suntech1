def get_block_details(self, block_dict):
    """
    Extracts text, average font size, and bold status from a dictionary block.
    """
    text_content = []
    sizes = []
    is_bold = False
    
    # Iterate through lines and spans
    for line in block_dict.get("lines", []):
        for span in line.get("spans", []):
            text_content.append(span["text"])
            sizes.append(span["size"])
            
            # Check for bold:
            # 1. PyMuPDF 'flags': bit 4 (16) usually indicates bold
            # 2. Font name: sometimes contains 'Bold' or 'Medi'
            if (span["flags"] & 16) or ("bold" in span["font"].lower()):
                is_bold = True

    full_text = " ".join(text_content).strip()
    
    # Calculate representative size (Max or Average)
    # Using Max is usually safer for Headers as they might have mixed content
    avg_size = round(max(sizes), 2) if sizes else 0.0

    return full_text, avg_size, is_bold