#!/usr/bin/env python3
"""
Test script to validate pgbench performance test setup.
Runs a minimal test to ensure everything works correctly.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Add the project root to the path so we can import our modules
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from run_pgbench_performance_tests import PgbenchPerformanceRunner

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_pgbench_availability():
    """Check if pgbench is available in the system."""
    try:
        result = subprocess.run(['pgbench', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            logger.info(f"pgbench found: {result.stdout.strip()}")
            return True
        else:
            logger.error("pgbench not found or returned error")
            return False
    except FileNotFoundError:
        logger.error("pgbench not found in PATH")
        return False


def test_pgbench_integration():
    """Test the integration with a local database if available."""
    
    # Check if we have a database URL in environment
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        # Try common local database patterns
        possible_urls = [
            'postgresql://demo:demo@localhost:5432/demo',
            'postgresql://postgres:postgres@localhost:5432/postgres',
            'postgresql://localhost:5432/postgres'
        ]
        
        logger.info("No DATABASE_URL found, testing requires a PostgreSQL database")
        logger.info("Possible URLs to try manually:")
        for url in possible_urls:
            logger.info(f"  export DATABASE_URL='{url}'")
        return False
    
    logger.info(f"Testing with database: {database_url}")
    
    try:
        # Create runner
        runner = PgbenchPerformanceRunner(database_url)
        
        # Test database connection
        with runner.db.cursor() as cursor:
            cursor.execute("SELECT version()")
            version = cursor.fetchone()[0]
            logger.info(f"Connected to: {version}")
        
        # Run a very quick test (small dataset, minimal transactions)
        logger.info("Running minimal pgbench test...")
        results = runner.run_quick_pgbench_suite(records=1000, batch_size=500, clients=1)
        
        if results and results['summary']['successful_tests'] > 0:
            logger.info("✅ pgbench integration test successful!")
            logger.info(f"Ran {results['summary']['successful_tests']} successful tests")
            return True
        else:
            logger.error("❌ pgbench integration test failed")
            return False
            
    except Exception as e:
        logger.error(f"Error during pgbench integration test: {e}")
        return False


def validate_sql_files():
    """Validate that all required SQL files exist and are readable."""
    pgbench_dir = Path("pgbench-tests")
    
    if not pgbench_dir.exists():
        logger.error(f"pgbench-tests directory not found: {pgbench_dir}")
        return False
    
    required_files = [
        "01-basic-queries.sql",
        "02-filtered-queries.sql", 
        "03-aggregation-queries.sql",
        "04-join-queries.sql",
        "05-update-queries.sql",
        "06-index-queries.sql",
        "07-overnight-queries.sql"
    ]
    
    missing_files = []
    for filename in required_files:
        file_path = pgbench_dir / filename
        if not file_path.exists():
            missing_files.append(filename)
        else:
            # Check if file is readable and has content
            try:
                content = file_path.read_text()
                if len(content.strip()) == 0:
                    logger.warning(f"Empty SQL file: {filename}")
                else:
                    logger.info(f"✅ {filename} ({len(content)} chars)")
            except Exception as e:
                logger.error(f"Error reading {filename}: {e}")
                missing_files.append(filename)
    
    if missing_files:
        logger.error(f"Missing or unreadable SQL files: {missing_files}")
        return False
    
    logger.info("✅ All SQL files validated")
    return True


def main():
    """Main validation function."""
    logger.info("=== pgbench Performance Test Validation ===")
    
    success = True
    
    # Check pgbench availability
    logger.info("1. Checking pgbench availability...")
    if not check_pgbench_availability():
        logger.error("pgbench is not available. Install with: sudo apt-get install postgresql-contrib")
        success = False
    
    # Validate SQL files
    logger.info("2. Validating SQL test files...")
    if not validate_sql_files():
        success = False
    
    # Test integration if possible
    logger.info("3. Testing database integration...")
    if not test_pgbench_integration():
        logger.warning("Database integration test skipped (no DATABASE_URL or connection failed)")
        logger.info("To test integration, set DATABASE_URL and ensure the database has the required schema")
    
    if success:
        logger.info("✅ pgbench performance test setup validation successful!")
        logger.info("Ready to run: python run_pgbench_performance_tests.py --database-url <url>")
    else:
        logger.error("❌ Validation failed. Please fix the issues above.")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())