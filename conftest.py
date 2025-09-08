"""
Pytest configuration and fixtures for TV show intervals testing.
Provides database connection, cleanup, and test isolation.
"""

import pytest
import psycopg2
from psycopg2.extras import RealDictCursor
import time
import os
from urllib.parse import urlparse


@pytest.fixture(scope="session")
def db_connection():
    """
    Create a database connection for the test session.
    Retries connection in case the database is still starting up.
    Uses DATABASE_URL environment variable if available,
    otherwise uses individual environment variables or defaults.
    """
    connection = None
    max_retries = 10
    retry_delay = 2
    
    # Check if DATABASE_URL is provided (for Neon integration)
    database_url = os.getenv("DATABASE_URL")
    
    if database_url:
        # Parse the DATABASE_URL
        parsed = urlparse(database_url)
        db_host = parsed.hostname
        db_port = parsed.port or 5432
        db_name = parsed.path.lstrip('/')
        db_user = parsed.username
        db_password = parsed.password
    else:
        # Get connection details from individual environment variables or use defaults
        db_host = os.getenv("DB_HOST", "localhost")
        db_port = int(os.getenv("DB_PORT", "5432"))
        db_name = os.getenv("DB_NAME", "demo")
        db_user = os.getenv("DB_USER", "demo")
        db_password = os.getenv("DB_PASSWORD", "demo")
    
    for attempt in range(max_retries):
        try:
            connection = psycopg2.connect(
                host=db_host,
                database=db_name,
                user=db_user, 
                password=db_password,
                port=db_port,
                cursor_factory=RealDictCursor
            )
            # Set to autocommit mode to avoid transaction issues
            connection.autocommit = True
            
            # Test the connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
            break
        except psycopg2.OperationalError as e:
            if attempt < max_retries - 1:
                print(f"Database connection attempt {attempt + 1} failed, retrying in {retry_delay}s...")
                time.sleep(retry_delay)
            else:
                raise Exception(f"Could not connect to database after {max_retries} attempts: {e}")
    
    if connection:
        yield connection
        connection.close()
    else:
        raise Exception("Failed to establish database connection")


@pytest.fixture(scope="function")
def db_cursor(db_connection):
    """
    Provide a database cursor for each test.
    Each test gets a clean database state.
    """
    with db_connection.cursor() as cursor:
        # Clear existing data before each test
        cursor.execute("DELETE FROM program_intervals")
        cursor.execute("DELETE FROM programs")
        
        yield cursor
        
        # Clean up after test
        cursor.execute("DELETE FROM program_intervals")
        cursor.execute("DELETE FROM programs")


@pytest.fixture(scope="function")
def clean_database(db_cursor):
    """
    Ensure database is clean before and after each test.
    This fixture provides explicit cleanup control.
    """
    # Clean before test
    db_cursor.execute("DELETE FROM program_intervals")
    db_cursor.execute("DELETE FROM programs")
    
    yield db_cursor
    
    # Clean after test
    db_cursor.execute("DELETE FROM program_intervals")
    db_cursor.execute("DELETE FROM programs")


def get_program_intervals(cursor, program_name=None):
    """
    Helper function to retrieve program intervals from the database.
    
    Args:
        cursor: Database cursor
        program_name: Optional program name to filter by
        
    Returns:
        List of dictionaries with program interval data
    """
    if program_name:
        cursor.execute(
            "SELECT program_name, interval_count FROM program_intervals WHERE program_name = %s",
            (program_name,)
        )
    else:
        cursor.execute("SELECT program_name, interval_count FROM program_intervals ORDER BY program_name")
    
    return cursor.fetchall()


def get_programs(cursor, program_name=None):
    """
    Helper function to retrieve programs from the database.
    
    Args:
        cursor: Database cursor
        program_name: Optional program name to filter by
        
    Returns:
        List of dictionaries with program data
    """
    if program_name:
        cursor.execute(
            "SELECT program_name, start_time, end_time FROM programs WHERE program_name = %s",
            (program_name,)
        )
    else:
        cursor.execute("SELECT program_name, start_time, end_time FROM programs ORDER BY program_name")
    
    return cursor.fetchall()


def insert_program(cursor, program_name, start_time, end_time):
    """
    Helper function to insert a program into the database.
    
    Args:
        cursor: Database cursor
        program_name: Name of the program
        start_time: Start time (string format like '09:00' or '09:00:30')
        end_time: End time (string format like '10:30' or '10:30:45')
    """
    cursor.execute(
        "INSERT INTO programs (program_name, start_time, end_time) VALUES (%s, %s, %s)",
        (program_name, start_time, end_time)
    )