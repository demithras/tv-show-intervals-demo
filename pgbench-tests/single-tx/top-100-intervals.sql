-- Single Transaction Query: Top 100 programs by intervals
-- Direct equivalent to Python "Top 100 by intervals" test

SELECT program_name, interval_count 
FROM program_intervals 
ORDER BY interval_count DESC 
LIMIT 100;