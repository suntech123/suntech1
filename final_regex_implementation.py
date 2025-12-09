import pandas as pd
import numpy as np

def categorize_headers(df):
    """
    Searches for specific regex patterns in columns starting with 'Header'
    and assigns a category in a new column.
    """
    
    # 1. Define the Pattern Lists (Transcribed from Image)
    # Note: We use raw strings (r'') to handle backslashes correctly for regex.
    
    exclusions_patterns = [
        r'EXCLUSIONS',
        r'NOT COVERED',
        r"PLAN DOESN.?T COVER"  # Handles "DOESN'T" or "DOESNT"
    ]

    inclusions_patterns = [
        r'SECTION\s*.:\s*COVERED.*SERVICES', # Matches SECTION .: COVERED SERVICES
        r'.*WHAT\s+IS\s+COVERED.*',
        r'COVERED.*SERVICES',
        r'.*COVERED.*EXPENSES.*',
        r'.*BENEFITS/COVERAGE.*',
        r'.*ADDITIONAL.*COVERAGE\s+DETAILS.*',
        r'.*ADDITIONAL\s+BENEFITS\s*\[0-9a-zA-Z\s\]\s*EQUIPMENTS.*',
        r'.*PLAN\s+BENEFITS.*',
        r'.*MEDICAL\s+BENEFITS.*',
        r'.*BEHAVIORAL\s+HEALTH\s+BENEFITS.*',
        r'.*PLANS\s+COVER.*',
        r'OTHER\s+COVERED\s+SERVICES',
        r'ADDITIONAL\s+COVERAGE',
        r'ADDITIONAL\s+BENEFITS',
        r'SURVIVOR\s+BENEFIT',
        r'WHAT\s+EXPENSES\s+ARE\s+COVERED'
    ]

    inclusion_exclusion_rider_patterns = [
        r'.*Outpatient Prescription Drug Rider.*',
        r'.*Outpatient Prescription Drug Benefits.*',
        r'.*Routine Vision Examination Rider.*',
        r'.*Vision Materials Rider.*',
        r'.*Gender Dysphoria Rider.*',
        r'.*Expatriate Insurance Rider.*',
        r'.*Vision Material and Eligible Expenses Rider.*',
        r'Section.*Pediatric Vision Care Services.*',
        r'Section.*Pediatric Dental Care Services.*'
    ]

    generic_rider_patterns = [
        r'.*Travel\s+and\s+Lodging\s+Program\s+Rider.*',
        r'.*Evacuation\s+Rider.*',
        r'.*Real\s+Appeal\s+Rider.*',
        r'.*Virtual\s+Behavioral\s+Health\s+Therapy\s+and\s+Coaching\s+Rider.*',
        r'.*UnitedHealthcare\s+Rewards\s+Rider.*',
        r'.*RIDER\s+CONTINUED\s+COVERAGE\s+FOR\s+CERTAIN\s+PUBLIC\s+SAFETY.*',
        r'.*RIDER\s+CONTINUED\s+COVERAGE\s+FOR\s+DISABLED\s+OR\s+RETIRED\s+PUBLIC.*',
        r'.*RIDER\s+CONTINUED\s+COVERAGE\s+FOR\s+CERTAIN\s+DISABLED\s+OR\s+RETIRED.*',
        r'.*Expatriate\s+Insurance\s+Rider.*',
        r'.*Ningen\s+Dock\s+and\s+Vision\s+Materials\s+Rider.*',
        r'.*Fertility\s+Preservation\s+for\s+Iatrogenic\s+Infertility\s+Rider.*',
        r'.*Kidney\s+Donor\s+Travel\s+and\s+Lodging\s+Program\s+Rider.*',
        r'.*Gender\s+Dysphoria\s+Rider.*',
        r'.*List\s+of\s+Pre-Deductible\s+Covered\s+Health\s+Care\s+Services.*',
        r'.*Abortion\s+Coverage\s+Rider.*',
        r'.*Mental\s+Health\s+Therapy\s+and\s+Coaching\s+Rider.*',
        r'.*Reimbursement\s+for\s+Travel\s+and\s+Lodging\s+Expenses.*',
        r'.*Domestic\s+Partner\s+Rider.*',
        r'.*Care\s+Cash\s+Rider.*',
        r'.*Sanvello\s+SM\s+Self\s+Help\s+Tool\s+Rider.*',
        r'.*Rider.*' # Catch-all rider
    ]

    # 2. Map Categories to their Pattern Lists
    # Order matters here! We usually want to find specific Riders first, then General Inclusions, etc.
    # However, Exclusions are usually distinct.
    # You can change this order based on which category should "win" if a row matches multiple.
    category_map = [
        ('Exclusion', exclusions_patterns),
        ('Specific Rider', inclusion_exclusion_rider_patterns),
        ('Generic Rider', generic_rider_patterns),
        ('Inclusion', inclusions_patterns)
    ]

    # 3. Identify Target Columns
    # Finds columns like "Header", "Header1", "Header2", etc.
    header_cols = [col for col in df.columns if str(col).startswith('Header')]
    print(f"Searching in columns: {header_cols}")

    # Initialize new column
    df['Category'] = None 

    # 4. Iterate and Apply Logic
    for category_name, pattern_list in category_map:
        
        # Join list into one regex string: (PatternA|PatternB|PatternC)
        combined_regex = '|'.join(pattern_list)
        
        # Create a mask initialized to False
        mask = pd.Series(False, index=df.index)
        
        for col in header_cols:
            # fillna('') is crucial because regex fails on NaN objects
            # case=False ensures case insensitivity
            col_matches = df[col].fillna('').astype(str).str.contains(combined_regex, case=False, regex=True)
            
            # Combine matches using OR (|) logic
            mask = mask | col_matches
        
        # Assign category ONLY if the Category is currently None 
        # (This prevents overwriting if you have a priority order)
        # If you want later matches to overwrite earlier ones, remove "& df['Category'].isna()"
        df.loc[mask & df['Category'].isna(), 'Category'] = category_name

    return df

# ==========================================
# TEST IMPLEMENTATION
# ==========================================

# Dummy Data
data = {
    'ID': [1, 2, 3, 4, 5],
    'Header1': [
        'Plan EXCLUSIONS', 
        'Nothing here', 
        'Section IV Pediatric Dental Care Services', 
        None, 
        'Some random text'
    ],
    'Header2': [
        None, 
        'WHAT IS COVERED', 
        None, 
        'Travel and Lodging Program Rider', 
        'EXCLUSIONS'
    ],
    'Header3': [
        None, None, None, None, None
    ]
}

df = pd.DataFrame(data)

print("--- Input Data ---")
print(df)

# Run the function
df_categorized = categorize_headers(df)

print("\n--- Processed Data with Category ---")
print(df_categorized[['ID', 'Header1', 'Header2', 'Category']])