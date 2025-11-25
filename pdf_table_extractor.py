import os
import math
import logging
import multiprocessing
from typing import List, Dict, Any, Tuple, Optional
import time

import fitz  # pymupdf
import pandas as pd

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [PID %(process)d] - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Type alias for the result structure
TableData = List[List[Any]]
PageResult = Dict[str, Any]

def extract_tables_from_page_chunk(
    pdf_path: str, 
    page_indices: List[int], 
    min_confidence: int = 50
) -> List[PageResult]:
    """
    Worker function to process a specific subset of pages.
    
    Args:
        pdf_path: Path to the PDF file.
        page_indices: List of page numbers (0-based) to process.
        min_confidence: Parsing configuration (placeholder for advanced logic).

    Returns:
        A list of dictionaries containing table data for the assigned pages.
    """
    results = []
    
    try:
        # Open a local instance of the document for this process
        doc = fitz.open(pdf_path)
    except Exception as e:
        logger.error(f"Failed to open PDF at {pdf_path}: {e}")
        return []

    for page_num in page_indices:
        try:
            page = doc.load_page(page_num)
            
            # PyMuPDF's built-in table finder
            # You can tune vertical_strategy and horizontal_strategy here if needed
            tabs = page.find_tables()
            
            if tabs.tables:
                logger.info(f"Found {len(tabs.tables)} tables on page {page_num + 1}")
                
                for i, table in enumerate(tabs):
                    # Extract raw data (list of lists)
                    raw_data = table.extract()
                    
                    # Convert to DataFrame for cleaner handling (optional)
                    # We treat the first row as headers if it looks like text
                    df = None
                    if raw_data:
                        try:
                            df = pd.DataFrame(raw_data[1:], columns=raw_data[0])
                        except Exception:
                            # Fallback if columns mismatch
                            df = pd.DataFrame(raw_data)

                    results.append({
                        "page_number": page_num + 1,
                        "table_index": i,
                        "bbox": table.bbox,
                        "data_raw": raw_data,
                        "dataframe": df
                    })
        except Exception as e:
            logger.error(f"Error processing page {page_num}: {e}")
            continue

    doc.close()
    return results

def distribute_workload(total_pages: int, num_workers: int) -> List[List[int]]:
    """
    Splits the total pages into even chunks for the workers.
    """
    chunk_size = math.ceil(total_pages / num_workers)
    chunks = []
    for i in range(0, total_pages, chunk_size):
        # Create a range of page indices
        end = min(i + chunk_size, total_pages)
        chunks.append(list(range(i, end)))
    return chunks

def parse_pdf_parallel(pdf_path: str, num_processes: Optional[int] = None) -> List[PageResult]:
    """
    Main entry point to parse PDF tables in parallel.
    """
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")

    # 1. Analyze Document Structure
    try:
        doc = fitz.open(pdf_path)
        total_pages = doc.page_count
        doc.close()
    except Exception as e:
        logger.critical(f"Could not read file metadata: {e}")
        return []

    if total_pages == 0:
        logger.warning("PDF has no pages.")
        return []

    # 2. Determine Concurrency
    if num_processes is None:
        # Leave one core free for system/main process
        num_processes = max(1, multiprocessing.cpu_count() - 1)
    
    # Don't spawn more processes than pages
    num_processes = min(num_processes, total_pages)
    
    logger.info(f"Starting extraction on '{pdf_path}' ({total_pages} pages) using {num_processes} cores.")

    # 3. Prepare Chunks
    page_chunks = distribute_workload(total_pages, num_processes)
    
    # Prepare arguments for starmap: [(pdf_path, chunk1), (pdf_path, chunk2), ...]
    # We fix the config (min_confidence) here
    tasks = [(pdf_path, chunk) for chunk in page_chunks]

    # 4. Execute Parallel Processing
    t0 = time.time()
    results_flat = []
    
    with multiprocessing.Pool(processes=num_processes) as pool:
        # starmap unpacks the tuple arguments for the target function
        chunk_results = pool.starmap(extract_tables_from_page_chunk, tasks)
        
        # Flatten the list of lists returned by workers
        for res in chunk_results:
            results_flat.extend(res)

    duration = time.time() - t0
    logger.info(f"Extraction complete. Processed {total_pages} pages in {duration:.2f}s.")
    logger.info(f"Total tables detected: {len(results_flat)}")

    return results_flat

if __name__ == "__main__":
    # Example Usage
    # Create a dummy PDF or point to an existing one
    TARGET_PDF = "sample_financial_report.pdf" 
    
    # For demonstration, let's verify if file exists, otherwise warn user
    if os.path.exists(TARGET_PDF):
        tables = parse_pdf_parallel(TARGET_PDF)
        
        # Example: Print the first detected table
        if tables:
            print("\n--- Sample Output (First Table Detected) ---")
            first_table = tables[0]
            print(f"Page: {first_table['page_number']}")
            print(f"Bounding Box: {first_table['bbox']}")
            
            if first_table['dataframe'] is not None:
                print("\nData (Pandas):")
                print(first_table['dataframe'].head())
            else:
                print("\nData (Raw):")
                print(first_table['data_raw'][:2]) # Print first 2 rows
    else:
        print(f"Please ensure '{TARGET_PDF}' exists to run the demo.")
        # Create a dummy file for testing logic if you don't have one
        doc = fitz.open()
        page = doc.new_page()
        # Draw a simple grid to simulate a table
        shape = page.new_shape()
        shape.draw_rect(fitz.Rect(50, 50, 300, 150))
        shape.draw_line((50, 100), (300, 100)) # Row line
        shape.draw_line((150, 50), (150, 150)) # Col line
        shape.finish(color=(0, 0, 0), width=1)
        page.insert_text((60, 90), "Header 1")
        page.insert_text((160, 90), "Header 2")
        page.insert_text((60, 140), "Value 1")
        page.insert_text((160, 140), "Value 2")
        doc.save("sample_financial_report.pdf")
        print("Created dummy PDF. Please run script again.")