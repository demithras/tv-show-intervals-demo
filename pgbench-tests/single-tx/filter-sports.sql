-- Single Transaction Query: Sports category filter
-- Direct equivalent to Python "Category filter (should use idx_programs_category)" test

SELECT * FROM programs 
WHERE category = 'Sports';