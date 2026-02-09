import pandas as pd
import logging
from typing import List, Dict, Any, Callable
from pathlib import Path

# --- Configuration & Logging ---
logging.basicConfig(
    level=logging.INFO, 
    format='%(levelname)s: %(message)s'
)

class TSVAnalyzer:
    """
    Analyzes large batches of TSV files and saves reports to a designated directory.
    """
    def __init__(self, input_dir: str = "tsvs", output_dir: str = "report"):
        self.input_path = Path(input_dir)
        self.output_path = Path(output_dir)
        self.results = []
        
        # Create output directory if it doesn't exist
        self.output_path.mkdir(parents=True, exist_ok=True)
        
        if not self.input_path.is_dir():
            logging.error(f"Input directory '{input_dir}' not found.")
            self.file_paths = []
        else:
            self.file_paths = list(self.input_path.glob("*.tsv"))
            logging.info(f"Found {len(self.file_paths)} files in '{input_dir}'")

    def run_analysis(self, rules: List[Callable[[pd.DataFrame], Dict[str, Any]]]):
        """
        Processes files with encoding fallback to prevent UnicodeDecodeError.
        """
        for file_path in self.file_paths:
            try:
                # Attempt to read with UTF-8, fallback to ISO-8859-1 for special characters
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
                except UnicodeDecodeError:
                    # Fix for the 0xd0 byte error seen in your logs
                    df = pd.read_csv(file_path, sep='\t', encoding='iso-8859-1')

                file_summary = {"filename": file_path.name}
                
                for rule in rules:
                    file_summary.update(rule(df))
                
                self.results.append(file_summary)
                
            except Exception as e:
                logging.error(f"Failed to process {file_path.name}: {e}")

    def save_report(self, filename: str = "analysis_summary.csv"):
        """Saves the final report to the 'report' directory and prints a preview."""
        if not self.results:
            logging.warning("No analysis results to save.")
            return

        report_df = pd.DataFrame(self.results)
        output_file = self.output_path / filename
        
        # Save to CSV
        report_df.to_csv(output_file, index=False)
        logging.info(f"Full report for {len(self.results)} files saved to: {output_file}")
        
        # Print preview
        print("\n" + "="*30)
        print("ANALYSIS SUMMARY PREVIEW")
        print("="*30)
        print(report_df.head(10).to_string(index=False)) # Show first 10 for brevity
        print(f"\n... and {max(0, len(report_df)-10)} more rows in the CSV.")

# --- Modular Analysis Rules ---

def get_category_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates unique values and nulls for the Category column."""
    col = 'Category'
    if col in df.columns:
        return {
            "unique_categories": df[col].nunique(),
            "null_categories": int(df[col].isna().sum())
        }
    return {"unique_categories": 0, "null_categories": "N/A"}

# --- Execution ---

if __name__ == "__main__":
    # Initialize with your specific folder structure
    analyzer = TSVAnalyzer(input_dir="tsvs", output_dir="report")
    
    # Run analysis
    analyzer.run_analysis(rules=[get_category_metrics])
    
    # Save results to 'report/analysis_summary.csv'
    analyzer.save_report()