import pandas as pd
import glob
import logging
from typing import List, Dict, Any, Callable
from pathlib import Path

# Setup logging for production-grade tracking
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

class TSVAnalyzer:
    """
    Analyzes a collection of TSV files based on pluggable validation rules.
    """
    def __init__(self, file_pattern: str = "*.tsv"):
        self.file_paths = glob.glob(file_pattern)
        self.results = []
        
        if not self.file_paths:
            logging.warning(f"No files matching '{file_pattern}' were found.")

    def run_analysis(self, rules: List[Callable[[pd.DataFrame], Dict[str, Any]]]):
        """
        Iterates through files and applies a list of analysis functions.
        """
        for file_path in self.file_paths:
            try:
                # Reading with 'sep=\t' as per your TSV requirement
                df = pd.read_csv(file_path, sep='\t')
                
                # Start file summary with the filename
                file_summary = {"filename": Path(file_path).name}
                
                # Apply each modular rule
                for rule in rules:
                    file_summary.update(rule(df))
                
                self.results.append(file_summary)
                logging.info(f"Successfully analyzed: {file_path}")
                
            except Exception as e:
                logging.error(f"Error processing {file_path}: {e}")

    def get_report(self) -> pd.DataFrame:
        """Returns the final results as a structured DataFrame."""
        return pd.DataFrame(self.results)

# --- Modular Rules (Extend these easily) ---

def analyze_category_field(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Rule: Calculates unique count and null count for the 'Category' column.
    """
    col = 'Category'
    if col in df.columns:
        return {
            "category_unique_count": df[col].nunique(),
            "category_null_count": int(df[col].isna().sum())
        }
    return {"category_unique_count": "Missing Col", "category_null_count": "Missing Col"}

def check_empty_file(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Example of an additional rule: Checks if the file has any data rows.
    """
    return {"total_rows": len(df)}

# --- Execution ---

if __name__ == "__main__":
    # Initialize analyzer
    analyzer = TSVAnalyzer(file_pattern="*.tsv")
    
    # Define which rules to apply (Add more functions to this list as needed)
    active_rules = [analyze_category_field, check_empty_file]
    
    # Run and display
    analyzer.run_analysis(rules=active_rules)
    report = analyzer.get_report()
    
    if not report.empty:
        print("\n--- TSV Analysis Report ---")
        print(report.to_string(index=False))