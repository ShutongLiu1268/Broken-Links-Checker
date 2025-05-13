import streamlit as st
import pandas as pd
import io
import time
from url_checker import check_urls, check_url, generate_report

st.set_page_config(
    page_title="URL 404 Checker",
    page_icon="🔗",
    layout="wide"
)

st.title("URL 404 Checker")

# Create tabs for different input methods
tab1, tab2 = st.tabs(["Batch Check (Excel)", "Single URL Check"])

with tab1:
    st.write("Upload an Excel file with URLs to check for 404 errors")
    # File upload section
    uploaded_file = st.file_uploader("Choose an Excel file", type=["xlsx", "xls"])

with tab1:
    if uploaded_file is not None:
        # Load the Excel file
        try:
            df = pd.read_excel(uploaded_file)
            st.success("File uploaded successfully!")
            
            # Display first few rows of the Excel file
            #st.subheader("Preview of your Excel file")
           #st.dataframe(df.head())
            
            # Let user select which column contains URLs
            columns = df.columns.tolist()
            selected_column = st.selectbox("Select the column that contains URLs", columns)
            
            # Validate that the selected column contains URLs
            if selected_column and len(df) > 0:
                urls = df[selected_column].dropna().tolist()
                
                st.write(f"Found {len(urls)} URLs to process")
                
                # Options for concurrent processing
                concurrency = st.slider("Concurrent connections (higher = faster but more resource intensive)", 
                                       min_value=1, max_value=20, value=5)
                
                timeout = st.slider("Request timeout (seconds)", 
                                  min_value=1, max_value=30, value=10)
                
                # Process button
                if st.button("Check URLs for 404 errors"):
                    if len(urls) == 0:
                        st.error("No URLs found in the selected column!")
                    elif len(urls) > 500:
                        st.error("For performance reasons, please limit your check to 500 URLs at once.")
                    else:
                        # Progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        # Process URLs
                        results = []
                        
                        with st.spinner("Checking URLs..."):
                            def update_progress(progress, current, total, url, status):
                                progress_bar.progress(progress)
                                status_text.text(f"Checking {current}/{total}: {url} - Status: {status}")
                                
                            results = check_urls(urls, concurrency, timeout, update_progress)
                            
                        # Completion message
                        progress_bar.progress(100)
                        status_text.text("Processing complete!")
                        
                        # Display report
                        st.subheader("Results Summary")
                        total_urls = len(results)
                        broken_urls = sum(1 for result in results if result["status_code"] == 404)
                        other_errors = sum(1 for result in results if result["status_code"] not in [200, 404])
                        
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Total URLs", total_urls)
                        with col2:
                            st.metric("404 Errors", broken_urls)
                        with col3:
                            st.metric("Other Errors", other_errors)
                        
                        # Create detailed report DataFrame
                        report_df = pd.DataFrame(results)
                        
                        # Filter for broken URLs
                        #if not report_df.empty:
                            #st.subheader("Broken URLs (404 errors)")
                            # broken_df = report_df[report_df["status_code"] == 404]
                             #if len(broken_df) > 0:
                                #st.dataframe(broken_df)
                            # else:
                                 #st.success("No 404 errors found!")
                        # Display all errors (not just 404)
                            if not report_df.empty:
                                # First show 404 errors
                                st.subheader("Broken URLs (404 errors)")
                                broken_df = report_df[report_df["status_code"] == 404]
                                if len(broken_df) > 0:
                                    st.dataframe(broken_df)
                                else:
                                    st.success("No 404 errors found!")
                                
                                # Then show other errors
                                st.subheader("Other Errors")
                                other_errors_df = report_df[(report_df["status_code"] != 200) & (report_df["status_code"] != 404)]
                                if len(other_errors_df) > 0:
                                    st.dataframe(other_errors_df)
                                else:
                                    st.success("No other errors found!")
                            # Export options
                            report_excel = generate_report(report_df)
                            st.download_button(
                                label="Download Full Report (Excel)",
                                data=report_excel,
                                file_name="url_check_report.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                            
                            # CSV Export
                            csv = report_df.to_csv(index=False)
                            st.download_button(
                                label="Download Full Report (CSV)",
                                data=csv,
                                file_name="url_check_report.csv",
                                mime="text/csv"
                            )
            
        except Exception as e:
            st.error(f"Error processing the file: {str(e)}")

# Single URL check tab content
with tab2:
    st.write("Enter a single URL to check for 404 errors")
    
    # URL input field
    single_url = st.text_input("URL to check", placeholder="https://example.com/page-to-check")
    
    # Timeout option for single URL
    single_timeout = st.slider("Request timeout (seconds)", 
                               min_value=1, max_value=30, value=10,
                               key="single_timeout")
    
    # Check button for single URL
    if st.button("Check URL"):
        if not single_url:
            st.error("Please enter a URL to check!")
        else:
            with st.spinner("Checking URL..."):
                result = check_url(single_url, timeout=single_timeout)
                
            # Display result
            st.subheader("Result")
            
            # Status indicator
            if result["status_code"] == 200:
                st.success(f"URL is working! Status: {result['status_code']} - {result['status']}")
            elif result["status_code"] == 404:
                st.error(f"URL is broken! Status: {result['status_code']} - {result['status']}")
            elif result["status_code"] is None:
                st.error(f"Error checking URL: {result['error']}")
            else:
                st.warning(f"URL returned status: {result['status_code']} - {result['status']}")
            
            # Detailed result
            st.json(result)

# App footer
st.markdown("---")
st.markdown("URL 404 Checker - Check your website links for errors and fix broken pages")
