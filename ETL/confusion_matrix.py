import pandas as pd
import numpy as np
import ast

# ---------------------------------------------------------
# 1. Setup Sample Data (Mimicking your screenshot)
# ---------------------------------------------------------
data = {
    'Filename': ['File_A', 'File_B', 'File_C'],
    'Total Pages': [152.0, 155.0, 125.0],
    # Simulating data read from CSV where lists look like strings
    'ScriptPages': ["[16, 17, 18, 19]", "[10, 20]", "[]"], 
    'ActualPages': ["[16, 17, 18]", "[8, 9, 10]", "[1, 2]"]
}
df = pd.DataFrame(data)

# ---------------------------------------------------------
# 2. Data Cleaning & Type Conversion
# ---------------------------------------------------------

# Requirement 1: Change Data type of "Total Pages" to int
# We use fillna(0) just in case there are missing values before converting
df['Total Pages'] = df['Total Pages'].fillna(0).astype(int)

# Helper function to convert string lists (e.g. "[1, 2]") to actual lists
def parse_list_column(val):
    if pd.isna(val) or val == '':
        return []
    if isinstance(val, list):
        return val
    try:
        return ast.literal_eval(val)
    except:
        return []

# Apply conversion to ScriptPages and ActualPages
df['ScriptPages'] = df['ScriptPages'].apply(parse_list_column)
df['ActualPages'] = df['ActualPages'].apply(parse_list_column)

# ---------------------------------------------------------
# 3. Create Derived Fields
# ---------------------------------------------------------

# 1. TotalPagesWithTable = length of ActualPages lists
df['TotalPagesWithTable'] = df['ActualPages'].apply(len)

# 2. TotalPagesWithNoTable = TotalPages - TotalPagesWithTable
df['TotalPagesWithNoTable'] = df['Total Pages'] - df['TotalPagesWithTable']

# 3. ActualNoTable = ScriptPages - ActualPages
# Logic: Pages detected by script (ScriptPages) BUT NOT in actual (ActualPages)
# This represents FALSE POSITIVES
df['ActualNoTable'] = df.apply(lambda row: list(set(row['ScriptPages']) - set(row['ActualPages'])), axis=1)

# 4. ActualTable = ActualPages - ScriptPages
# Logic: Pages that are actually tables (ActualPages) BUT NOT detected by script (ScriptPages)
# This represents FALSE NEGATIVES
df['ActualTable'] = df.apply(lambda row: list(set(row['ActualPages']) - set(row['ScriptPages'])), axis=1)

# ---------------------------------------------------------
# 4. Generate Confusion Matrix Logic
# ---------------------------------------------------------

# To build the matrix, we need the COUNTS of pages for every category across the whole dataset.

# TP (True Positive): Pages in BOTH Script and Actual
tp_count = df.apply(lambda row: len(set(row['ScriptPages']).intersection(row['ActualPages'])), axis=1).sum()

# FP (False Positive): Script says YES, Actual says NO (Count of your 'ActualNoTable' column)
fp_count = df['ActualNoTable'].apply(len).sum()

# FN (False Negative): Script says NO, Actual says YES (Count of your 'ActualTable' column)
fn_count = df['ActualTable'].apply(len).sum()

# TN (True Negative): Pages with NO table in Script AND NO table in Actual
# Logic: Total Pages - (Union of all pages mentioned in Script or Actual)
tn_count = df.apply(lambda row: row['Total Pages'] - len(set(row['ScriptPages']).union(row['ActualPages'])), axis=1).sum()

# ---------------------------------------------------------
# 5. Create and Display Confusion Matrix
# ---------------------------------------------------------

confusion_matrix = pd.DataFrame(
    data=[
        [tp_count, fp_count],  # Row 1: Script Detected (1)
        [fn_count, tn_count]   # Row 2: Script Detected (0)
    ],
    columns=['Actual (Table Exists) 1', 'Actual (No Table) 0'],
    index=['Script (Detected Table) 1', 'Script (Detected Table) 0']
)

# Styling to match your request image
print("--- Processed Data Frame ---")
print(df[['Filename', 'Total Pages', 'TotalPagesWithTable', 'TotalPagesWithNoTable', 'ActualNoTable', 'ActualTable']])

print("\n--- Confusion Matrix ---")
print(confusion_matrix)
