import re
import pandas as pd

log_lines = []
input_file = "logs.txt"  # Replace with your actual file path

# Updated Regex Pattern:
# Group 1 (Filename): Everything between "Finished" and ".pdf"
# Group 2 (Count): The digits after "Total pages with tables:"
# Group 3 (List): The brackets and content after "Page List:"
pattern = re.compile(r"Finished\s+(.*?\.pdf).*?Total pages with tables:\s+(\d+).*?Page List:\s+(\[.*\])")

with open(input_file, 'r') as f:
    for line in f:
        match = pattern.search(line)
        if match:
            # Extract the 3 groups
            filename = match.group(1)
            table_count = match.group(2)
            page_list = match.group(3)
            
            log_lines.append({
                "filename": filename,
                "table_count": int(table_count), # Convert to integer for analysis
                "page_list": page_list
            })

# Create DataFrame
df = pd.DataFrame(log_lines)

# --- Analysis Examples ---
print("--- Extracted Data Sample ---")
print(df.head())

print("\n--- Summary Stats ---")
print(f"Total Tables Detected across all files: {df['table_count'].sum()}")
print(f"Average Tables per PDF: {df['table_count'].mean():.2f}")

# Save to CSV for your Excel analysis
# df.to_csv("table_metrics.csv", index=False)