import fitz  # PyMuPDF
import pandas as pd
from typing import List, Dict, Union, Optional
import os

class PDFTableExtractor:
    def __init__(self, pdf_path: str):
        """
        Initialize the extractor with a file path.
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"The file {pdf_path} was not found.")
        
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def detect_and_extract(self, 
                           pages: Optional[List[int]] = None, 
                           min_confidence: int = 1) -> List[Dict]:
        """
        Detects tables and extracts them as Pandas DataFrames.
        
        Args:
            pages: List of page numbers to scan (0-indexed). If None, scans all.
            min_confidence: Minimum number of cells to consider it a valid table (default 1).
            
        Returns:
            A list of dictionaries containing metadata and the dataframe.
        """
        extracted_tables = []
        
        # If no specific pages requested, look at all of them
        if pages is None:
            pages = range(len(self.doc))

        for page_num in pages:
            try:
                page = self.doc[page_num]
                
                # Native PyMuPDF table finder
                # vertical_strategy='lines' looks for graphic lines separating columns
                # vertical_strategy='text' looks for whitespace alignment
                tabs = page.find_tables(vertical_strategy='lines_strict', horizontal_strategy='lines_strict')
                
                # Fallback: If strict lines fail, try a hybrid approach (text alignment)
                if not tabs.tables:
                    tabs = page.find_tables()

                for i, table in enumerate(tabs):
                    # Extract content as a list of lists
                    # to_pandas() is a helper method in newer PyMuPDF versions
                    df = table.to_pandas()
                    
                    if df.shape[0] < min_confidence:
                        continue

                    table_data = {
                        "page": page_num + 1,
                        "table_index": i + 1,
                        "bbox": table.bbox,  # (x0, y0, x1, y1)
                        "dataframe": df,
                        "row_count": len(df),
                        "col_count": len(df.columns)
                    }
                    extracted_tables.append(table_data)
                    
            except IndexError:
                print(f"Warning: Page {page_num} does not exist.")
                continue

        return extracted_tables

    def generate_visual_debug(self, output_path: str):
        """
        Draws bounding boxes around detected tables and saves a new PDF.
        Useful for verifying if the logic is detecting the right areas.
        """
        debug_doc = fitz.open(self.pdf_path)
        
        for page in debug_doc:
            tabs = page.find_tables()
            for tab in tabs:
                # Draw a red rectangle around the table
                page.draw_rect(tab.bbox, color=(1, 0, 0), width=1.5)
                
                # Draw distinct lines for rows/cols (optional visual aid)
                for cell in tab.header.cells:
                    page.draw_rect(cell, color=(0, 0, 1), width=0.5)
                for row in tab.rows:
                    for cell in row.cells:
                        page.draw_rect(cell, color=(0, 1, 0), width=0.5)

        debug_doc.save(output_path)
        print(f"Debug PDF saved to: {output_path}")

    def close(self):
        self.doc.close()

# --- Usage Example ---
if __name__ == "__main__":
    # Create a dummy PDF or point to an existing one
    input_pdf = "invoice_example.pdf" 
    
    # (Optional) logic to create a dummy PDF for testing if file doesn't exist
    if not os.path.exists(input_pdf):
        print(f"Please provide a valid PDF path. '{input_pdf}' not found.")
    else:
        extractor = PDFTableExtractor(input_pdf)
        
        # 1. Extract Data
        results = extractor.detect_and_extract()
        
        for res in results:
            print(f"--- Found Table on Page {res['page']} ---")
            print(f"Bounding Box: {res['bbox']}")
            print(res['dataframe'].head()) # Print first few rows
            print("\n")

        # 2. Create Visual Debug File
        extractor.generate_visual_debug("debug_output.pdf")
        
        extractor.close()