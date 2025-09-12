-- pgTAP Test Runner for CI/CD
-- Executes all data integrity tests with embedded test cases
-- Works in both Docker and GitHub Actions environments

\set ON_ERROR_STOP on

-- Ensure we're in the correct database and have necessary extensions
DO $$
BEGIN
    -- Check if pgTAP is available
    IF NOT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgtap') THEN
        RAISE EXCEPTION 'pgTAP extension is not installed. Please install it first.';
    END IF;
    
    -- Check if our core function exists
    IF NOT EXISTS (SELECT 1 FROM pg_proc WHERE proname = 'count_15min_intervals') THEN
        RAISE EXCEPTION 'count_15min_intervals function not found. Please run schema.sql first.';
    END IF;
END $$;

-- Display test environment information
\echo 'pgTAP Data Integrity Test Suite'
\echo '==============================='
\echo ''

-- Show database connection info
SELECT 'Database: ' || current_database() as info
UNION ALL
SELECT 'User: ' || current_user as info  
UNION ALL
SELECT 'Timestamp: ' || CURRENT_TIMESTAMP::text as info;

\echo ''
\echo 'Starting Data Integrity Tests...'
\echo ''

-- ==================== EMBEDDED DATA INTEGRITY TESTS ====================
BEGIN;

-- Load pgTAP extension
SELECT plan(17); -- Total number of tests

-- Test Setup: Ensure we have test data loaded
SELECT lives_ok(
    'SELECT 1 FROM programs LIMIT 1',
    'Test data should be loaded in programs table'
);

SELECT lives_ok(
    'SELECT 1 FROM program_intervals LIMIT 1', 
    'Test data should be loaded in program_intervals table'
);

-- Scenario: All programs from the programs table should exist in the program_intervals table
SELECT is(
    (SELECT COUNT(*) FROM programs),
    (SELECT COUNT(*) FROM program_intervals),
    'Program count in both tables should be equal'
);

-- Test that every program has a corresponding interval entry
SELECT is(
    (SELECT COUNT(p.program_name) 
     FROM programs p 
     LEFT JOIN program_intervals pi ON p.program_name = pi.program_name 
     WHERE pi.program_name IS NULL),
    0::bigint,
    'Every program should have a corresponding entry in program_intervals table'
);

-- Test that all unique programs are represented
SELECT is(
    (SELECT COUNT(DISTINCT p.program_name) FROM programs p),
    (SELECT COUNT(DISTINCT pi.program_name) FROM program_intervals pi),
    'All unique programs should be represented in intervals table'
);

-- Scenario: Program intervals table should not contain orphaned entries
SELECT is(
    (SELECT COUNT(pi.program_name) 
     FROM program_intervals pi 
     LEFT JOIN programs p ON pi.program_name = p.program_name 
     WHERE p.program_name IS NULL),
    0::bigint,
    'No orphaned entries should exist in program_intervals table'
);

-- Test reverse relationship - intervals without programs
SELECT is(
    (SELECT COUNT(*) FROM program_intervals pi
     WHERE NOT EXISTS (
         SELECT 1 FROM programs p WHERE p.program_name = pi.program_name
     )),
    0::bigint,
    'Every interval entry should have a corresponding program'
);

-- Scenario: Verify no gaps in the schedule coverage
-- Test that we have programs covering time periods
SELECT ok(
    (SELECT COUNT(*) FROM programs) > 0,
    'Schedule should have programs covering time periods'
);

-- Test that we have a reasonable number of programs (not empty dataset)
SELECT ok(
    (SELECT COUNT(*) FROM programs) >= 10,
    'Schedule should have adequate program coverage (at least 10 programs)'
);

-- Test for potential overlapping programs within the same time
-- This checks if we have programs that start and end at exactly the same time (which might indicate data issues)
SELECT is(
    (SELECT COUNT(*) FROM (
        SELECT p1.program_name
        FROM programs p1
        JOIN programs p2 ON p1.program_name != p2.program_name
        WHERE p1.start_time = p2.start_time AND p1.end_time = p2.end_time
    ) duplicates),
    0::bigint,
    'No programs should have identical start and end times'
);

-- Scenario: Program names should not be empty or null
SELECT is(
    (SELECT COUNT(*) FROM programs WHERE program_name IS NULL OR program_name = '' OR trim(program_name) = ''),
    0::bigint,
    'No program names should be empty or null in programs table'
);

SELECT is(
    (SELECT COUNT(*) FROM program_intervals WHERE program_name IS NULL OR program_name = '' OR trim(program_name) = ''),
    0::bigint,
    'No program names should be empty or null in program_intervals table'
);

-- Scenario: Verify no gaps in the schedule coverage
SELECT is(
    (SELECT COUNT(*) FROM (
        WITH ordered_programs AS (
            SELECT program_name, start_time, end_time,
                   LAG(end_time) OVER (ORDER BY start_time) as prev_end_time
            FROM programs
            ORDER BY start_time
        )
        SELECT * FROM ordered_programs
        WHERE prev_end_time IS NOT NULL 
        AND start_time != prev_end_time
    ) gaps_or_overlaps),
    0::bigint,
    'Schedule should have no gaps or overlaps in coverage'
);

SELECT ok(
    NOT EXISTS (
        SELECT 1 FROM programs p1
        JOIN programs p2 ON p1.program_name != p2.program_name
        WHERE p1.start_time < p2.end_time AND p1.end_time > p2.start_time
    ),
    'Schedule should have no overlapping programs'
);

-- Additional data integrity checks
SELECT ok(
    (SELECT COUNT(*) FROM programs WHERE start_time IS NULL OR end_time IS NULL) = 0,
    'All programs should have valid start and end times'
);

-- Test that interval calculations are consistent with program durations
SELECT ok(
    NOT EXISTS (
        SELECT 1 FROM programs p
        JOIN program_intervals pi ON p.program_name = pi.program_name
        WHERE pi.interval_count != count_15min_intervals(p.start_time, p.end_time)
    ),
    'All interval counts should match the calculated 15-minute intervals'
);

-- Test for data type consistency
SELECT ok(
    (SELECT COUNT(*) FROM program_intervals WHERE interval_count < 0) = 0,
    'All interval counts should be non-negative'
);

SELECT finish();

ROLLBACK;

-- ==================== END EMBEDDED TESTS ====================

\echo ''
\echo 'Test Execution Summary:'
\echo '======================'

-- Provide summary information for verification
SELECT 
    'Total Programs: ' || COUNT(*) as summary 
FROM programs
UNION ALL
SELECT 
    'Total Intervals: ' || COUNT(*) as summary 
FROM program_intervals
UNION ALL
SELECT 
    'Unique Program Names: ' || COUNT(DISTINCT program_name) as summary
FROM programs
UNION ALL
SELECT 
    'Total Calculated Intervals: ' || SUM(interval_count) as summary 
FROM program_intervals;

\echo ''
\echo 'Data Integrity Verification Complete'
\echo '===================================='