"""
Data loader utility for TV show intervals project.
Provides functionality to load CSV data into the database with proper error handling.
"""

import csv
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from urllib.parse import urlparse
import logging
from typing import List, Dict, Tuple


class DataLoader:
    """Handles loading CSV data into the database with validation and error reporting."""
    
    def __init__(self, connection_string: str = None):
        """
        Initialize the data loader.
        
        Args:
            connection_string: Database connection string. If None, uses environment variables.
        """
        self.connection = None
        self.connection_string = connection_string
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging for data loading operations."""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def connect(self):
        """Establish database connection."""
        if self.connection_string:
            # Parse the connection string
            parsed = urlparse(self.connection_string)
            db_config = {
                'host': parsed.hostname,
                'port': parsed.port or 5432,
                'database': parsed.path.lstrip('/'),
                'user': parsed.username,
                'password': parsed.password
            }
        else:
            # Use environment variables
            db_config = {
                'host': os.getenv("DB_HOST", "localhost"),
                'port': int(os.getenv("DB_PORT", "5432")),
                'database': os.getenv("DB_NAME", "demo"),
                'user': os.getenv("DB_USER", "demo"),
                'password': os.getenv("DB_PASSWORD", "demo")
            }
        
        try:
            self.connection = psycopg2.connect(
                cursor_factory=RealDictCursor,
                **db_config
            )
            self.connection.autocommit = True
            self.logger.info("Database connection established")
        except Exception as e:
            self.logger.error(f"Failed to connect to database: {e}")
            raise
    
    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            self.logger.info("Database connection closed")
    
    def load_csv_to_programs(self, csv_file_path: str, validate_only: bool = False) -> Tuple[List[Dict], List[Dict]]:
        """
        Load CSV data into the programs table.
        
        Args:
            csv_file_path: Path to the CSV file
            validate_only: If True, only validate data without inserting
            
        Returns:
            Tuple of (successful_records, failed_records)
        """
        if not self.connection:
            self.connect()
        
        successful_records = []
        failed_records = []
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # Use DictReader to handle CSV with headers
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # Start at 2 since row 1 is header
                    try:
                        # Validate and clean the data
                        program_name = row.get('program_name', '').strip()
                        start_time = row.get('start_time', '').strip()
                        end_time = row.get('end_time', '').strip()
                        
                        # Basic validation
                        validation_errors = self._validate_program_data(program_name, start_time, end_time)
                        
                        if validation_errors:
                            failed_records.append({
                                'row': row_num,
                                'data': row,
                                'errors': validation_errors
                            })
                            continue
                        
                        if not validate_only:
                            # Insert into database
                            with self.connection.cursor() as cursor:
                                cursor.execute(
                                    "INSERT INTO programs (program_name, start_time, end_time) VALUES (%s, %s, %s)",
                                    (program_name, start_time, end_time)
                                )
                        
                        successful_records.append({
                            'row': row_num,
                            'program_name': program_name,
                            'start_time': start_time,
                            'end_time': end_time
                        })
                        
                    except Exception as e:
                        failed_records.append({
                            'row': row_num,
                            'data': row,
                            'errors': [f"Database error: {str(e)}"]
                        })
        
        except Exception as e:
            self.logger.error(f"Failed to read CSV file {csv_file_path}: {e}")
            raise
        
        self.logger.info(f"Processed {len(successful_records)} successful records, {len(failed_records)} failed records")
        return successful_records, failed_records
    
    def _validate_program_data(self, program_name: str, start_time: str, end_time: str) -> List[str]:
        """
        Validate program data for common integrity issues.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        # Check for missing data
        if not program_name:
            errors.append("Program name is missing or empty")
        if not start_time:
            errors.append("Start time is missing or empty")
        if not end_time:
            errors.append("End time is missing or empty")
        
        # Check for invalid values
        if program_name and (program_name.lower() == 'null' or 'null' in program_name.lower()):
            errors.append("Program name contains NULL value")
        
        # Check program name length
        if program_name and len(program_name) > 255:
            errors.append("Program name exceeds maximum length (255 characters)")
        
        # Validate time format
        if start_time:
            time_errors = self._validate_time_format(start_time, "start_time")
            errors.extend(time_errors)
        
        if end_time:
            time_errors = self._validate_time_format(end_time, "end_time")
            errors.extend(time_errors)
        
        # Check for SQL injection patterns
        dangerous_patterns = ["drop", "delete", "insert", "update", "select", "--", ";"]
        for pattern in dangerous_patterns:
            if pattern in program_name.lower():
                errors.append(f"Program name contains potentially dangerous pattern: {pattern}")
        
        return errors
    
    def _validate_time_format(self, time_str: str, field_name: str) -> List[str]:
        """
        Validate time format.
        
        Returns:
            List of validation error messages
        """
        errors = []
        
        if not time_str or time_str.lower() == 'null':
            errors.append(f"{field_name} contains NULL or empty value")
            return errors
        
        # Check for common invalid patterns
        if ':' not in time_str:
            errors.append(f"{field_name} missing colon separator: {time_str}")
            return errors
        
        # Try to parse as time
        try:
            parts = time_str.split(':')
            if len(parts) < 2:
                errors.append(f"{field_name} invalid format: {time_str}")
                return errors
            
            hours = int(parts[0])
            minutes = int(parts[1])
            
            # Validate hour range (allow 24:00 for midnight)
            if hours < 0 or hours > 24:
                errors.append(f"{field_name} hour out of range (0-24): {hours}")
            
            # Validate minute range
            if minutes < 0 or minutes > 59:
                errors.append(f"{field_name} minute out of range (0-59): {minutes}")
            
            # Special case: 24:XX should only be 24:00
            if hours == 24 and minutes != 0:
                errors.append(f"{field_name} invalid time 24:{minutes:02d}, only 24:00 is valid")
                
        except ValueError:
            errors.append(f"{field_name} contains non-numeric values: {time_str}")
        except Exception as e:
            errors.append(f"{field_name} validation error: {str(e)}")
        
        return errors
    
    def clear_programs_table(self):
        """Clear all data from programs table."""
        if not self.connection:
            self.connect()
        
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM program_intervals")
            cursor.execute("DELETE FROM programs")
        
        self.logger.info("Cleared programs and program_intervals tables")
    
    def get_data_integrity_issues(self) -> Dict:
        """
        Analyze the database for data integrity issues.
        
        Returns:
            Dictionary containing various integrity check results
        """
        if not self.connection:
            self.connect()
        
        issues = {}
        
        with self.connection.cursor() as cursor:
            # Check for programs without corresponding intervals
            cursor.execute("""
                SELECT p.program_name 
                FROM programs p 
                LEFT JOIN program_intervals pi ON p.program_name = pi.program_name 
                WHERE pi.program_name IS NULL
            """)
            issues['programs_without_intervals'] = [row['program_name'] for row in cursor.fetchall()]
            
            # Check for intervals without corresponding programs
            cursor.execute("""
                SELECT pi.program_name 
                FROM program_intervals pi 
                LEFT JOIN programs p ON pi.program_name = p.program_name 
                WHERE p.program_name IS NULL
            """)
            issues['intervals_without_programs'] = [row['program_name'] for row in cursor.fetchall()]
            
            # Check for overlapping programs (same time slots)
            cursor.execute("""
                SELECT p1.program_name as program1, p2.program_name as program2,
                       p1.start_time, p1.end_time
                FROM programs p1 
                JOIN programs p2 ON p1.id < p2.id
                WHERE (p1.start_time < p2.end_time AND p1.end_time > p2.start_time)
                   OR (p1.start_time = p2.start_time AND p1.end_time = p2.end_time)
            """)
            issues['overlapping_programs'] = cursor.fetchall()
            
            # Check for duplicate program names
            cursor.execute("""
                SELECT program_name, COUNT(*) as count
                FROM programs 
                GROUP BY program_name 
                HAVING COUNT(*) > 1
            """)
            issues['duplicate_program_names'] = cursor.fetchall()
            
            # Check for programs with same start and end time
            cursor.execute("""
                SELECT program_name, start_time, end_time
                FROM programs 
                WHERE start_time = end_time
            """)
            issues['zero_duration_programs'] = cursor.fetchall()
            
            # Check for negative duration programs (end before start)
            cursor.execute("""
                SELECT program_name, start_time, end_time
                FROM programs 
                WHERE start_time > end_time AND NOT (start_time > '12:00' AND end_time < '12:00')
            """)
            issues['negative_duration_programs'] = cursor.fetchall()
            
        return issues


def main():
    """Main function for testing the data loader."""
    loader = DataLoader()
    
    try:
        # Test loading valid data
        print("Loading valid data...")
        success, failed = loader.load_csv_to_programs('/Users/demithrras/Documents/tv-show-intervals-demo/data/full_day_programs.csv')
        print(f"Valid data: {len(success)} successful, {len(failed)} failed")
        
        # Clear and test loading corrupted data
        print("\nClearing database and loading corrupted data...")
        loader.clear_programs_table()
        success, failed = loader.load_csv_to_programs('/Users/demithrras/Documents/tv-show-intervals-demo/data/corrupted_programs.csv')
        print(f"Corrupted data: {len(success)} successful, {len(failed)} failed")
        
        # Show failed records
        if failed:
            print("\nFailed records:")
            for record in failed[:5]:  # Show first 5 failures
                print(f"Row {record['row']}: {record['errors']}")
        
        # Analyze integrity issues
        print("\nData integrity analysis:")
        issues = loader.get_data_integrity_issues()
        for issue_type, data in issues.items():
            if data:
                print(f"{issue_type}: {len(data)} found")
    
    finally:
        loader.disconnect()


if __name__ == "__main__":
    main()