# extractor.py
import pdfplumber
from typing import Iterator, Dict, Any
from models import RawLine
import logging

# Setup logger
logger = logging.getLogger(__name__)

class PDFExtractor:
    def __init__(self, file_path: str):
        self.file_path = file_path

    def extract_lines(self) -> Iterator[RawLine]:
        """
        Generates a stream of RawLine objects from the PDF.
        Using a generator (yield) is memory efficient for large PDFs.
        """
        try:
            with pdfplumber.open(self.file_path) as pdf:
                for page_idx, page in enumerate(pdf.pages):
                    # extract_words allows us to see font info. 
                    # extract_text is simpler but loses font metadata.
                    # We group words into lines generally based on 'top' position.
                    words = page.extract_words(keep_blank_chars=True, use_text_flow=True)
                    
                    # Logic to group words into lines would go here.
                    # For simplicity, pdfplumber's 'extract_text' works well for text, 
                    # but for expert hierarchy, we iterate page.chars or rely on 'dict' extraction.
                    
                    # NOTE: This is a simplified extraction logic for demonstration. 
                    # In a real deep-dive, we analyze individual characters.
                    # Here we simulate line extraction based on standard layout.
                    
                    # Extracting raw dictionaries which contain 'fontname' and 'size'
                    lines = page.extract_text_lines()
                    
                    for line in lines:
                        # Extract the most common font size in this line to determine style
                        # 'chars' contains individual character metadata
                        if not line['chars']:
                            continue
                            
                        first_char = line['chars'][0]
                        
                        yield RawLine(
                            text=line['text'],
                            font_name=first_char.get('fontname', 'Unknown'),
                            font_size=float(first_char.get('size', 0)),
                            is_bold="Bold" in first_char.get('fontname', ''),
                            page_number=page_idx + 1
                        )
                        
        except Exception as e:
            logger.error(f"Failed to process PDF {self.file_path}: {e}")
            raise