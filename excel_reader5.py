import streamlit as st
import pandas as pd

def process_file(uploaded_file, file_number):
    """Helper function to process and display basic file info"""
    try:
        if uploaded_file is None:
            return None
            
        excel_file = pd.ExcelFile(uploaded_file)
        sheet_names = excel_file.sheet_names
        
        # Worksheet selection with custom styling
        selected_sheet = st.selectbox(
            f"📋 Select Worksheet for File {file_number}",
            sheet_names,
            index=0,
            key=f"sheet_{file_number}"
        )
        
        # Read selected sheet
        df = pd.read_excel(excel_file, sheet_name=selected_sheet)
        
        # Success message with emoji
        st.success(f"✅ File {file_number} loaded successfully!")
        
        # Display metrics with custom styling
        st.markdown(f"<h3 style='color: #2e86c1;'>File {file_number} Summary</h3>", 
                    unsafe_allow_html=True)
        
        # Create spaced columns with custom colors
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"<div style='padding: 15px; background-color: #e8f8f5; border-radius: 10px;'>"
                        f"<h4 style='color: #17a589;'>Rows</h4>"
                        f"<h2 style='color: #148f77;'>{df.shape[0]}</h2></div>", 
                        unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"<div style='padding: 15px; background-color: #fdedec; border-radius: 10px;'>"
                        f"<h4 style='color: #c0392b;'>Columns</h4>"
                        f"<h2 style='color: #a93226;'>{df.shape[1]}</h2></div>", 
                        unsafe_allow_html=True)
        
        with col3:
            st.markdown(f"<div style='padding: 15px; background-color: #f4ecf7; border-radius: 10px;'>"
                        f"<h4 style='color: #6c3483;'>Worksheet</h4>"
                        f"<h2 style='color: #5b2c6f;'>{selected_sheet}</h2></div>", 
                        unsafe_allow_html=True)
        
        return df
    except Exception as e:
        st.error(f"🚨 Error loading File {file_number}: {str(e)}")
        return None

# Main app structure with custom styling
st.set_page_config(layout="wide")
st.markdown("<h5 style='text-align: center; color: #2c3e50;'>📁 Excel File Comparator</h5>", 
            unsafe_allow_html=True)

# Create spaced columns for uploaders
col_space1, col_upload1, col_space2, col_upload2, col_space3 = st.columns([0.1, 0.4, 0.05, 0.4, 0.1])

with col_upload1:
    # Custom uploader styling
    st.markdown("<div style='padding: 20px; background-color: #f8f9f9; border-radius: 10px; margin-bottom: 30px;'>"
                "<h3 style='color: #3498db;'>First File Upload</h3>", unsafe_allow_html=True)
    file1 = st.file_uploader(
        " ",
        type=["xlsx", "xls"],
        help="Select first Excel file",
        key="file1",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_upload2:
    st.markdown("<div style='padding: 20px; background-color: #f8f9f9; border-radius: 10px; margin-bottom: 30px;'>"
                "<h3 style='color: #e74c3c;'>Second File Upload</h3>", unsafe_allow_html=True)
    file2 = st.file_uploader(
        " ",
        type=["xlsx", "xls"],
        help="Select second Excel file",
        key="file2",
        label_visibility="collapsed"
    )
    st.markdown("</div>", unsafe_allow_html=True)

# Main processing logic
if file1 or file2:
    st.markdown("<hr style='border: 1px solid #d5d8dc'>", unsafe_allow_html=True)
    
    # Create spaced columns for results
    col_result1, col_space, col_result2 = st.columns([0.45, 0.1, 0.45])
    
    with col_result1:
        if file1:
            process_file(file1, 1)
        else:
            st.info("ℹ️ Please upload first file")
    
    with col_result2:
        if file2:
            process_file(file2, 2)
        else:
            st.info("ℹ️ Please upload second file")

    # Status message with styling
    if file1 and file2:
        st.markdown("<div style='padding: 15px; background-color: #e8f6f3; border-radius: 10px; "
                    "margin: 20px 0; text-align: center;'>"
                    "<h4 style='color: #1d8348;'>✅ Both files successfully processed!</h4></div>", 
                    unsafe_allow_html=True)

# Enhanced sidebar styling
with st.sidebar:
    st.markdown("<h2 style='color: #2c3e50;'>📌 Navigation Guide</h2>", unsafe_allow_html=True)
    st.markdown("""
    <div style='padding: 10px; background-color: #f8f9f9; border-radius: 10px;'>
    <ol style='color: #2c3e50;'>
        <li>Upload Excel files</li>
        <li>Select worksheets</li>
        <li>Compare metrics</li>
    </ol>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    st.markdown("<h4 style='color: #2c3e50;'>🔧 Requirements</h4>", unsafe_allow_html=True)
    st.code("pip install streamlit pandas openpyxl")
    st.markdown("---")
    st.markdown("<div style='text-align: center; color: #7f8c8d;'>Made with ❤️ using Streamlit</div>", 
                unsafe_allow_html=True)

if not file1 and not file2:
    st.markdown("<div style='text-align: center; padding: 50px;'>"
                "<h4 style='color: #7f8c8d;'>👋 Upload Excel files to begin</h4>"
                "</div>", unsafe_allow_html=True)