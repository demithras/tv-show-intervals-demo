"""
Data integrity validation functions for TV show intervals project.
Provides comprehensive data quality checks for programs and program_intervals tables.
"""

from typing import Dict, List, Tuple, Any
import psycopg2
from psycopg2.extras import RealDictCursor


class DataIntegrityValidator:
    """Validates data integrity across TV program tables."""
    
    def __init__(self, cursor):
        """
        Initialize validator with database cursor.
        
        Args:
            cursor: Database cursor for executing queries
        """
        self.cursor = cursor
    
    def validate_referential_integrity(self) -> Dict[str, Any]:
        """
        Check referential integrity between programs and program_intervals tables.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'orphaned_intervals': [],
            'missing_intervals': []
        }
        
        # Check for program_intervals without corresponding programs
        self.cursor.execute("""
            SELECT pi.program_name 
            FROM program_intervals pi 
            LEFT JOIN programs p ON pi.program_name = p.program_name 
            WHERE p.program_name IS NULL
        """)
        orphaned = [row['program_name'] for row in self.cursor.fetchall()]
        
        if orphaned:
            results['is_valid'] = False
            results['orphaned_intervals'] = orphaned
            results['errors'].append(f"Found {len(orphaned)} orphaned interval records")
        
        # Check for programs without corresponding intervals
        self.cursor.execute("""
            SELECT p.program_name 
            FROM programs p 
            LEFT JOIN program_intervals pi ON p.program_name = pi.program_name 
            WHERE pi.program_name IS NULL
        """)
        missing = [row['program_name'] for row in self.cursor.fetchall()]
        
        if missing:
            results['is_valid'] = False
            results['missing_intervals'] = missing
            results['errors'].append(f"Found {len(missing)} programs without interval records")
        
        return results
    
    def validate_time_constraints(self) -> Dict[str, Any]:
        """
        Validate time-related constraints and business rules.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'invalid_times': [],
            'overlapping_programs': [],
            'negative_durations': []
        }
        
        # Check for invalid time formats or values
        self.cursor.execute("""
            SELECT program_name, start_time, end_time
            FROM programs 
            WHERE start_time IS NULL 
               OR end_time IS NULL
               OR start_time::text = ''
               OR end_time::text = ''
        """)
        invalid_times = self.cursor.fetchall()
        
        if invalid_times:
            results['is_valid'] = False
            results['invalid_times'] = invalid_times
            results['errors'].append(f"Found {len(invalid_times)} programs with invalid time values")
        
        # Check for overlapping programs (excluding overnight programs)
        self.cursor.execute("""
            SELECT p1.program_name as program1, p2.program_name as program2,
                   p1.start_time as start1, p1.end_time as end1,
                   p2.start_time as start2, p2.end_time as end2
            FROM programs p1 
            JOIN programs p2 ON p1.id < p2.id
            WHERE p1.start_time < p2.end_time 
              AND p1.end_time > p2.start_time
              AND NOT (p1.start_time > p1.end_time OR p2.start_time > p2.end_time)
        """)
        overlapping = self.cursor.fetchall()
        
        if overlapping:
            results['is_valid'] = False
            results['overlapping_programs'] = overlapping
            results['errors'].append(f"Found {len(overlapping)} overlapping program pairs")
        
        # Check for negative duration (non-overnight programs)
        self.cursor.execute("""
            SELECT program_name, start_time, end_time
            FROM programs 
            WHERE start_time > end_time 
              AND NOT (start_time > '12:00' AND end_time < '12:00')
        """)
        negative = self.cursor.fetchall()
        
        if negative:
            results['is_valid'] = False
            results['negative_durations'] = negative
            results['errors'].append(f"Found {len(negative)} programs with negative durations")
        
        return results
    
    def validate_interval_calculations(self) -> Dict[str, Any]:
        """
        Validate that interval calculations are correct.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'incorrect_calculations': []
        }
        
        # Check if calculated intervals match expected values
        self.cursor.execute("""
            SELECT p.program_name, p.start_time, p.end_time,
                   pi.interval_count as stored_count,
                   count_15min_intervals(p.start_time, p.end_time) as calculated_count
            FROM programs p
            JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE pi.interval_count != count_15min_intervals(p.start_time, p.end_time)
        """)
        incorrect = self.cursor.fetchall()
        
        if incorrect:
            results['is_valid'] = False
            results['incorrect_calculations'] = incorrect
            results['errors'].append(f"Found {len(incorrect)} programs with incorrect interval calculations")
        
        return results
    
    def validate_data_quality(self) -> Dict[str, Any]:
        """
        Check general data quality issues.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'duplicate_names': [],
            'empty_names': [],
            'long_names': [],
            'zero_duration': []
        }
        
        # Check for duplicate program names
        self.cursor.execute("""
            SELECT program_name, COUNT(*) as count
            FROM programs 
            GROUP BY program_name 
            HAVING COUNT(*) > 1
        """)
        duplicates = self.cursor.fetchall()
        
        if duplicates:
            results['is_valid'] = False
            results['duplicate_names'] = duplicates
            results['errors'].append(f"Found {len(duplicates)} duplicate program names")
        
        # Check for empty or whitespace-only program names
        self.cursor.execute("""
            SELECT program_name, start_time, end_time
            FROM programs 
            WHERE program_name IS NULL 
               OR TRIM(program_name) = ''
               OR LENGTH(program_name) = 0
        """)
        empty_names = self.cursor.fetchall()
        
        if empty_names:
            results['is_valid'] = False
            results['empty_names'] = empty_names
            results['errors'].append(f"Found {len(empty_names)} programs with empty names")
        
        # Check for excessively long program names
        self.cursor.execute("""
            SELECT program_name, LENGTH(program_name) as name_length
            FROM programs 
            WHERE LENGTH(program_name) > 255
        """)
        long_names = self.cursor.fetchall()
        
        if long_names:
            results['is_valid'] = False
            results['long_names'] = long_names
            results['errors'].append(f"Found {len(long_names)} programs with names exceeding 255 characters")
        
        # Check for zero duration programs
        self.cursor.execute("""
            SELECT program_name, start_time, end_time
            FROM programs 
            WHERE start_time = end_time
        """)
        zero_duration = self.cursor.fetchall()
        
        if zero_duration:
            # This might be valid business case, so just report it
            results['zero_duration'] = zero_duration
            results['errors'].append(f"Found {len(zero_duration)} zero-duration programs (may be valid)")
        
        return results
    
    def validate_business_rules(self) -> Dict[str, Any]:
        """
        Validate business-specific rules for TV programming.
        
        Returns:
            Dictionary with validation results
        """
        results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'suspicious_patterns': []
        }
        
        # Check for programs longer than 24 hours (impossible for daily schedule)
        self.cursor.execute("""
            SELECT program_name, start_time, end_time,
                   CASE 
                       WHEN end_time < start_time THEN 
                           EXTRACT(EPOCH FROM (TIME '24:00:00' - start_time)) / 60 + 
                           EXTRACT(EPOCH FROM end_time) / 60
                       ELSE 
                           EXTRACT(EPOCH FROM (end_time - start_time)) / 60
                   END as duration_minutes
            FROM programs
            HAVING duration_minutes > 1440  -- 24 hours
        """)
        long_programs = self.cursor.fetchall()
        
        if long_programs:
            results['is_valid'] = False
            results['errors'].append(f"Found {len(long_programs)} programs longer than 24 hours")
            results['suspicious_patterns'].extend(long_programs)
        
        # Check for suspicious program names (potential SQL injection, etc.)
        self.cursor.execute("""
            SELECT program_name
            FROM programs 
            WHERE program_name ILIKE ANY(ARRAY['%drop%', '%delete%', '%insert%', '%update%', 
                                               '%select%', '%--%', '%;%', '%script%'])
        """)
        suspicious_names = [row['program_name'] for row in self.cursor.fetchall()]
        
        if suspicious_names:
            results['warnings'].append(f"Found {len(suspicious_names)} programs with suspicious names")
            results['suspicious_patterns'].extend(suspicious_names)
        
        # Check for programs with non-standard time intervals (not aligned to common broadcast patterns)
        self.cursor.execute("""
            SELECT program_name, start_time, end_time
            FROM programs 
            WHERE EXTRACT(MINUTE FROM start_time) NOT IN (0, 15, 30, 45)
               OR EXTRACT(MINUTE FROM end_time) NOT IN (0, 15, 30, 45)
        """)
        non_standard_times = self.cursor.fetchall()
        
        if non_standard_times:
            results['warnings'].append(f"Found {len(non_standard_times)} programs with non-standard time slots")
        
        return results
    
    def run_comprehensive_validation(self) -> Dict[str, Any]:
        """
        Run all validation checks and return comprehensive results.
        
        Returns:
            Dictionary with all validation results
        """
        all_results = {
            'overall_valid': True,
            'summary': {
                'total_errors': 0,
                'total_warnings': 0,
                'checks_performed': 0
            },
            'referential_integrity': self.validate_referential_integrity(),
            'time_constraints': self.validate_time_constraints(),
            'interval_calculations': self.validate_interval_calculations(),
            'data_quality': self.validate_data_quality(),
            'business_rules': self.validate_business_rules()
        }
        
        # Calculate summary
        for check_name, check_results in all_results.items():
            if isinstance(check_results, dict) and 'is_valid' in check_results:
                all_results['summary']['checks_performed'] += 1
                if not check_results['is_valid']:
                    all_results['overall_valid'] = False
                    all_results['summary']['total_errors'] += len(check_results.get('errors', []))
                all_results['summary']['total_warnings'] += len(check_results.get('warnings', []))
        
        return all_results


def format_validation_report(validation_results: Dict[str, Any]) -> str:
    """
    Format validation results into a readable report.
    
    Args:
        validation_results: Results from run_comprehensive_validation()
        
    Returns:
        Formatted string report
    """
    report = []
    report.append("=" * 60)
    report.append("DATA INTEGRITY VALIDATION REPORT")
    report.append("=" * 60)
    
    summary = validation_results['summary']
    overall_valid = validation_results['overall_valid']
    
    report.append(f"Overall Status: {'PASS' if overall_valid else 'FAIL'}")
    report.append(f"Checks Performed: {summary['checks_performed']}")
    report.append(f"Total Errors: {summary['total_errors']}")
    report.append(f"Total Warnings: {summary['total_warnings']}")
    report.append("")
    
    # Detail each check
    checks = ['referential_integrity', 'time_constraints', 'interval_calculations', 
              'data_quality', 'business_rules']
    
    for check_name in checks:
        check_results = validation_results.get(check_name, {})
        if isinstance(check_results, dict):
            report.append(f"{check_name.upper().replace('_', ' ')}:")
            report.append(f"  Status: {'PASS' if check_results.get('is_valid', True) else 'FAIL'}")
            
            errors = check_results.get('errors', [])
            if errors:
                report.append("  Errors:")
                for error in errors:
                    report.append(f"    - {error}")
            
            warnings = check_results.get('warnings', [])
            if warnings:
                report.append("  Warnings:")
                for warning in warnings:
                    report.append(f"    - {warning}")
            
            report.append("")
    
    report.append("=" * 60)
    return "\n".join(report)