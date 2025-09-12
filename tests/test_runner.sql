-- pgTAP Test Runner
-- Executes all data integrity tests and provides structured TAP output
-- This file coordinates the execution of pgTAP tests for CI/CD integration

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

-- Run the main data integrity test suite
\i tests/data_integrity_tests.sql

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