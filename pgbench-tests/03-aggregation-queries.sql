-- Aggregation Performance Tests for pgbench
-- Tests complex GROUP BY and aggregate functions

\set random_channel random(1, 500)

-- Choose random query type
\set query_type random(1, 5)

-- Query 1: Category statistics with intervals
SELECT 
    category,
    AVG(interval_count) as avg_intervals,
    MAX(interval_count) as max_intervals,
    MIN(interval_count) as min_intervals,
    COUNT(*) as program_count
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE p.category IS NOT NULL AND 1 = (:query_type % 5) + 1
GROUP BY category 
ORDER BY avg_intervals DESC;

-- Query 2: Channel-day analysis (top 100)
SELECT 
    channel_id,
    day_of_week,
    COUNT(*) as program_count,
    SUM(interval_count) as total_intervals,
    AVG(interval_count) as avg_intervals
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE p.channel_id IS NOT NULL AND p.day_of_week IS NOT NULL AND 2 = (:query_type % 5) + 1
GROUP BY channel_id, day_of_week 
HAVING COUNT(*) > 5
ORDER BY total_intervals DESC 
LIMIT 100;

-- Query 3: Hourly program distribution with duration
SELECT 
    EXTRACT(HOUR FROM start_time) as hour,
    COUNT(*) as programs_starting,
    AVG(interval_count) as avg_duration,
    COUNT(DISTINCT category) as unique_categories
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE 3 = (:query_type % 5) + 1
GROUP BY EXTRACT(HOUR FROM start_time) 
ORDER BY hour;

-- Query 4: Category-priority cross-analysis
SELECT 
    category,
    priority,
    COUNT(*) as program_count,
    AVG(interval_count) as avg_intervals,
    STDDEV(interval_count) as stddev_intervals
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE p.category IS NOT NULL AND p.priority IS NOT NULL AND 4 = (:query_type % 5) + 1
GROUP BY category, priority
ORDER BY category, priority;

-- Query 5: Overnight programs by day of week
SELECT 
    day_of_week,
    COUNT(CASE WHEN start_time > end_time THEN 1 END) as overnight_programs,
    COUNT(*) as total_programs,
    ROUND(100.0 * COUNT(CASE WHEN start_time > end_time THEN 1 END) / COUNT(*), 2) as overnight_percentage
FROM programs
WHERE day_of_week IS NOT NULL AND 5 = (:query_type % 5) + 1
GROUP BY day_of_week
ORDER BY day_of_week;