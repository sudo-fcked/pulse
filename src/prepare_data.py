import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
import os

def ingest_historical_data():
    username = os.environ.get("USER", "swolfkil")
    print(f"Connecting to PostgreSQL as {username}...")
    conn = psycopg2.connect(dbname="pulse", user=username)
    cursor = conn.cursor()

    months = ["04", "05", "06"]
    base_path = "data/raw/MBTA_Bus_Arrival_Departure_Times_2026/MBTA-Bus-Arrival-Departure-Times_2026-{}.csv"

    insert_query = """
        INSERT INTO stop_events (
            service_date, route_id, direction_id, stop_id, time_point_id,
            time_point_order, point_type, standard_type, scheduled, actual,
            scheduled_headway, headway, half_trip_id, delay_min, late, source
        ) VALUES %s
        ON CONFLICT (service_date, route_id, direction_id, stop_id, scheduled)
        DO NOTHING;
    """

    for month in months:
        file_path = base_path.format(month)
        print(f"\nProcessing {file_path}...")

        df = pd.read_csv(file_path, low_memory=False)
        print(f"Loaded {len(df):,} raw rows.")

        # Filter missing actuals
        df = df.dropna(subset=['actual']).copy()

        # Compute delay and filter errors (-30 to +120 minutes)
        sched = pd.to_datetime(df['scheduled'])
        act = pd.to_datetime(df['actual'])
        df['delay_min'] = (act - sched).dt.total_seconds() / 60.0
        df = df[(df['delay_min'] >= -30) & (df['delay_min'] <= 120)].copy()

        df['late'] = df['delay_min'] > 3.0
        df['source'] = 'historical'

        # Convert nullable integer columns to pure Python int or None (prevents NaN errors)
        for col in ['time_point_order', 'scheduled_headway', 'headway']:
            df[col] = df[col].apply(lambda x: int(x) if pd.notnull(x) else None)

        # Replace any remaining NaNs (e.g. half_trip_id) with None across all columns
        df = df.astype(object).where(pd.notnull(df), None)

        cols = [
            'service_date', 'route_id', 'direction_id', 'stop_id', 'time_point_id',
            'time_point_order', 'point_type', 'standard_type', 'scheduled', 'actual',
            'scheduled_headway', 'headway', 'half_trip_id', 'delay_min', 'late', 'source'
        ]

        # Build pure Python tuples
        records = [tuple(row) for row in df[cols].values]

        print(f"Inserting {len(records):,} clean rows into database...")
        execute_values(cursor, insert_query, records, page_size=10000)
        conn.commit()
        print(f"Finished inserting month {month}.")

    cursor.close()
    conn.close()
    print("\nHistorical data ingestion complete.")

if __name__ == "__main__":
    ingest_historical_data()
