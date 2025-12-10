# main.py
import argparse
import logging
import pandas as pd
from pathlib import Path
from dataclasses import asdict

from extractor import PDFExtractor
from parser import HierarchyParser
import config

# --- Logging Configuration ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_single_pdf(input_path: Path, output_path: Path):
    """Orchestrates the pipeline for one file."""
    logger.info(f"Starting processing for: {input_path.name}")
    
    # 1. Init Modules
    extractor = PDFExtractor(str(input_path))
    parser = HierarchyParser()

    # 2. Run Pipeline
    try:
        # Stream lines one by one into the parser (Memory Efficient)
        for raw_line in extractor.extract_lines():
            parser.process_line(raw_line)
        
        # 3. Get Results
        structured_data = parser.finalize()
        
        # 4. Export using Pandas
        # Convert List[ParsedSection] -> List[Dict]
        data_dicts = [asdict(record) for record in structured_data]
        df = pd.DataFrame(data_dicts)
        
        # Reorder columns for readability
        df = df[["header_l1", "header_l2", "header_l3", "body_text", "page_number"]]
        
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        logger.info(f"Successfully saved to {output_path}")

    except Exception as e:
        logger.error(f"Pipeline failed for {input_path.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Expert PDF to Hierarchical CSV Parser")
    parser.add_argument("--filename", type=str, help="Specific file name in input_pdfs folder")
    args = parser.parse_args()

    if args.filename:
        # Process specific file
        in_file = config.INPUT_FOLDER / args.filename
        out_file = config.OUTPUT_FOLDER / f"{in_file.stem}.csv"
        if in_file.exists():
            process_single_pdf(in_file, out_file)
        else:
            logger.error(f"File not found: {in_file}")
    else:
        # Process all PDFs in input folder
        pdf_files = list(config.INPUT_FOLDER.glob("*.pdf"))
        if not pdf_files:
            logger.warning(f"No PDF files found in {config.INPUT_FOLDER}")
            return

        for pdf_file in pdf_files:
            out_file = config.OUTPUT_FOLDER / f"{pdf_file.stem}.csv"
            process_single_pdf(pdf_file, out_file)

if __name__ == "__main__":
    main()