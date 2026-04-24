import requests
import os
from datetime import datetime

#Link to Argo data server (Indian Ocean region)
BASE_URL  = "https://data-argo.ifremer.fr/geo/indian_ocean/"
CACHE_DIR = "data/argo_cache"

os.makedirs(CACHE_DIR, exist_ok=True)

# Single File Download
def download_file(date: datetime):
    filename   = date.strftime("%Y%m%d") + "_prof.nc"
    year       = date.strftime("%Y")
    month      = date.strftime("%m")
    cache_path = os.path.join(CACHE_DIR, filename)

    #if Already downloaded return directly
    if os.path.exists(cache_path):
        print(f"Cache found: {filename}")
        return cache_path

    #else download
    url = f"{BASE_URL}{year}/{month}/{filename}"
    print(f"Downloading: {filename}...")

    try:
        r = requests.get(url, timeout=120, stream=True)
        if r.status_code == 200:
            with open(cache_path, "wb") as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
            size = os.path.getsize(cache_path) / (1024*1024)
            print(f"Downloaded: {filename} ({size:.1f} MB)")
            return cache_path
        else:
            print(f"Not found on server: {filename}")
            return None
    except Exception as e:
        print(f"Download error: {e}")
        return None


#chek if already ingested ,Download if needed ,Insert into DB
def fetch_and_ingest(date: datetime):
    from backend.ingest import process_file, is_already_ingested

    filename = date.strftime("%Y%m%d") + "_prof.nc"

    if is_already_ingested(date):
        print(f"Already ingested: {filename}")
        return True

    print(f"Not in DB: {filename} — downloading...")
    filepath = download_file(date)

    if filepath is None:
        print(f"Download failed: {filename}")
        return False

    print(f"Inserting into DB: {filename}")
    process_file(filepath)

    print(f"Ready: {filename}")
    return True



#Date Range Fetch
def fetch_date_range(start_date: datetime, end_date: datetime):
    """
    Fetch all dates in a range
    """
    from datetime import timedelta

    current = start_date
    results = []

    while current <= end_date:
        success = fetch_and_ingest(current)
        results.append({
            'date'   : current.strftime("%Y-%m-%d"),
            'success': success
        })
        current += timedelta(days=1)

    success_count = sum(1 for r in results if r['success'])
    print(f"""
Date Range Complete!
━━━━━━━━━━━━━━━━━━━━━━
Success : {success_count}/{len(results)} dates
""")
    return results

# Test
if __name__ == "__main__":
    fetch_and_ingest(datetime(2024, 6, 15))