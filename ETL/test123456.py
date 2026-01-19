import re
import os
import csv

def generate_csv_from_log(log_text, output_filename="table_report.csv"):
    # 1. Parse the Filename
    # Regex looks for the path ending in .pdf
    filename_match = re.search(r"Analyzing \d+ pages in: (.+\.pdf)", log_text)
    
    clean_filename = "Unknown_File"
    if filename_match:
        full_path = filename_match.group(1)
        # Get just the name (remove path) and remove extension
        clean_filename = os.path.splitext(os.path.basename(full_path))[0]

    print(f"Target Filename: {clean_filename}")

    # 2. Parse Table Detections
    # Regex to capture: Page Number, H-lines, V-lines
    # Pattern looks for: [+] Table detected on Page X (H-lines: Y, V-lines: Z)
    table_pattern = r"\[\+\] Table detected on Page (\d+) \(H-lines: (\d+), V-lines: (\d+)\)"
    
    matches = re.findall(table_pattern, log_text)

    # 3. Filter Data and Prepare CSV Rows
    csv_rows = []
    count = 0

    for match in matches:
        page_num = int(match[0])
        h_lines = int(match[1])
        v_lines = int(match[2])

        # APPLY LOGIC: H-lines >= 2 AND V-lines <= 3
        if h_lines >= 2 and v_lines <= 3:
            csv_rows.append([clean_filename, page_num, h_lines, v_lines])
            count += 1

    # 4. Write to CSV
    if csv_rows:
        try:
            with open(output_filename, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                # Write Header
                writer.writerow(['Filename', 'Page No', 'H-lines', 'V-lines'])
                # Write Data
                writer.writerows(csv_rows)
            
            print(f"Successfully wrote {count} rows to '{output_filename}'")
        except Exception as e:
            print(f"Error writing CSV: {e}")
    else:
        print("No tables matched the criteria (H>=2, V<=3).")

# ==========================================
# INPUT DATA (From your screenshot)
# ==========================================
log_data = """
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
    generate_csv_from_log(log_data)