import os
import psycopg2
import pandas as pd
import warnings

warnings.filterwarnings('ignore', 'pandas only supports SQLAlchemy')

def create_splits():
    username = os.environ.get("USER", "swolfkil")
    conn = psycopg2.connect(dbname="pulse", user=username)
    
    query = """
        SELECT 
            service_date,
            route_id,
            direction_id,
            stop_id,
            time_point_id,
            time_point_order,
            point_type,
            standard_type,
            scheduled,
            scheduled_headway,
            late
        FROM stop_events
        WHERE source = 'historical' AND late IS NOT NULL
    """
    
    print("Exporting labeled historical dataset from Postgres...")
    df = pd.read_sql_query(query, conn)
    conn.close()
    print(f"Loaded {len(df):,} total labeled records.")

    df['scheduled'] = pd.to_datetime(df['scheduled'])
    df['service_date'] = pd.to_datetime(df['service_date'])
    
    time_delta = df['scheduled'] - pd.to_datetime('1900-01-01')
    df['scheduled'] = df['service_date'] + time_delta
    df = df.sort_values('scheduled').reset_index(drop=True)

    df['day_of_week'] = df['scheduled'].dt.dayofweek
    df['hour'] = df['scheduled'].dt.hour
    df['minute_of_day'] = df['hour'] * 60 + df['scheduled'].dt.minute

    train_df = df[(df['service_date'] >= '2026-04-01') & (df['service_date'] <= '2026-05-31')].copy()
    val_df = df[(df['service_date'] >= '2026-06-01') & (df['service_date'] <= '2026-06-15')].copy()
    test_df = df[(df['service_date'] >= '2026-06-16') & (df['service_date'] <= '2026-06-30')].copy()

    print(f"Train max scheduled: {train_df['scheduled'].max()} | Val min scheduled: {val_df['scheduled'].min()}")
    print(f"Val max scheduled:   {val_df['scheduled'].max()} | Test min scheduled: {test_df['scheduled'].min()}")

    assert train_df['scheduled'].max() < val_df['scheduled'].min(), "Train overlaps with validation split!"
    assert val_df['scheduled'].max() < test_df['scheduled'].min(), "Validation overlaps with test split!"

    os.makedirs("data/splits", exist_ok=True)
    
    train_path = "data/splits/train.parquet"
    val_path = "data/splits/val.parquet"
    test_path = "data/splits/test.parquet"

    train_df.to_parquet(train_path, index=False)
    val_df.to_parquet(val_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print("\nDataset Split Summary:")
    print(f"Train:      {len(train_df):,} rows | Late rate: {train_df['late'].mean()*100:.2f}% -> {train_path}")
    print(f"Validation: {len(val_df):,} rows | Late rate: {val_df['late'].mean()*100:.2f}% -> {val_path}")
    print(f"Test:       {len(test_df):,} rows | Late rate: {test_df['late'].mean()*100:.2f}% -> {test_path}")

if __name__ == "__main__":
    create_splits()
