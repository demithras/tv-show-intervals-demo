-- Basic Query Performance Tests for pgbench
-- These are representative queries from the Python test suite

-- Choose random query type (1-7)
\set query_type random(1, 7)

-- Query 1: Count all programs
SELECT COUNT(*) FROM programs WHERE 1 = (:query_type % 7) + 1;

-- Query 2: Count all intervals  
SELECT COUNT(*) FROM program_intervals WHERE 2 = (:query_type % 7) + 1;

-- Query 3: Top programs by intervals
SELECT program_name, interval_count 
FROM program_intervals 
WHERE 3 = (:query_type % 7) + 1
ORDER BY interval_count DESC 
LIMIT 100;

-- Query 4: Programs by category
SELECT category, COUNT(*) 
FROM programs 
WHERE category IS NOT NULL AND 4 = (:query_type % 7) + 1
GROUP BY category 
ORDER BY COUNT(*) DESC;

-- Query 5: Top channels by program count
SELECT channel_id, COUNT(*) 
FROM programs 
WHERE channel_id IS NOT NULL AND 5 = (:query_type % 7) + 1
GROUP BY channel_id 
ORDER BY COUNT(*) DESC 
LIMIT 10;

-- Query 6: Programs by day of week
SELECT day_of_week, COUNT(*) 
FROM programs 
WHERE day_of_week IS NOT NULL AND 6 = (:query_type % 7) + 1
GROUP BY day_of_week 
ORDER BY day_of_week;

-- Query 7: Programs by priority
SELECT priority, COUNT(*) 
FROM programs 
WHERE priority IS NOT NULL AND 7 = (:query_type % 7) + 1
GROUP BY priority 
ORDER BY priority;