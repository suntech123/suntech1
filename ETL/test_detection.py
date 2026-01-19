import re
import os
import csv
import sys

def process_log_to_csv(log_text, output_csv="multi_file_report.csv"):
    lines = log_text.splitlines()
    
    # State variable to keep track of which file we are currently looking at
    current_filename = "Unknown_File"
    
    # Store results here
    csv_rows = []
    
    # Regex patterns
    # Pattern to find the filename line
    filename_pattern = r"Analyzing \d+ pages in: (.+\.pdf)"
    # Pattern to find the table details
    table_pattern = r"\[\+\] Table detected on Page (\d+) \(H-lines: (\d+), V-lines: (\d+)\)"

    print("Processing log data...")

    for line in lines:
        # 1. Check if this line is a new File header
        file_match = re.search(filename_pattern, line)
        if file_match:
            full_path = file_match.group(1)
            # Clean the filename: remove path and extension
            current_filename = os.path.splitext(os.path.basename(full_path))[0]
            # print(f"-> Switched to file: {current_filename}") # Uncomment for debug
            continue # Move to next line

        # 2. Check if this line is a Table detection
        table_match = re.search(table_pattern, line)
        if table_match:
            page_num = int(table_match.group(1))
            h_lines = int(table_match.group(2))
            v_lines = int(table_match.group(3))

            # 3. Apply Logic: H-lines >= 2 AND V-lines <= 3
            if h_lines >= 2 and v_lines <= 3:
                # Append the row using the CURRENT filename
                csv_rows.append([current_filename, page_num, h_lines, v_lines])

    # 4. Write results to CSV
    if csv_rows:
        try:
            with open(output_csv, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Filename', 'Page No', 'H-lines', 'V-lines'])
                writer.writerows(csv_rows)
            
            print(f"\nSuccess! Found {len(csv_rows)} matching tables.")
            print(f"CSV generated: {os.path.abspath(output_csv)}")
        except IOError as e:
            print(f"Error writing CSV: {e}")
    else:
        print("No tables found matching criteria (H>=2, V<=3).")

# ==========================================
# MAIN EXECUTION
# ==========================================
if __name__ == "__main__":
    # Define your input file name here
    input_log_file = "output_run.txt" # <--- Make sure this matches your file name

    if os.path.exists(input_log_file):
        try:
            with open(input_log_file, 'r', encoding='utf-8') as f:
                content = f.read()
            process_log_to_csv(content)
        except Exception as e:
            print(f"Error reading file: {e}")
    else:
        print(f"File '{input_log_file}' not found. Please check the name.")