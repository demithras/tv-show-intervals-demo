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