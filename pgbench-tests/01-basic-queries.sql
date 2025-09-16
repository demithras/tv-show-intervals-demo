-- Basic Query Performance Tests for pgbench
-- These are representative queries from the Python test suite

\set random_category random(1, 10)
\set random_channel random(1, 500)
\set random_day random(1, 7)
\set random_priority random(1, 3)

-- Choose random query type
\set query_type random(1, 7)

-- Query 1: Count all programs
SELECT COUNT(*) FROM programs
WHERE :query_type = 1;

-- Query 2: Count all intervals  
SELECT COUNT(*) FROM program_intervals
WHERE :query_type = 2;

-- Query 3: Top programs by intervals (with LIMIT to ensure consistent performance)
SELECT program_name, interval_count 
FROM program_intervals 
ORDER BY interval_count DESC 
LIMIT 100
WHERE :query_type = 3;

-- Query 4: Programs by category
SELECT category, COUNT(*) 
FROM programs 
WHERE category IS NOT NULL AND :query_type = 4
GROUP BY category 
ORDER BY COUNT(*) DESC;

-- Query 5: Top channels by program count
SELECT channel_id, COUNT(*) 
FROM programs 
WHERE channel_id IS NOT NULL AND :query_type = 5
GROUP BY channel_id 
ORDER BY COUNT(*) DESC 
LIMIT 10;

-- Query 6: Programs by day of week
SELECT day_of_week, COUNT(*) 
FROM programs 
WHERE day_of_week IS NOT NULL AND :query_type = 6
GROUP BY day_of_week 
ORDER BY day_of_week;

-- Query 7: Programs by priority
SELECT priority, COUNT(*) 
FROM programs 
WHERE priority IS NOT NULL AND :query_type = 7
GROUP BY priority 
ORDER BY priority;