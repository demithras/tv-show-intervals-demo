-- pgTAP Installation Script for Docker PostgreSQL Container
-- This script is executed during Docker container initialization
-- to install the pgTAP extension for database testing

-- Connect to the demo database
\c demo;

-- Install pgTAP extension
-- Note: This requires the postgresql-contrib package to be installed
-- which should be available in most PostgreSQL Docker images
CREATE EXTENSION IF NOT EXISTS pgtap;

-- Verify installation and show version
DO $$
DECLARE
    pgtap_version TEXT;
BEGIN
    SELECT extversion INTO pgtap_version 
    FROM pg_extension 
    WHERE extname = 'pgtap';
    
    IF pgtap_version IS NOT NULL THEN
        RAISE NOTICE 'pgTAP extension installed successfully - Version: %', pgtap_version;
    ELSE
        RAISE EXCEPTION 'pgTAP extension installation failed';
    END IF;
END $$;

-- Grant necessary permissions for test execution
-- Ensure the demo user can use pgTAP functions
GRANT USAGE ON SCHEMA public TO demo;

-- Create a simple test to verify pgTAP is working
-- This will be displayed during container startup
SELECT 'pgTAP installation verification' as test_name, 
       CASE 
           WHEN (SELECT plan(1)) IS NOT NULL AND ok(true, 'pgTAP is working correctly') IS NOT NULL 
           THEN 'PASSED' 
           ELSE 'FAILED' 
       END as result;

-- Show available pgTAP functions for debugging
\echo 'Available pgTAP test functions:'
SELECT proname as function_name
FROM pg_proc 
WHERE pronamespace = (SELECT oid FROM pg_namespace WHERE nspname = 'public')
  AND proname LIKE '%tap%' OR proname IN ('plan', 'ok', 'is', 'finish')
ORDER BY proname
LIMIT 10;

\echo 'pgTAP installation completed successfully!';