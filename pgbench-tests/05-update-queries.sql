-- Update Performance Tests for pgbench
-- Tests UPDATE performance and trigger overhead

\set random_channel random(1, 500)
\set random_priority random(1, 3)
\set random_category random(1, 10)
\set channel_start random(1, 450)
\set channel_end (:channel_start + 50)

-- Map random numbers to actual categories
\set category_name 'News'

-- Choose random update type
\set update_type random(1, 4)

-- Update 1: Single program update by program name (requires finding a valid program)
UPDATE programs 
SET priority = :random_priority 
WHERE id = (
    SELECT id FROM programs 
    WHERE channel_id IS NOT NULL 
    ORDER BY RANDOM() 
    LIMIT 1
) AND :update_type = 1;

-- Update 2: Batch update by category
UPDATE programs 
SET priority = :random_priority 
WHERE category = :category_name AND :update_type = 2;

-- Update 3: Batch update by channel range
UPDATE programs 
SET priority = :random_priority 
WHERE channel_id BETWEEN :channel_start AND :channel_end AND :update_type = 3;

-- Update 4: Update start time (triggers interval recalculation)
UPDATE programs 
SET start_time = '19:30' 
WHERE id = (
    SELECT id FROM programs 
    WHERE category = 'Movies' AND start_time != '19:30'
    ORDER BY RANDOM() 
    LIMIT 1
) AND :update_type = 4;