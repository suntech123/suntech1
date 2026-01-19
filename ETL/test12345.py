import re
import os

def parse_table_log(log_data):
    # 1. Extract Filename
    # Looking for pattern: "Analyzing X pages in: path/to/filename.pdf"
    filename_pattern = r"Analyzing \d+ pages in: (.+\.pdf)"
    filename_match = re.search(filename_pattern, log_data)
    
    clean_filename = "Unknown File"
    if filename_match:
        full_path = filename_match.group(1)
        # Extract just the filename from the path
        base_name = os.path.basename(full_path)
        # Remove the extension
        clean_filename = os.path.splitext(base_name)[0]

    print(f"Filename without extension: {clean_filename}")
    print("-" * 50)
    print("Matching Table Detections (H >= 2, V <= 3):")

    # 2. Extract Lines and Filter
    # Looking for pattern: "[+] Table detected on Page X (H-lines: Y, V-lines: Z)"
    lines = log_data.split('\n')
    
    # Regex breakdown:
    # \[+\]      -> Matches literal "[+]"
    # .*Page (\d+) -> Matches text up to Page and captures the page number
    # H-lines: (\d+) -> Captures H-lines count
    # V-lines: (\d+) -> Captures V-lines count
    line_pattern = r"\[\+\] Table detected on Page (\d+) \(H-lines: (\d+), V-lines: (\d+)\)"

    found_matches = False
    
    for line in lines:
        match = re.search(line_pattern, line)
        if match:
            # Extract numbers (converted to integers)
            page_num = int(match.group(1))
            h_lines = int(match.group(2))
            v_lines = int(match.group(3))

            # Apply Logic: H-lines >= 2 and V-lines <= 3
            if h_lines >= 2 and v_lines <= 3:
                print(line.strip())
                found_matches = True

    if not found_matches:
        print("No tables found matching criteria.")

# ==========================================
# INPUT DATA (Transcribed from your image)
# ==========================================
log_content = """
Analyzing 175 pages in: data_files/cleaned_pdfs/2021 CORE SPD W 2024 WELL CARE ABC SCHEDULE OF BENEFITS AND 2024 SMMS_bd4ddaf6-c2a7-4dff-9ab1-f586471cd485.pdf ...
[-] No table on Page 1 (H-lines: 0, V-lines: 0)
[-] No table on Page 2 (H-lines: 0, V-lines: 0)
[-] No table on Page 3 (H-lines: 0, V-lines: 0)
[-] No table on Page 4 (H-lines: 0, V-lines: 0)
[-] No table on Page 5 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 6 (H-lines: 6, V-lines: 3)
[-] No table on Page 7 (H-lines: 0, V-lines: 0)
[-] No table on Page 8 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 9 (H-lines: 12, V-lines: 3)
[-] No table on Page 10 (H-lines: 0, V-lines: 0)
[-] No table on Page 11 (H-lines: 0, V-lines: 0)
[-] No table on Page 12 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 13 (H-lines: 9, V-lines: 6)
[+] Table detected on Page 14 (H-lines: 12, V-lines: 3)
[-] No table on Page 15 (H-lines: 0, V-lines: 0)
[-] No table on Page 16 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 17 (H-lines: 7, V-lines: 4)
[-] No table on Page 18 (H-lines: 0, V-lines: 0)
[-] No table on Page 19 (H-lines: 0, V-lines: 0)
[-] No table on Page 20 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 21 (H-lines: 49, V-lines: 50)
[-] No table on Page 44 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 45 (H-lines: 5, V-lines: 3)
[-] No table on Page 46 (H-lines: 0, V-lines: 0)
[+] Table detected on Page 47 (H-lines: 3, V-lines: 3)
[+] Table detected on Page 48 (H-lines: 14, V-lines: 9)
[+] Table detected on Page 49 (H-lines: 7, V-lines: 3)
[+] Table detected on Page 56 (H-lines: 3, V-lines: 3)
"""

# Run the function
if __name__ == "__main__":
    parse_table_log(log_content)

    # --- OPTIONAL: If you want to read from a real file, uncomment below ---
    # with open("your_log_file.txt", "r") as f:
    #     file_content = f.read()
    #     parse_table_log(file_content)