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
    Analyzes TSV files in a specific directory and exports results.
    """
    def __init__(self, directory_name: str = "tsvs"):
        self.directory = Path(directory_name)
        self.results = []
        
        # Validate directory existence
        if not self.directory.is_dir():
            logging.error(f"Directory '{directory_name}' not found. Please ensure it exists.")
            self.file_paths = []
        else:
            self.file_paths = list(self.directory.glob("*.tsv"))
            logging.info(f"Found {len(self.file_paths)} files in '{self.directory}'")

    def run_analysis(self, rules: List[Callable[[pd.DataFrame], Dict[str, Any]]]):
        """
        Applies logic rules to each file and handles encoding fallbacks.
        """
        for file_path in self.file_paths:
            try:
                # FIX: Handle UnicodeDecodeError by trying fallback encoding
                try:
                    df = pd.read_csv(file_path, sep='\t', encoding='utf-8')
                except UnicodeDecodeError:
                    logging.warning(f"UTF-8 failed for {file_path.name}. Retrying with ISO-8859-1...")
                    df = pd.read_csv(file_path, sep='\t', encoding='iso-8859-1')

                # Basic Metadata
                file_summary = {"filename": file_path.name}
                
                # Apply each modular rule
                for rule in rules:
                    file_summary.update(rule(df))
                
                self.results.append(file_summary)
                
            except Exception as e:
                logging.error(f"Failed to process {file_path.name}: {e}")

    def get_report(self) -> pd.DataFrame:
        """Returns the accumulated analysis as a DataFrame."""
        return pd.DataFrame(self.results)

# --- Pluggable Rules (Extendable) ---

def analyze_category_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Rule to check unique counts and nulls in the Category column."""
    target_col = 'Category'
    if target_col in df.columns:
        return {
            "category_unique": df[target_col].nunique(),
            "category_nulls": int(df[target_col].isna().sum())
        }
    return {"category_unique": "Not Found", "category_nulls": "Not Found"}

def analyze_row_counts(df: pd.DataFrame) -> Dict[str, Any]:
    """Rule to provide total row count for the file."""
    return {"total_rows": len(df)}

# --- Main Execution ---

if __name__ == "__main__":
    # 1. Initialize - specify your directory here (e.g., "tsvs")
    # Make sure this folder exists in your project directory
    analyzer = TSVAnalyzer(directory_name="tsvs")
    
    # 2. Define the rules to apply
    active_rules = [analyze_category_stats, analyze_row_counts]
    
    # 3. Run the processing engine
    analyzer.run_analysis(rules=active_rules)
    
    # 4. Generate and Handle Report
    report_df = analyzer.get_report()
    
    if not report_df.empty:
        # A. Print to console
        print("\n" + "="*40)
        print("TSV ANALYSIS REPORT")
        print("="*40)
        print(report_df.to_string(index=False))
        
        # B. Export to CSV
        output_csv = "final_analysis_report.csv"
        report_df.to_csv(output_csv, index=False)
        print(f"\n[Success] Report saved to: {output_csv}")
    else:
        print("\n[Warning] No data was processed. Check if the directory contains .tsv files.")