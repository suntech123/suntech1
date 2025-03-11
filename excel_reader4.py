import streamlit as st
import pandas as pd

def process_file(uploaded_file, file_number):
    """Helper function to process and display basic file info"""
    try:
        if uploaded_file is None:
            return None
            
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        # Worksheet selection
        selected_sheet = st.selectbox(
            f"Select Worksheet for File {file_number}",
            sheet_names,
            index=0,
            key=f"sheet_{file_number}"
        )
        
        # Read selected sheet
        df = pd.read_excel(excel_file, sheet_name=selected_sheet)
        st.success(f"File {file_number} loaded successfully!")
        
        # Display basic metrics
        st.subheader(f"File {file_number} Summary")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows", df.shape[0])
        col2.metric("Total Columns", df.shape[1])
        col3.metric("Selected Worksheet", selected_sheet)
        
        return df
    except Exception as e:
        st.error(f"Error loading File {file_number}: {str(e)}")
        return None

# Main app structure
st.title("PDL - Source grid to PDL template")

# Create two columns for file uploaders
col_upload1, col_upload2 = st.columns(2)

with col_upload1:
    st.subheader("Template Excel File")
    file1 = st.file_uploader(
        "Upload template file",
        type=["xlsx", "xls"],
        help="Select template Excel file",
        key="file1"
    )

with col_upload2:
    st.subheader("Source grid File")
    file2 = st.file_uploader(
        "Upload source grid file",
        type=["xlsx", "xls"],
        help="Select source grid file",
        key="file2"
    )

# Main processing logic
if file1 or file2:
    col1, col2 = st.columns(2)
    
    with col1:
        if file1:
            process_file(file1, 1)
        else:
            st.info("Please upload template file")
    
    with col2:
        if file2:
            process_file(file2, 2)
        else:
            st.info("Please upload source grid file")

    # Show status message
    if file1 and file2:
        st.success("Both files successfully processed")
    else:
        st.warning("Upload both files for comparison")

# Simplified sidebar instructions
with st.sidebar:
    st.markdown("## Basic Guide")
    st.markdown("""
    1. Upload PDL template and UHCP grid files
    2. Select worksheets
    3. Select row number which contains drug data.
    3. Compare basic metrics
    """)

if not file1 and not file2:
    st.info("Upload Excel files to see metrics")