import os
import sys
import datetime
import requests
import psycopg2
from psycopg2.extras import execute_values

DB_NAME = "pulse"
DB_USER = os.environ.get("USER", "swolfkil")
API_BASE = "https://api-v3.mbta.com"
LOG_FILE = "pull_daily.log"

def get_db_connection():
    return psycopg2.connect(dbname=DB_NAME, user=DB_USER)

def get_historical_timepoints(cursor):
    """Retrieve distinct timepoint keys from historical data."""
    print("Loading historical timepoints from stop_events...")
    cursor.execute("""
        SELECT DISTINCT route_id, direction_id, stop_id
        FROM stop_events
        WHERE source = 'historical';
    """)
    timepoints = set(cursor.fetchall())
    print(f"Loaded {len(timepoints):,} unique historical timepoints.")
    return timepoints

def build_route_map():
    """Build a bidirectional map between API route IDs and file route IDs."""
    url = f"{API_BASE}/routes?filter[type]=3"
    resp = requests.get(url, timeout=30)
    resp.raise_for_status()
    routes_data = resp.json().get("data", [])

    api_to_file = {}
    file_to_api = {}

    for r in routes_data:
        api_id = r["id"]
        short_name = r.get("attributes", {}).get("short_name", api_id)

        # File convention zero-pads single digits: '1' -> '01'
        file_id = short_name.zfill(2) if short_name.isdigit() else short_name

        api_to_file[api_id] = file_id
        file_to_api[file_id] = api_id

    return api_to_file, file_to_api

def run_daily_pull(target_date=None):
    if target_date is None:
        target_date = datetime.date.today().strftime("%Y-%m-%d")

    print(f"Starting daily schedule pull for service_date: {target_date}")

    conn = get_db_connection()
    cursor = conn.cursor()

    historical_timepoints = get_historical_timepoints(cursor)
    api_to_file, file_to_api = build_route_map()

    # Get all distinct route_ids present in historical data
    cursor.execute("SELECT DISTINCT route_id FROM stop_events WHERE source = 'historical';")
    distinct_routes = [row[0] for row in cursor.fetchall()]

    total_fetched = 0
    total_kept = 0
    total_inserted = 0

    insert_query = """
        INSERT INTO stop_events (
            service_date, route_id, direction_id, stop_id,
            time_point_order, scheduled, source
        ) VALUES %s
        ON CONFLICT (service_date, route_id, direction_id, stop_id, scheduled)
        DO NOTHING;
    """

    all_records = []

    for file_route_id in distinct_routes:
        # Convert to API route ID
        api_route_id = file_to_api.get(file_route_id, file_route_id.lstrip("0"))

        url = f"{API_BASE}/schedules?filter[route]={api_route_id}&filter[date]={target_date}"
        try:
            resp = requests.get(url, timeout=15)
            if resp.status_code != 200:
                continue
            data = resp.json().get("data", [])
        except Exception as e:
            print(f"Failed pulling route {api_route_id}: {e}")
            continue

        total_fetched += len(data)

        for item in data:
            attrs = item.get("attributes", {})
            rel = item.get("relationships", {})

            # Map direction
            dir_num = attrs.get("direction_id")
            dir_str = "Inbound" if dir_num == 1 else "Outbound"

            # Stop ID
            stop_id = rel.get("stop", {}).get("data", {}).get("id")
            if not stop_id:
                continue

            # Filter against historical timepoints
            if (file_route_id, dir_str, stop_id) not in historical_timepoints:
                continue

            # Scheduled time: departure_time fallback to arrival_time
            sched_str = attrs.get("departure_time") or attrs.get("arrival_time")
            if not sched_str:
                continue

            # Drop timezone offset for wall-clock alignment
            scheduled_ts = sched_str[:19].replace("T", " ")

            # Point order fallback
            stop_seq = attrs.get("stop_sequence")

            record = (
                target_date,
                file_route_id,
                dir_str,
                stop_id,
                stop_seq,
                scheduled_ts,
                "api"
            )
            all_records.append(record)
            total_kept += 1

    print(f"Fetched {total_fetched:,} API records; kept {total_kept:,} timepoint records.")

    if all_records:
        cursor.execute("SELECT count(*) FROM stop_events;")
        count_before = cursor.fetchone()[0]

        execute_values(cursor, insert_query, all_records, page_size=10000)
        conn.commit()

        cursor.execute("SELECT count(*) FROM stop_events;")
        count_after = cursor.fetchone()[0]
        total_inserted = count_after - count_before

    cursor.close()
    conn.close()

    log_line = (
        f"{datetime.datetime.now().isoformat()} | Date: {target_date} | "
        f"Fetched: {total_fetched:,} | Kept: {total_kept:,} | Inserted: {total_inserted:,}\n"
    )
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    print(f"Finished pull: {total_inserted:,} rows inserted.")
    print(f"Log written to {LOG_FILE}: {log_line.strip()}")

if __name__ == "__main__":
    run_daily_pull()
