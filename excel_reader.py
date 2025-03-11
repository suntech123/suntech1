import streamlit as st
import pandas as pd

# Set page title
st.title("Excel File Reader App")

# File upload section
uploaded_file = st.file_uploader(
    "Choose an Excel file",
    type=["xlsx", "xls"],
    help="Upload XLSX or XLS files only"
)

if uploaded_file is not None:
    try:
        # Read Excel file
        excel_file = pd.ExcelFile(uploaded_file)
        
        # Get sheet names
        sheet_names = excel_file.sheet_names
        
        # Let user select sheet
        selected_sheet = st.selectbox(
            "Select Worksheet",
            sheet_names,
            index=0
        )
        
        # Read selected sheet into DataFrame
        df = pd.read_excel(excel_file, sheet_name=selected_sheet)
        
        # Show success message
        st.success("File loaded successfully!")
        
        # Display file info
        st.subheader("File Details")
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Rows", df.shape[0])
        col2.metric("Total Columns", df.shape[1])
        col3.metric("Selected Worksheet", selected_sheet)
        
        # Show data preview
        st.subheader("Data Preview")
        st.dataframe(df.head(20), use_container_width=True)
        
        # Show full data checkbox
        if st.checkbox("Show full data"):
            st.subheader("Full Data View")
            st.dataframe(df, use_container_width=True)
        
        # Show basic statistics
        if st.checkbox("Show basic statistics"):
            st.subheader("Basic Statistics")
            st.write(df.describe())
            
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
else:
    st.info("Please upload an Excel file to get started")

# Instructions in sidebar
with st.sidebar:
    st.markdown("## Instructions")
    st.markdown("""
    1. Upload an Excel file (XLSX/XLS)
    2. Select worksheet from dropdown
    3. View interactive data preview
    4. Use checkboxes to see more data
    5. Tables are scrollable and sortable
    """)
    st.markdown("---")
    st.markdown("Made with using Streamlit")

# Required libraries installation hint
st.sidebar.markdown("**Required libraries**")
st.sidebar.code("pip install streamlit pandas openpyxl")