import shutil
import hashlib
from pathlib import Path
from typing import Set, Dict, List

import hashlib
import uuid
from pathlib import Path

def get_hash(file_path: Path | str) -> str:
    """
    Generates a deterministic UUID-like string from file content.
    Reads in chunks to ensure memory efficiency with large files.
    """
    # 1. Use MD5 to match your original logic (128-bit hash)
    hasher = hashlib.md5()
    
    # 2. Open file as binary
    with open(file_path, 'rb') as f:
        # 3. Read in 4KB chunks using iter() - "The Pythonic Loop"
        # This prevents crashing RAM on large files
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
            
    # 4. The Magic Trick:
    # MD5 is 128-bit. UUIDs are 128-bit. 
    # Instead of manual string slicing, just let the UUID class format it.
    return str(uuid.UUID(hex=hasher.hexdigest()))

def get_uuid() -> str:
    """
    Generates a random standard UUID string.
    """
    return str(uuid.uuid4())

def clean_pdf_file_names(
    pdf_dir: Path, 
    cleaned_dir: Path, 
    existing_hashes: Set[str]
) -> Dict[str, str]:
    """
    Cleans PDF filenames, deduplicates based on content hash, and copies to new dir.
    """
    
    # 1. Use Pathlib for robust file finding (case-insensitive)
    # This replaces the glob.glob string concatenation
    pdf_paths = sorted([
        p for p in pdf_dir.iterdir() 
        if p.is_file() and p.suffix.lower() == '.pdf'
    ])

    if not pdf_paths:
        print(f'No PDFs found at {pdf_dir}')
        return {}

    # 2. Reset Output Directory safely
    if cleaned_dir.exists():
        shutil.rmtree(cleaned_dir)
    cleaned_dir.mkdir(parents=True, exist_ok=True)

    print(f'Cleaning PDF file names and copying to {cleaned_dir}')
    
    new_file_hashes: Dict[str, str] = {}

    for pdf_path in pdf_paths:
        try:
            # 3. Optimize Hash Generation
            file_hash = get_file_hash(pdf_path)

            # 4. O(1) Lookup: Checking a set is instant vs O(N) for a list
            if file_hash in existing_hashes:
                print(f'Skipping duplicate: {pdf_path.name}')
                continue

            # Standardize Name (assuming logic similar to your original helper)
            # using .stem to get filename without extension
            clean_name = pdf_path.stem.strip().replace(" ", "_") 
            standardized_name = f"{clean_name}.pdf"
            
            target_path = cleaned_dir / standardized_name
            
            # Handle potential filename collisions in the new folder
            counter = 1
            while target_path.exists():
                target_path = cleaned_dir / f"{clean_name}_{counter}.pdf"
                counter += 1

            # 5. Copy2 preserves metadata (creation times, etc.)
            shutil.copy2(pdf_path, target_path)

            # Update records
            new_file_hashes[target_path.stem] = file_hash
            existing_hashes.add(file_hash)

        except Exception as e:
            print(f"Error processing {pdf_path}: {e}")

    return new_file_hashes

# Usage Example
if __name__ == "__main__":
    src = Path("./data_files")
    dst = Path("./data_files/cleaned_pdfs")
    
    # Using a Set for 'seen_hashes' is crucial for performance
    global_hashes = set() 
    
    results = clean_pdf_file_names(src, dst, global_hashes)