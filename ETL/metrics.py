import pandas as pd

# ---------------------------------------------------------
# 1. Setup & Pre-Calculation (Continuing from previous logic)
# ---------------------------------------------------------
# Assuming 'df' is the dataframe from the previous step with:
# 'ScriptPages', 'ActualPages', 'ActualNoTable' (FP List), 'ActualTable' (FN List), 'Total Pages'

# We need the counts for every individual row first to do the math
df['TP_Count'] = df.apply(lambda row: len(set(row['ScriptPages']).intersection(row['ActualPages'])), axis=1)
df['FP_Count'] = df['ActualNoTable'].apply(len)
df['FN_Count'] = df['ActualTable'].apply(len)
df['TN_Count'] = df.apply(lambda row: row['Total Pages'] - len(set(row['ScriptPages']).union(row['ActualPages'])), axis=1)

# ---------------------------------------------------------
# 2. Calculate Global Metrics (Aggregate)
# ---------------------------------------------------------
# Summing up counts across all files
TP = df['TP_Count'].sum()
FP = df['FP_Count'].sum()
FN = df['FN_Count'].sum()
TN = df['TN_Count'].sum()

# Helper function to avoid DivisionByZero errors
def safe_div(n, d):
    return n / d if d > 0 else 0.0

# Definitions:
# Accuracy: (TP+TN) / Total
# Precision: TP / (TP + FP)  -> Out of all pages predicted as tables, how many were actually tables?
# Recall:    TP / (TP + FN)  -> Out of all actual tables, how many did the script find?
# F1 Score:  2 * (Prec * Rec) / (Prec + Rec)

global_accuracy = safe_div((TP + TN), (TP + TN + FP + FN))
global_precision = safe_div(TP, (TP + FP))
global_recall = safe_div(TP, (TP + FN))
global_f1 = safe_div((2 * global_precision * global_recall), (global_precision + global_recall))
global_specificity = safe_div(TN, (TN + FP)) # True Negative Rate

# Create a Summary DataFrame
metrics_summary = pd.DataFrame({
    'Metric': ['Accuracy', 'Precision', 'Recall', 'F1 Score', 'Specificity'],
    'Value': [global_accuracy, global_precision, global_recall, global_f1, global_specificity],
    'Description': [
        'Overall correctness (both Table and No-Table)',
        'When script predicts a table, how often is it right?',
        'How many of the actual tables did the script find?',
        'Balance between Precision and Recall',
        'How well does script identify pages with NO tables?'
    ]
})

print("--- Global Performance Metrics ---")
print(metrics_summary)

# ---------------------------------------------------------
# 3. Calculate Per-File Metrics (Row-by-Row)
# ---------------------------------------------------------
# This helps identify which specific files are failing

df['Accuracy'] = (df['TP_Count'] + df['TN_Count']) / df['Total Pages']

df['Precision'] = df.apply(lambda x: safe_div(x['TP_Count'], (x['TP_Count'] + x['FP_Count'])), axis=1)

df['Recall'] = df.apply(lambda x: safe_div(x['TP_Count'], (x['TP_Count'] + x['FN_Count'])), axis=1)

df['F1_Score'] = df.apply(lambda x: safe_div(
    (2 * x['Precision'] * x['Recall']), 
    (x['Precision'] + x['Recall'])
), axis=1)

print("\n--- Per-File Metrics (First 5 Rows) ---")
print(df[['Filename', 'Accuracy', 'Precision', 'Recall', 'F1_Score']].head())
