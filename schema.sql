-- TV Show Intervals Demo Schema
-- This schema creates tables and triggers to automatically calculate
-- 15-minute intervals for TV programs

-- Drop existing objects if they exist (for clean setup)
DROP TRIGGER IF EXISTS trigger_update_program_intervals ON programs;
DROP FUNCTION IF EXISTS update_program_intervals();
DROP FUNCTION IF EXISTS count_15min_intervals(TIME, TIME);
DROP TABLE IF EXISTS program_intervals;
DROP TABLE IF EXISTS programs;

-- Programs table: stores program name, start time, and end time
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(program_name, start_time, end_time)
);

-- Program intervals table: stores calculated 15-minute intervals
CREATE TABLE program_intervals (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    interval_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(program_name)
);

-- Function to count 15-minute intervals
-- Handles overnight programs (crossing midnight)
-- Rules:
-- - If start == end → 0 intervals
-- - If duration < 15 minutes → 0 intervals  
-- - If duration is exactly N*15 minutes → N intervals
-- - Handles midnight crossing correctly
CREATE OR REPLACE FUNCTION count_15min_intervals(start_time TIME, end_time TIME)
RETURNS INTEGER AS $$
DECLARE
    duration_minutes INTEGER;
BEGIN
    -- Handle same start and end time
    IF start_time = end_time THEN
        RETURN 0;
    END IF;
    
    -- Calculate duration in minutes
    -- If end_time < start_time, program crosses midnight
    IF end_time < start_time THEN
        -- Duration = minutes until midnight + minutes from midnight to end
        duration_minutes := EXTRACT(EPOCH FROM (TIME '24:00:00' - start_time)) / 60 + 
                           EXTRACT(EPOCH FROM end_time) / 60;
    ELSE
        -- Normal case: end_time >= start_time
        duration_minutes := EXTRACT(EPOCH FROM (end_time - start_time)) / 60;
    END IF;
    
    -- Return number of complete 15-minute intervals
    -- If duration < 15 minutes, this returns 0
    RETURN duration_minutes / 15;
END;
$$ LANGUAGE plpgsql;

-- Trigger function to automatically update program_intervals table
CREATE OR REPLACE FUNCTION update_program_intervals()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'DELETE' THEN
        -- Remove from program_intervals when program is deleted
        DELETE FROM program_intervals WHERE program_name = OLD.program_name;
        RETURN OLD;
    ELSIF TG_OP = 'INSERT' THEN
        -- Insert or update program_intervals when new program is added
        INSERT INTO program_intervals (program_name, interval_count)
        VALUES (NEW.program_name, count_15min_intervals(NEW.start_time, NEW.end_time))
        ON CONFLICT (program_name) 
        DO UPDATE SET 
            interval_count = count_15min_intervals(NEW.start_time, NEW.end_time),
            updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    ELSIF TG_OP = 'UPDATE' THEN
        -- Update program_intervals when program is modified
        -- Handle program name changes
        IF OLD.program_name != NEW.program_name THEN
            -- Remove old entry
            DELETE FROM program_intervals WHERE program_name = OLD.program_name;
        END IF;
        
        -- Insert or update with new values
        INSERT INTO program_intervals (program_name, interval_count)
        VALUES (NEW.program_name, count_15min_intervals(NEW.start_time, NEW.end_time))
        ON CONFLICT (program_name) 
        DO UPDATE SET 
            interval_count = count_15min_intervals(NEW.start_time, NEW.end_time),
            updated_at = CURRENT_TIMESTAMP;
        RETURN NEW;
    END IF;
    
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger that fires on INSERT, UPDATE, DELETE
CREATE TRIGGER trigger_update_program_intervals
    AFTER INSERT OR UPDATE OR DELETE ON programs
    FOR EACH ROW
    EXECUTE FUNCTION update_program_intervals();

-- Create indexes for better performance
CREATE INDEX idx_programs_name ON programs(program_name);
CREATE INDEX idx_programs_times ON programs(start_time, end_time);
CREATE INDEX idx_intervals_name ON program_intervals(program_name);

-- Add some helpful comments
COMMENT ON TABLE programs IS 'TV programs with their daily time slots';
COMMENT ON TABLE program_intervals IS 'Automatically calculated 15-minute intervals for each program';
COMMENT ON FUNCTION count_15min_intervals(TIME, TIME) IS 'Calculates number of 15-minute intervals, handling overnight programs';
COMMENT ON TRIGGER trigger_update_program_intervals ON programs IS 'Automatically maintains program_intervals table when programs change';

-- =============================================================================
-- pgTAP Testing Extension and Helper Functions
-- =============================================================================

-- Enable pgTAP extension for database testing
-- This allows us to run TAP-format tests directly in PostgreSQL
CREATE EXTENSION IF NOT EXISTS pgtap;

-- Create a test schema for organizing test functions
CREATE SCHEMA IF NOT EXISTS tests;

-- Grant permissions for test execution
GRANT USAGE ON SCHEMA tests TO demo;
GRANT CREATE ON SCHEMA tests TO demo;

-- Helper function for comprehensive data integrity verification
CREATE OR REPLACE FUNCTION tests.verify_data_integrity()
RETURNS TABLE(
    test_name TEXT,
    result BOOLEAN,
    details TEXT
) AS $$
BEGIN
    -- Test 1: Program count consistency
    RETURN QUERY
    SELECT 
        'program_count_consistency'::TEXT,
        (SELECT COUNT(*) FROM programs) = (SELECT COUNT(*) FROM program_intervals),
        format('Programs: %s, Intervals: %s', 
               (SELECT COUNT(*) FROM programs), 
               (SELECT COUNT(*) FROM program_intervals))::TEXT;
    
    -- Test 2: No orphaned intervals
    RETURN QUERY
    SELECT 
        'no_orphaned_intervals'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM program_intervals pi 
            LEFT JOIN programs p ON pi.program_name = p.program_name 
            WHERE p.program_name IS NULL
        ),
        format('Orphaned intervals: %s', 
               (SELECT COUNT(*) FROM program_intervals pi 
                LEFT JOIN programs p ON pi.program_name = p.program_name 
                WHERE p.program_name IS NULL))::TEXT;
    
    -- Test 3: No missing intervals
    RETURN QUERY
    SELECT 
        'no_missing_intervals'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM programs p 
            LEFT JOIN program_intervals pi ON p.program_name = pi.program_name 
            WHERE pi.program_name IS NULL
        ),
        format('Missing intervals: %s', 
               (SELECT COUNT(*) FROM programs p 
                LEFT JOIN program_intervals pi ON p.program_name = pi.program_name 
                WHERE pi.program_name IS NULL))::TEXT;

    -- Test 4: Interval calculation accuracy
    RETURN QUERY
    SELECT 
        'interval_calculation_accuracy'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM programs p
            JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE pi.interval_count != count_15min_intervals(p.start_time, p.end_time)
        ),
        format('Miscalculated intervals: %s', 
               (SELECT COUNT(*) FROM programs p
                JOIN program_intervals pi ON p.program_name = pi.program_name
                WHERE pi.interval_count != count_15min_intervals(p.start_time, p.end_time)))::TEXT;

    -- Test 5: Data quality - no empty program names
    RETURN QUERY
    SELECT 
        'no_empty_program_names'::TEXT,
        NOT EXISTS (
            SELECT 1 FROM programs WHERE program_name IS NULL OR program_name = ''
        ) AND NOT EXISTS (
            SELECT 1 FROM program_intervals WHERE program_name IS NULL OR program_name = ''
        ),
        format('Empty program names - Programs: %s, Intervals: %s', 
               (SELECT COUNT(*) FROM programs WHERE program_name IS NULL OR program_name = ''),
               (SELECT COUNT(*) FROM program_intervals WHERE program_name IS NULL OR program_name = ''))::TEXT;
END;
$$ LANGUAGE plpgsql;

-- Function to get test environment information
CREATE OR REPLACE FUNCTION tests.get_test_environment()
RETURNS TABLE(
    property TEXT,
    value TEXT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 'database_name'::TEXT, current_database()::TEXT
    UNION ALL
    SELECT 'current_user'::TEXT, current_user::TEXT
    UNION ALL
    SELECT 'postgres_version'::TEXT, version()::TEXT
    UNION ALL
    SELECT 'pgtap_version'::TEXT, 
           CASE 
               WHEN EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'pgtap') 
               THEN (SELECT extversion FROM pg_extension WHERE extname = 'pgtap')
               ELSE 'Not installed'
           END
    UNION ALL
    SELECT 'test_timestamp'::TEXT, CURRENT_TIMESTAMP::TEXT
    UNION ALL
    SELECT 'total_programs'::TEXT, (SELECT COUNT(*)::TEXT FROM programs)
    UNION ALL
    SELECT 'total_intervals'::TEXT, (SELECT COUNT(*)::TEXT FROM program_intervals);
END;
$$ LANGUAGE plpgsql;

-- Add comments for the test functions
COMMENT ON FUNCTION tests.verify_data_integrity() IS 'Comprehensive data integrity verification for pgTAP tests';
COMMENT ON FUNCTION tests.get_test_environment() IS 'Provides test environment information for debugging and reporting';
COMMENT ON SCHEMA tests IS 'Schema for organizing pgTAP test functions and utilities';