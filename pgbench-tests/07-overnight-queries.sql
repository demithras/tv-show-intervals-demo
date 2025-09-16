-- Overnight Program Performance Tests for pgbench
-- Tests the overnight program function and calculations

\set random_program random(1, 1000)

-- Choose random query type
\set query_type random(1, 4)

-- Query 1: Find all overnight programs
SELECT * FROM programs 
WHERE start_time > end_time AND :query_type = 1;

-- Query 2: Overnight programs with interval calculations
SELECT p.program_name, p.start_time, p.end_time, pi.interval_count
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.start_time > p.end_time AND :query_type = 2;

-- Query 3: Test the count_15min_intervals function directly with overnight times
SELECT count_15min_intervals('23:30'::time, '00:15'::time) as intervals_overnight_45min
WHERE :query_type = 3;

-- Query 4: Test function with various overnight scenarios
SELECT count_15min_intervals('23:45'::time, '00:30'::time) as intervals_overnight_45min
WHERE :query_type = 4;