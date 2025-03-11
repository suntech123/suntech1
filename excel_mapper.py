import streamlit as st
import pandas as pd
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

st.title("Excel Data Mapper")

# Session State to preserve data
if 'filled_data' not in st.session_state:
    st.session_state.filled_data = None

def map_and_transfer_data(source_df, target_df):
    """Map columns and transfer data with normalization"""
    # Normalize column names (case-insensitive, strip whitespace)
    source_cols = [str(col).strip().lower() for col in source_df.columns]
    target_cols = [str(col).strip().lower() for col in target_df.columns]
    
    # Create empty target dataframe with original column names
    filled_df = pd.DataFrame(columns=target_df.columns)
    
    # Map data
    for target_col in target_df.columns:
        normalized_target = str(target_col).strip().lower()
        if normalized_target in source_cols:
            source_col = source_df.columns[source_cols.index(normalized_target)]
            filled_df[target_col] = source_df[source_col].values
            
    return filled_df

def get_mapping_stats(source_df, target_df):
    """Generate mapping statistics"""
    stats = {
        'total_target_columns': len(target_df.columns),
        'matched_columns': 0,
        'unmatched_columns': [],
        'matched_percentage': 0
    }
    
    source_cols = [str(col).strip().lower() for col in source_df.columns]
    
    for target_col in target_df.columns:
        normalized_target = str(target_col).strip().lower()
        if normalized_target in source_cols:
            stats['matched_columns'] += 1
        else:
            stats['unmatched_columns'].append(target_col)
    
    if stats['total_target_columns'] > 0:
        stats['matched_percentage'] = round(
            (stats['matched_columns'] / stats['total_target_columns']) * 100, 2
        )
    
    return stats

# File Upload Section
st.header("1. Upload Files")
col1, col2 = st.columns(2)

with col1:
    source_file = st.file_uploader("Upload Source Excel", type=["xlsx", "xls"])

with col2:
    target_file = st.file_uploader("Upload Target Excel", type=["xlsx", "xls"])

# Sheet Selection Section
st.header("2. Select Sheets")
sheet_col1, sheet_col2 = st.columns(2)

source_sheet = None
target_sheet = None

if source_file:
    with sheet_col1:
        source_sheets = pd.ExcelFile(source_file).sheet_names
        source_sheet = st.selectbox("Source Sheet", source_sheets)

if target_file:
    with sheet_col2:
        target_sheets = pd.ExcelFile(target_file).sheet_names
        target_sheet = st.selectbox("Target Sheet", target_sheets)

# Processing Section
if source_file and target_file and source_sheet and target_sheet:
    if st.button("Process Data"):
        with st.spinner("Processing..."):
            try:
                # Read files
                source_df = pd.read_excel(source_file, sheet_name=source_sheet)
                target_df = pd.read_excel(target_file, sheet_name=target_sheet)
                
                # Process data
                filled_df = map_and_transfer_data(source_df, target_df)
                stats = get_mapping_stats(source_df, target_df)
                
                # Save to session state
                st.session_state.filled_data = filled_df
                st.session_state.stats = stats
                
                st.success("Data mapping completed!")
                
            except Exception as e:
                st.error(f"Error processing files: {str(e)}")

# Display Statistics
if 'stats' in st.session_state:
    st.header("Mapping Statistics")
    
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Target Columns", st.session_state.stats['total_target_columns'])
    col2.metric("Matched Columns", st.session_state.stats['matched_columns'])
    col3.metric("Match Percentage", f"{st.session_state.stats['matched_percentage']}%")
    
    if st.session_state.stats['unmatched_columns']:
        st.subheader("Unmapped Columns")
        st.write(", ".join(st.session_state.stats['unmatched_columns']))

# Download Section
if st.session_state.filled_data is not None:
    st.header("Download Mapped File")
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        st.session_state.filled_data.to_excel(writer, index=False)
    
    # Create download button
    st.download_button(
        label="Download Mapped File",
        data=output.getvalue(),
        file_name="mapped_output.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

# Instructions
with st.expander("How to use this app"):
    st.markdown("""
    1. Upload both source and target Excel files
    2. Select appropriate sheets from both files
    3. Click 'Process Data' to perform mapping
    4. Review mapping statistics
    5. Download the mapped file
    """)
    st.markdown("**Note:** Column matching is case-insensitive and ignores whitespace")