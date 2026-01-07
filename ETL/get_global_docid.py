import re
from pathlib import Path
from typing import Union

# Context: Assuming your regex constant is defined globally like in your image
# If not, uncomment the line below:
# UUID_REGEX_CANONICAL = r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

def extract_global_doc_id_from_filename(file_path: Union[str, Path]) -> str:
    """
    Extracts the Global Document ID (UUID) from a filename using the canonical regex.

    Args:
        file_path (Union[str, Path]): The full file path or filename string.

    Returns:
        str: The extracted UUID.

    Raises:
        ValueError: If no valid UUID is found in the filename.
    """
    # 1. Safely extract just the filename (handles /path/to/file.csv)
    filename = Path(file_path).name

    # 2. Search for the pattern
    match = re.search(UUID_REGEX_CANONICAL, filename, flags=re.IGNORECASE)

    # 3. Handle Missing ID (Guard Clause)
    if not match:
        raise ValueError(
            f"Global Document ID not found in filename: '{filename}'.\n"
            f"Expected pattern: {UUID_REGEX_CANONICAL}"
        )

    # 4. Return the match
    return match.group(0)