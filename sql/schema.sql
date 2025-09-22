-- Health Data Analysis Database Schema
-- This schema supports Apple Health and Freestyle Libre glucose data analysis

-- Create database tables for health data analysis
PRAGMA foreign_keys = ON;

-- Apple Health Records Table
CREATE TABLE IF NOT EXISTS apple_health_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    record_type TEXT NOT NULL,
    source_name TEXT,
    value REAL,
    unit TEXT,
    creation_date DATETIME,
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_health_records_type ON apple_health_records(record_type);
CREATE INDEX IF NOT EXISTS idx_health_records_start_date ON apple_health_records(start_date);
CREATE INDEX IF NOT EXISTS idx_health_records_source ON apple_health_records(source_name);

-- Glucose Readings Table (Freestyle Libre)
CREATE TABLE IF NOT EXISTS glucose_readings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME NOT NULL,
    glucose_value REAL NOT NULL,
    glucose_source TEXT CHECK(glucose_source IN ('historic', 'scan', 'fingerstick')),
    glucose_rate_change REAL,
    glucose_trend TEXT CHECK(glucose_trend IN ('rising_fast', 'rising', 'stable', 'falling', 'falling_fast')),
    glucose_range TEXT CHECK(glucose_range IN ('very_low', 'low', 'normal', 'high', 'very_high')),
    serial_number TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for glucose data
CREATE INDEX IF NOT EXISTS idx_glucose_timestamp ON glucose_readings(timestamp);
CREATE INDEX IF NOT EXISTS idx_glucose_range ON glucose_readings(glucose_range);
CREATE INDEX IF NOT EXISTS idx_glucose_source ON glucose_readings(glucose_source);

-- Workout Records Table
CREATE TABLE IF NOT EXISTS workout_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workout_type TEXT NOT NULL,
    duration REAL,
    duration_unit TEXT,
    total_distance REAL,
    total_distance_unit TEXT,
    total_energy_burned REAL,
    total_energy_burned_unit TEXT,
    source_name TEXT,
    creation_date DATETIME,
    start_date DATETIME NOT NULL,
    end_date DATETIME,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for workouts
CREATE INDEX IF NOT EXISTS idx_workout_start_date ON workout_records(start_date);
CREATE INDEX IF NOT EXISTS idx_workout_type ON workout_records(workout_type);

-- Merged Health Data Table (for analysis)
CREATE TABLE IF NOT EXISTS merged_health_data (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    health_timestamp DATETIME NOT NULL,
    glucose_timestamp DATETIME NOT NULL,
    time_diff_minutes REAL,
    
    -- Health metrics
    health_record_type TEXT,
    health_value REAL,
    health_unit TEXT,
    health_source TEXT,
    
    -- Glucose metrics
    glucose_value REAL NOT NULL,
    glucose_source TEXT,
    glucose_range TEXT,
    glucose_trend TEXT,
    
    -- Contextual features
    hour INTEGER,
    day_of_week INTEGER,
    is_weekend BOOLEAN,
    is_night BOOLEAN,
    is_morning BOOLEAN,
    is_afternoon BOOLEAN,
    is_evening BOOLEAN,
    likely_meal_time BOOLEAN,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for merged data analysis
CREATE INDEX IF NOT EXISTS idx_merged_health_timestamp ON merged_health_data(health_timestamp);
CREATE INDEX IF NOT EXISTS idx_merged_glucose_timestamp ON merged_health_data(glucose_timestamp);
CREATE INDEX IF NOT EXISTS idx_merged_health_type ON merged_health_data(health_record_type);
CREATE INDEX IF NOT EXISTS idx_merged_glucose_range ON merged_health_data(glucose_range);
CREATE INDEX IF NOT EXISTS idx_merged_hour ON merged_health_data(hour);
CREATE INDEX IF NOT EXISTS idx_merged_day_of_week ON merged_health_data(day_of_week);

-- Time-in-Range Statistics Table
CREATE TABLE IF NOT EXISTS glucose_statistics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    date_start DATE NOT NULL,
    date_end DATE NOT NULL,
    total_readings INTEGER,
    time_very_low_percent REAL,
    time_low_percent REAL,
    time_in_range_percent REAL,
    time_high_percent REAL,
    time_very_high_percent REAL,
    average_glucose REAL,
    glucose_std REAL,
    coefficient_variation REAL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Create index for statistics
CREATE INDEX IF NOT EXISTS idx_glucose_stats_date ON glucose_statistics(date_start, date_end);

-- Data Quality Tracking Table
CREATE TABLE IF NOT EXISTS data_quality_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    table_name TEXT NOT NULL,
    check_name TEXT NOT NULL,
    check_result TEXT CHECK(check_result IN ('PASS', 'FAIL', 'WARNING')),
    details TEXT,
    record_count INTEGER,
    checked_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Views for common queries

-- View for daily glucose summaries
CREATE VIEW IF NOT EXISTS daily_glucose_summary AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as reading_count,
    AVG(glucose_value) as avg_glucose,
    MIN(glucose_value) as min_glucose,
    MAX(glucose_value) as max_glucose,
    STDEV(glucose_value) as glucose_std,
    SUM(CASE WHEN glucose_range = 'very_low' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_very_low_pct,
    SUM(CASE WHEN glucose_range = 'low' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_low_pct,
    SUM(CASE WHEN glucose_range = 'normal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_in_range_pct,
    SUM(CASE WHEN glucose_range = 'high' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_high_pct,
    SUM(CASE WHEN glucose_range = 'very_high' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_very_high_pct
FROM glucose_readings 
GROUP BY DATE(timestamp)
ORDER BY date;

-- View for hourly glucose patterns
CREATE VIEW IF NOT EXISTS hourly_glucose_patterns AS
SELECT 
    CAST(strftime('%H', timestamp) AS INTEGER) as hour,
    COUNT(*) as reading_count,
    AVG(glucose_value) as avg_glucose,
    STDEV(glucose_value) as glucose_std,
    SUM(CASE WHEN glucose_range = 'normal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as time_in_range_pct
FROM glucose_readings 
GROUP BY hour
ORDER BY hour;

-- View for workout impact on glucose
CREATE VIEW IF NOT EXISTS workout_glucose_impact AS
SELECT 
    w.workout_type,
    w.start_date as workout_start,
    w.duration,
    w.total_energy_burned,
    
    -- Pre-workout glucose (30 minutes before)
    (SELECT AVG(g1.glucose_value) 
     FROM glucose_readings g1 
     WHERE g1.timestamp BETWEEN datetime(w.start_date, '-30 minutes') 
                            AND w.start_date) as pre_workout_glucose,
    
    -- Post-workout glucose (2 hours after)
    (SELECT AVG(g2.glucose_value) 
     FROM glucose_readings g2 
     WHERE g2.timestamp BETWEEN w.end_date 
                            AND datetime(w.end_date, '+2 hours')) as post_workout_glucose
FROM workout_records w
WHERE w.start_date >= (SELECT MIN(timestamp) FROM glucose_readings)
  AND w.end_date <= (SELECT MAX(timestamp) FROM glucose_readings);

-- Add any additional constraints or triggers

-- Trigger to automatically update glucose ranges when inserting new readings
CREATE TRIGGER IF NOT EXISTS update_glucose_range
    AFTER INSERT ON glucose_readings
    WHEN NEW.glucose_range IS NULL
BEGIN
    UPDATE glucose_readings 
    SET glucose_range = CASE 
        WHEN NEW.glucose_value < 54 THEN 'very_low'
        WHEN NEW.glucose_value < 70 THEN 'low'
        WHEN NEW.glucose_value <= 180 THEN 'normal'
        WHEN NEW.glucose_value <= 250 THEN 'high'
        ELSE 'very_high'
    END
    WHERE id = NEW.id;
END;
