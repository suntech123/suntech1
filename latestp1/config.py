# config.py
from pathlib import Path

# --- File Paths ---
BASE_DIR = Path(__file__).parent
INPUT_FOLDER = BASE_DIR / "input_pdfs"
OUTPUT_FOLDER = BASE_DIR / "output_csvs"

# Ensure directories exist
INPUT_FOLDER.mkdir(exist_ok=True)
OUTPUT_FOLDER.mkdir(exist_ok=True)

# --- Parsing Logic ---
# Heuristics to determine if a line is a header based on font size.
# Adjust these based on your specific PDF document styles.
HEADER_1_MIN_SIZE = 18.0
HEADER_2_MIN_SIZE = 14.0
HEADER_3_MIN_SIZE = 11.0

# Tolerance for vertical grouping (lines close together are same paragraph)
Y_TOLERANCE = 3