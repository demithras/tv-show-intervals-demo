-- Filtered Query Performance Tests for pgbench
-- Tests query performance with WHERE clauses and indexes

\set random_category random(1, 10)
\set random_channel random(1, 500)
\set random_day random(1, 7)
\set random_priority random(1, 3)
\set channel_start random(1, 450)
\set channel_end (:channel_start + 50)

-- Map random numbers to actual categories
\set category_map_1 'News'
\set category_map_2 'Drama' 
\set category_map_3 'Comedy'
\set category_map_4 'Sports'
\set category_map_5 'Documentary'
\set category_map_6 'Reality'
\set category_map_7 'Kids'
\set category_map_8 'Movies'
\set category_map_9 'Talk Show'
\set category_map_10 'Game Show'

-- Choose random query type
\set query_type random(1, 7)

-- Query 1: Filter by category (should use idx_programs_category)
SELECT * FROM programs 
WHERE category = 'News' AND :query_type = 1;

-- Query 2: Filter by channel range  
SELECT * FROM programs 
WHERE channel_id BETWEEN :channel_start AND :channel_end AND :query_type = 2;

-- Query 3: Filter by day and priority (composite condition)
SELECT * FROM programs 
WHERE day_of_week = :random_day AND priority = :random_priority AND :query_type = 3;

-- Query 4: Prime time programs (time range filter)
SELECT * FROM programs 
WHERE start_time >= '18:00' AND start_time < '22:00' AND :query_type = 4;

-- Query 5: Sports on specific channel range
SELECT * FROM programs 
WHERE category = 'Sports' AND channel_id BETWEEN :channel_start AND (:channel_start + 100) AND :query_type = 5;

-- Query 6: Movies with high interval count (JOIN with interval table)
SELECT p.*, pi.interval_count 
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name 
WHERE p.category = 'Movies' AND pi.interval_count > 5 AND :query_type = 6;

-- Query 7: Overnight programs
SELECT * FROM programs 
WHERE start_time > end_time AND :query_type = 7;