CREATE TABLE IF NOT EXISTS stop_events (
    service_date DATE,
    route_id VARCHAR(50),
    direction_id VARCHAR(50),
    stop_id VARCHAR(50),
    time_point_id VARCHAR(50),
    time_point_order BIGINT,
    point_type VARCHAR(50),
    standard_type VARCHAR(50),
    scheduled TIMESTAMP,
    actual TIMESTAMP,
    scheduled_headway BIGINT,
    headway BIGINT,
    half_trip_id VARCHAR(100),
    delay_min DOUBLE PRECISION,
    late BOOLEAN,
    source VARCHAR(50),
    CONSTRAINT unique_stop_event UNIQUE (service_date, route_id, direction_id, stop_id, scheduled)
);
