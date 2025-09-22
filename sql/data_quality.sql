-- Data Quality Validation Queries
-- These queries check data integrity and quality for the health analysis

-- 1. Basic data availability checks
SELECT 'Glucose Data Availability' as check_name,
       COUNT(*) as total_records,
       MIN(timestamp) as earliest_date,
       MAX(timestamp) as latest_date,
       ROUND(JULIANDAY(MAX(timestamp)) - JULIANDAY(MIN(timestamp)), 1) as days_coverage
FROM glucose_readings;

SELECT 'Apple Health Data Availability' as check_name,
       COUNT(*) as total_records,
       MIN(start_date) as earliest_date,
       MAX(start_date) as latest_date,
       COUNT(DISTINCT record_type) as unique_record_types
FROM apple_health_records;

-- 2. Missing value analysis
SELECT 'Glucose Missing Values' as check_name,
       COUNT(*) as total_records,
       SUM(CASE WHEN glucose_value IS NULL THEN 1 ELSE 0 END) as missing_glucose,
       SUM(CASE WHEN timestamp IS NULL THEN 1 ELSE 0 END) as missing_timestamp,
       SUM(CASE WHEN glucose_source IS NULL THEN 1 ELSE 0 END) as missing_source
FROM glucose_readings;

SELECT 'Health Data Missing Values' as check_name,
       COUNT(*) as total_records,
       SUM(CASE WHEN value IS NULL THEN 1 ELSE 0 END) as missing_values,
       SUM(CASE WHEN start_date IS NULL THEN 1 ELSE 0 END) as missing_start_date,
       SUM(CASE WHEN record_type IS NULL THEN 1 ELSE 0 END) as missing_record_type
FROM apple_health_records;

-- 3. Data range validation
SELECT 'Glucose Range Validation' as check_name,
       MIN(glucose_value) as min_glucose,
       MAX(glucose_value) as max_glucose,
       AVG(glucose_value) as avg_glucose,
       SUM(CASE WHEN glucose_value < 20 OR glucose_value > 600 THEN 1 ELSE 0 END) as out_of_range_count,
       SUM(CASE WHEN glucose_value < 20 OR glucose_value > 600 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as out_of_range_percent
FROM glucose_readings;

-- 4. Duplicate detection
SELECT 'Glucose Duplicate Timestamps' as check_name,
       COUNT(*) as total_records,
       COUNT(DISTINCT timestamp) as unique_timestamps,
       COUNT(*) - COUNT(DISTINCT timestamp) as duplicate_count
FROM glucose_readings;

SELECT 'Health Data Duplicates' as check_name,
       COUNT(*) as total_records,
       COUNT(DISTINCT record_type || start_date || COALESCE(value, '')) as unique_records,
       COUNT(*) - COUNT(DISTINCT record_type || start_date || COALESCE(value, '')) as potential_duplicates
FROM apple_health_records;

-- 5. Data consistency checks
SELECT 'Glucose Trend Consistency' as check_name,
       COUNT(*) as total_with_trend,
       SUM(CASE WHEN glucose_trend IN ('rising_fast', 'rising', 'stable', 'falling', 'falling_fast') THEN 1 ELSE 0 END) as valid_trends,
       SUM(CASE WHEN glucose_trend NOT IN ('rising_fast', 'rising', 'stable', 'falling', 'falling_fast') THEN 1 ELSE 0 END) as invalid_trends
FROM glucose_readings 
WHERE glucose_trend IS NOT NULL;

-- 6. Temporal data gaps analysis
WITH glucose_gaps AS (
    SELECT 
        timestamp,
        LAG(timestamp) OVER (ORDER BY timestamp) as prev_timestamp,
        ROUND((JULIANDAY(timestamp) - JULIANDAY(LAG(timestamp) OVER (ORDER BY timestamp))) * 24 * 60, 1) as gap_minutes
    FROM glucose_readings
    ORDER BY timestamp
)
SELECT 'Glucose Data Gaps' as check_name,
       COUNT(*) as total_intervals,
       AVG(gap_minutes) as avg_gap_minutes,
       MAX(gap_minutes) as max_gap_minutes,
       SUM(CASE WHEN gap_minutes > 60 THEN 1 ELSE 0 END) as gaps_over_1_hour,
       SUM(CASE WHEN gap_minutes > 360 THEN 1 ELSE 0 END) as gaps_over_6_hours
FROM glucose_gaps
WHERE prev_timestamp IS NOT NULL;

-- 7. Data distribution analysis
SELECT 'Glucose Range Distribution' as check_name,
       glucose_range,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM glucose_readings), 2) as percentage
FROM glucose_readings
WHERE glucose_range IS NOT NULL
GROUP BY glucose_range
ORDER BY count DESC;

-- 8. Source data quality
SELECT 'Glucose Source Distribution' as check_name,
       glucose_source,
       COUNT(*) as count,
       ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM glucose_readings WHERE glucose_source IS NOT NULL), 2) as percentage
FROM glucose_readings
WHERE glucose_source IS NOT NULL
GROUP BY glucose_source
ORDER BY count DESC;

-- 9. Apple Health record type distribution
SELECT 'Health Record Type Distribution' as check_name,
       record_type,
       COUNT(*) as count,
       MIN(start_date) as first_record,
       MAX(start_date) as last_record
FROM apple_health_records
GROUP BY record_type
ORDER BY count DESC
LIMIT 20;

-- 10. Time coverage overlap between datasets
SELECT 'Data Coverage Overlap' as check_name,
       (SELECT MIN(timestamp) FROM glucose_readings) as glucose_start,
       (SELECT MAX(timestamp) FROM glucose_readings) as glucose_end,
       (SELECT MIN(start_date) FROM apple_health_records) as health_start,
       (SELECT MAX(start_date) FROM apple_health_records) as health_end,
       CASE 
           WHEN (SELECT MIN(timestamp) FROM glucose_readings) > (SELECT MAX(start_date) FROM apple_health_records) OR
                (SELECT MAX(timestamp) FROM glucose_readings) < (SELECT MIN(start_date) FROM apple_health_records)
           THEN 'NO_OVERLAP'
           ELSE 'HAS_OVERLAP'
       END as overlap_status;

-- 11. Data freshness check
SELECT 'Data Freshness' as check_name,
       (SELECT MAX(timestamp) FROM glucose_readings) as latest_glucose,
       (SELECT MAX(start_date) FROM apple_health_records) as latest_health,
       ROUND(JULIANDAY('now') - JULIANDAY((SELECT MAX(timestamp) FROM glucose_readings)), 1) as days_since_glucose,
       ROUND(JULIANDAY('now') - JULIANDAY((SELECT MAX(start_date) FROM apple_health_records)), 1) as days_since_health;

-- 12. Merged data quality assessment
SELECT 'Merged Data Quality' as check_name,
       COUNT(*) as total_merged_records,
       AVG(ABS(time_diff_minutes)) as avg_time_diff_abs,
       MAX(ABS(time_diff_minutes)) as max_time_diff_abs,
       SUM(CASE WHEN ABS(time_diff_minutes) > 30 THEN 1 ELSE 0 END) as records_over_30min_diff
FROM merged_health_data;

-- 13. Generate data quality summary report
WITH quality_summary AS (
    SELECT 
        'Total Glucose Readings' as metric,
        (SELECT COUNT(*) FROM glucose_readings) as value
    UNION ALL
    SELECT 
        'Total Health Records' as metric,
        (SELECT COUNT(*) FROM apple_health_records) as value
    UNION ALL
    SELECT 
        'Glucose Data Days' as metric,
        (SELECT ROUND(JULIANDAY(MAX(timestamp)) - JULIANDAY(MIN(timestamp)), 1) FROM glucose_readings) as value
    UNION ALL
    SELECT 
        'Time in Range %' as metric,
        (SELECT ROUND(SUM(CASE WHEN glucose_range = 'normal' THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 1) FROM glucose_readings) as value
    UNION ALL
    SELECT 
        'Average Glucose' as metric,
        (SELECT ROUND(AVG(glucose_value), 1) FROM glucose_readings) as value
    UNION ALL
    SELECT 
        'Merged Records' as metric,
        (SELECT COUNT(*) FROM merged_health_data) as value
)
SELECT 'Data Quality Summary Report' as report_name, metric, value
FROM quality_summary;
