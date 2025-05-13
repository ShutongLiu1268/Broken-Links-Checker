import requests
import pandas as pd
import io
import concurrent.futures
import time
from requests.exceptions import RequestException, Timeout, ConnectionError

def check_url(url, timeout=10):
    """
    Check a single URL for its HTTP status
    
    Args:
        url (str): URL to check
        timeout (int): Request timeout in seconds
        
    Returns:
        dict: Result with URL, status code, and error message if any
    """
    result = {
        "url": url,
        "status_code": None,
        "status": "Unknown",
        "error": None,
        "response_time": None
    }
    
    try:
        # Add http:// prefix if missing
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
            
        start_time = time.time()
        response = requests.get(url, timeout=timeout, allow_redirects=True)
        end_time = time.time()
        
        result["status_code"] = response.status_code
        result["response_time"] = round(end_time - start_time, 2)
        
        # Determine status text
        if response.status_code == 200:
            result["status"] = "OK"
        elif response.status_code == 404:
            result["status"] = "Not Found"
        elif 300 <= response.status_code < 400:
            result["status"] = f"Redirect ({response.status_code})"
        elif 400 <= response.status_code < 500:
            result["status"] = f"Client Error ({response.status_code})"
        elif 500 <= response.status_code < 600:
            result["status"] = f"Server Error ({response.status_code})"
        else:
            result["status"] = f"Unknown ({response.status_code})"
            
    except Timeout:
        result["error"] = "Request Timeout"
        result["status"] = "Timeout"
    except ConnectionError:
        result["error"] = "Connection Error"
        result["status"] = "Connection Failed"
    except RequestException as e:
        result["error"] = str(e)
        result["status"] = "Request Failed"
    except Exception as e:
        result["error"] = str(e)
        result["status"] = "Error"
        
    return result

def check_urls(urls, concurrency=5, timeout=10, progress_callback=None):
    """
    Check multiple URLs concurrently for their HTTP status
    
    Args:
        urls (list): List of URLs to check
        concurrency (int): Number of concurrent requests
        timeout (int): Request timeout in seconds
        progress_callback (callable): Function to call with progress updates
        
    Returns:
        list: Results for all URLs
    """
    results = []
    total_urls = len(urls)
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        # Submit all tasks and get futures
        future_to_url = {executor.submit(check_url, url, timeout): url for url in urls}
        
        # Process as tasks complete
        for i, future in enumerate(concurrent.futures.as_completed(future_to_url)):
            url = future_to_url[future]
            try:
                result = future.result()
                results.append(result)
                
                # Update progress if callback provided
                if progress_callback:
                    progress = (i + 1) / total_urls
                    status = result.get("status", "Unknown")
                    progress_callback(progress, i + 1, total_urls, url, status)
                    
            except Exception as e:
                results.append({
                    "url": url,
                    "status_code": None,
                    "status": "Error",
                    "error": str(e),
                    "response_time": None
                })
                
                # Update progress if callback provided
                if progress_callback:
                    progress = (i + 1) / total_urls
                    progress_callback(progress, i + 1, total_urls, url, "Error")
    
    return results

def generate_report(results_df):
    """
    Generate an Excel report from the results
    
    Args:
        results_df (DataFrame): Results data frame
        
    Returns:
        bytes: Excel file as bytes
    """
    output = io.BytesIO()
    
    # Create the Excel writer and add the results
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        # Write results to the main sheet
        results_df.to_excel(writer, sheet_name='All URLs', index=False)
        
        # Create a "404 Errors" sheet
        broken_urls = results_df[results_df["status_code"] == 404]
        if not broken_urls.empty:
            broken_urls.to_excel(writer, sheet_name='404 Errors', index=False)
        
        # Create a "Summary" sheet
        summary_data = {
            'Metric': [
                'Total URLs',
                'Successful (200)',
                '404 Errors',
                'Other Client Errors (4xx)',
                'Server Errors (5xx)',
                'Redirects (3xx)',
                'Connection Errors',
                'Timeouts',
                'Other Errors'
            ],
            'Count': [
                len(results_df),
                len(results_df[results_df["status_code"] == 200]),
                len(results_df[results_df["status_code"] == 404]),
                len(results_df[(results_df["status_code"] >= 400) & (results_df["status_code"] < 500) & (results_df["status_code"] != 404)]),
                len(results_df[(results_df["status_code"] >= 500) & (results_df["status_code"] < 600)]),
                len(results_df[(results_df["status_code"] >= 300) & (results_df["status_code"] < 400)]),
                len(results_df[results_df["status"] == "Connection Failed"]),
                len(results_df[results_df["status"] == "Timeout"]),
                len(results_df[(results_df["status"] == "Error") | (results_df["status"] == "Unknown")])
            ]
        }
        
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
    # Seek to the beginning and return the data
    output.seek(0)
    return output.getvalue()
