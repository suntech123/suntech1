import pandas as pd

# 1. Your original list
sqlite_patterns = [
    '*Outpatient Prescription Drug Rider*',
    '*Outpatient Prescription Drug Benefits*',
    '*Routine Vision Examination Rider*',
    '*Vision Materials Rider*',
    '*Gender Dysphoria Rider*',
    '*Expatriate Insurance Rider*',
    '*Vision Material and Eligible Expenses Rider*',
    'Section* Pediatric Vision Care Services*',
    'Section* Pediatric Dental Care Services*'
]

# 2. Conversion Logic
# We replace the SQLite wildcard '*' with the Regex wildcard '.*'
# Then we join them all with '|' which means "OR"
pandas_pattern = '|'.join([p.replace('*', '.*') for p in sqlite_patterns])

# 3. Implementation in Pandas
# Assuming your dataframe is named 'df' and column is 'text_column'
# case=False makes it case-insensitive (optional but recommended)
filtered_df = df[df['text_column'].str.contains(pandas_pattern, regex=True, case=False)]

# --- DEBUGGING ---
# If you want to see what the generated pattern looks like:
print(pandas_pattern)