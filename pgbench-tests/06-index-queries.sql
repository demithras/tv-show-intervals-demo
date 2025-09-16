-- Index Effectiveness Tests for pgbench
-- Tests specific queries that should benefit from indexes

\set random_category random(1, 10)
\set random_channel random(1, 500)
\set random_day random(1, 7)
\set random_priority random(1, 3)

-- Choose random query type
\set query_type random(1, 4)

-- Query 1: Category filter (should use idx_programs_category)
SELECT * FROM programs 
WHERE category = 'Sports' AND :query_type = 1;

-- Query 2: Channel filter (should use idx_programs_channel)
SELECT * FROM programs 
WHERE channel_id = :random_channel AND :query_type = 2;

-- Query 3: Day filter (should use idx_programs_day)
SELECT * FROM programs 
WHERE day_of_week = :random_day AND :query_type = 3;

-- Query 4: Composite index test (should use idx_programs_composite)
SELECT * FROM programs 
WHERE channel_id = :random_channel 
  AND day_of_week = :random_day 
  AND start_time >= '18:00' 
  AND :query_type = 4;