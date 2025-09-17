-- Filtered Query Performance Tests for pgbench
-- Tests query performance with WHERE clauses and indexes

\set random_channel random(1, 500)
\set random_day random(1, 7)
\set random_priority random(1, 3)
\set channel_start random(1, 450)
\set channel_end (:channel_start + 50)

-- Choose random query type
\set query_type random(1, 7)

-- Query 1: Filter by category (should use idx_programs_category)
SELECT * FROM programs 
WHERE category = 'News' AND 1 = (:query_type % 7) + 1;

-- Query 2: Filter by channel range  
SELECT * FROM programs 
WHERE channel_id BETWEEN :channel_start AND :channel_end AND 2 = (:query_type % 7) + 1;

-- Query 3: Filter by day and priority (composite condition)
SELECT * FROM programs 
WHERE day_of_week = :random_day AND priority = :random_priority AND 3 = (:query_type % 7) + 1;

-- Query 4: Prime time programs (time range filter)
SELECT * FROM programs 
WHERE start_time >= '18:00' AND start_time < '22:00' AND 4 = (:query_type % 7) + 1;

-- Query 5: Sports on specific channel range
SELECT * FROM programs 
WHERE category = 'Sports' AND channel_id BETWEEN :channel_start AND (:channel_start + 100) AND 5 = (:query_type % 7) + 1;

-- Query 6: Movies with high interval count (JOIN with interval table)
SELECT p.*, pi.interval_count 
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE p.category = 'Movies' AND pi.interval_count > 5 AND 6 = (:query_type % 7) + 1;

-- Query 7: Overnight programs
SELECT * FROM programs 
WHERE start_time > end_time AND 7 = (:query_type % 7) + 1;