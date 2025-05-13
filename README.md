# URL 404 Checker

A simple web application that checks URLs for 404 and other errors. Built with Streamlit.

## Features

- **Batch URL Checking**: Upload an Excel file containing URLs to check multiple links at once
- **Single URL Checking**: Check individual URLs directly without uploading a file
- **Detailed Reports**: Get comprehensive reports on URL status, including status codes and error types
- **Export Options**: Download results as Excel or CSV files for further analysis

## How to Use

### Single URL Check
1. Select the "Single URL Check" tab
2. Enter the URL you want to check
3. Click "Check URL" to see the results

### Batch URL Check
1. Select the "Batch Check (Excel)" tab
2. Prepare an Excel file with URLs (can be in any column)
3. Upload the Excel file
4. Select the column containing URLs
5. Adjust concurrent connections and timeout settings if needed
6. Click "Check URLs for 404 errors"
7. View the results and download reports as needed

## Technical Details

Built with:
- Streamlit
- Pandas
- Requests
- XlsxWriter

## Local Development

If you want to run this application locally:

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Run the application: `streamlit run app.py`

## License

MIT License