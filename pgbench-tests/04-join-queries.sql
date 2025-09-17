-- JOIN Performance Tests for pgbench
-- Tests JOIN performance between programs and intervals tables

\set random_channel random(1, 500)
\set channel_start random(1, 400)
\set channel_end (:channel_start + 100)

-- Choose random query type
\set query_type random(1, 3)

-- Query 1: Inner join programs-intervals filtered by category
SELECT p.program_name, p.category, pi.interval_count
FROM programs p
INNER JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.category = 'Movies' AND 1 = (:query_type % 3) + 1;

-- Query 2: Left join programs-intervals filtered by channel
SELECT p.*, pi.interval_count
FROM programs p
LEFT JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.channel_id BETWEEN :channel_start AND :channel_end AND 2 = (:query_type % 3) + 1;

-- Query 3: Join with aggregation and HAVING clause
SELECT 
    p.category,
    COUNT(p.program_name) as program_count,
    SUM(pi.interval_count) as total_intervals,
    AVG(pi.interval_count) as avg_intervals_per_program
FROM programs p
INNER JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.category IS NOT NULL AND 3 = (:query_type % 3) + 1
GROUP BY p.category
HAVING SUM(pi.interval_count) > 1000
ORDER BY total_intervals DESC;