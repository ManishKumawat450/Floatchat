import xarray as xr
import numpy as np
import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# ─────────────────────────────
# Database Connection
# ─────────────────────────────
def get_connection():
    return psycopg2.connect(
        host     = os.getenv("DB_HOST"),
        port     = os.getenv("DB_PORT"),
        dbname   = os.getenv("DB_NAME"),
        user     = os.getenv("DB_USER"),
        password = os.getenv("DB_PASSWORD")
    )

# ─────────────────────────────
# India Region Check
# ─────────────────────────────
def is_india_region(lat, lon):
    return (0 <= lat <= 26) and (55 <= lon <= 101)

# ─────────────────────────────
# Processed Files Tracker
# ─────────────────────────────
PROCESSED_FILE = "data/processed_dates.txt"

def _load_processed_dates() -> set:
    """Load all processed dates into memory — fast lookup"""
    if not os.path.exists(PROCESSED_FILE):
        return set()
    with open(PROCESSED_FILE, 'r') as f:
        return set(line.strip() for line in f if line.strip())

def _mark_file_processed(date_str: str, processed_set: set):
    """Mark date as processed — only if not already there"""
    if date_str not in processed_set:
        os.makedirs("data", exist_ok=True)
        with open(PROCESSED_FILE, 'a') as f:
            f.write(date_str + "\n")
        processed_set.add(date_str)

# ─────────────────────────────
# DB Mein Already Hai?
# ─────────────────────────────
def is_already_ingested(date: datetime) -> bool:
    date_str  = date.strftime("%Y-%m-%d")
    processed = _load_processed_dates()
    if date_str in processed:
        return True
    try:
        conn = get_connection()
        cur  = conn.cursor()
        cur.execute("""
            SELECT COUNT(*) FROM argo_profiles
            WHERE date::date = %s
        """, (date_str,))
        count = cur.fetchone()[0]
        cur.close()
        conn.close()
        return count > 0
    except Exception:
        return False

# ─────────────────────────────
# Single File Process
# ─────────────────────────────
def process_file(filepath):
    print(f"\n📂 Processing: {os.path.basename(filepath)}")

    # Corrupt file check
    try:
        ds = xr.open_dataset(filepath)
    except Exception as e:
        print(f"  Corrupt file — skipping: {e}")
        try:
            os.remove(filepath)
            print(f"  Deleted: {os.path.basename(filepath)}")
        except Exception:
            pass
        return 0

    conn = get_connection()
    cur  = conn.cursor()

    inserted = 0
    skipped  = 0
    n_prof   = ds.sizes['N_PROF']

    for i in range(n_prof):
        try:
            lat = float(ds['LATITUDE'].values[i])
            lon = float(ds['LONGITUDE'].values[i])

            if not is_india_region(lat, lon):
                skipped += 1
                continue

            float_id = ds['PLATFORM_NUMBER'].values[i]
            if isinstance(float_id, bytes):
                float_id = float_id.decode('utf-8').strip()

            date = str(ds['JULD'].values[i])[:19]

            def decode(val):
                if isinstance(val, bytes):
                    return val.decode('utf-8').strip()
                return str(val).strip()

            platform_type = decode(ds['PLATFORM_TYPE'].values[i])
            data_centre   = decode(ds['DATA_CENTRE'].values[i])
            positioning   = decode(ds['POSITIONING_SYSTEM'].values[i])
            project       = decode(ds['PROJECT_NAME'].values[i])

            pres = ds['PRES'].values[i]
            temp = ds['TEMP'].values[i]
            psal = ds['PSAL'].values[i]

            mask = (
                ~np.isnan(pres) &
                ~np.isnan(temp) &
                ~np.isnan(psal)
            )

            pres_clean = pres[mask]
            temp_clean = temp[mask]
            psal_clean = psal[mask]

            if len(pres_clean) == 0:
                skipped += 1
                continue

            for j in range(len(pres_clean)):
                cur.execute("""
                    INSERT INTO argo_profiles
                    (float_id, date, latitude, longitude,
                     pressure, temperature, salinity,
                     data_centre, platform_type,
                     positioning_system, project_name)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                    ON CONFLICT DO NOTHING
                """, (
                    float_id, date, lat, lon,
                    float(pres_clean[j]),
                    float(temp_clean[j]),
                    float(psal_clean[j]),
                    data_centre, platform_type,
                    positioning, project
                ))

            inserted += 1

            cur.execute("""
                INSERT INTO float_metadata
                (float_id, data_centre, platform_type,
                 positioning_system, project_name,
                 first_seen, last_seen, total_profiles)
                VALUES (%s,%s,%s,%s,%s,%s,%s,1)
                ON CONFLICT (float_id) DO UPDATE SET
                    last_seen      = EXCLUDED.last_seen,
                    total_profiles = float_metadata.total_profiles + 1
            """, (
                float_id, data_centre, platform_type,
                positioning, project, date, date
            ))

        except Exception as e:
            print(f"  Error at profile {i}: {e}")
            continue

    conn.commit()
    cur.close()
    conn.close()
    ds.close()

    # Mark as processed — FIXED: ab process_file se bhi mark hoga
    try:
        date_from_file = os.path.basename(filepath)[:8]
        date_str       = f"{date_from_file[:4]}-{date_from_file[4:6]}-{date_from_file[6:8]}"
        processed_set  = _load_processed_dates()
        _mark_file_processed(date_str, processed_set)
    except Exception:
        pass

    print(f"  Inserted : {inserted} floats")
    print(f"  Skipped  : {skipped} floats (non-India)")

    return inserted

# ─────────────────────────────
# Saari Files Process
# ─────────────────────────────
def ingest_all():
    cache_dir = "data/argo_cache"
    files     = sorted([
        f for f in os.listdir(cache_dir)
        if f.endswith('.nc')
    ])

    print(f"Total files: {len(files)}")
    print("Ingestion starting...\n")

    # Ek baar saare processed dates load karo
    processed_set = _load_processed_dates()
    print(f"Already processed: {len(processed_set)} dates — will skip these\n")

    total         = 0
    skipped_files = 0
    new_files     = 0
    start         = datetime.now()

    for filename in files:

        # Filename se date nikalo
        try:
            date_part = filename[:8]
            date_str  = f"{date_part[:4]}-{date_part[4:6]}-{date_part[6:8]}"
        except Exception:
            date_str = ""

        # Already processed? SKIP!
        if date_str and date_str in processed_set:
            print(f"Skipping (already done): {filename}")
            skipped_files += 1
            continue

        # New file — process karo
        new_files += 1
        filepath   = os.path.join(cache_dir, filename)
        inserted   = process_file(filepath)
        total     += inserted

        # Memory mein update karo
        if date_str:
            processed_set.add(date_str)

    elapsed = datetime.now() - start
    print(f"""
Ingestion Complete!
━━━━━━━━━━━━━━━━━━━━
Total files     : {len(files)}
Skipped (done)  : {skipped_files}
Newly processed : {new_files}
Floats inserted : {total}
Time taken      : {elapsed}
""")

if __name__ == "__main__":
    ingest_all()