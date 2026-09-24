CREATE TABLE stop_events (
    service_date DATE,
    route_id VARCHAR(50),
    direction_id VARCHAR(50),
    stop_id VARCHAR(50),
    time_point_id VARCHAR(50),
    time_point_order INT,
    point_type VARCHAR(50),
    standard_type VARCHAR(50),
    scheduled TIMESTAMP,
    actual TIMESTAMP,
    scheduled_headway INT,
    headway INT,
    half_trip_id VARCHAR(100),
    source VARCHAR(50)
);
