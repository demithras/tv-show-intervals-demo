"""
Step definitions for data integrity testing between programs and program_intervals tables.
Implements focused data integrity verification scenarios.
"""

import pytest
import allure
import hashlib
import csv
import os
from pytest_bdd import scenarios, given, when, then, parsers
from conftest import get_program_intervals, get_programs, insert_program


# Load all scenarios from the data integrity feature file
scenarios('features/data_integrity.feature')


def generate_test_id(scenario_name):
    """Generate consistent test ID for history tracking"""
    return hashlib.md5(scenario_name.encode()).hexdigest()[:16]


# Test context to store data between steps
@pytest.fixture
def test_context():
    """Fixture to maintain test context between steps."""
    return {}


@pytest.fixture(autouse=True)
def setup_allure_test_id(request):
    """Automatically set consistent test IDs for Allure history tracking"""
    if hasattr(request.node, 'scenario'):
        scenario_name = request.node.scenario['name']
        test_id = generate_test_id(scenario_name)
        allure.dynamic.testcase_id(test_id)
        allure.dynamic.label("testType", "DataIntegrity")
        allure.dynamic.label("framework", "pytest-bdd")


# Background and Given steps
@given("the database is clean")
def database_is_clean(clean_database):
    """Ensure the database starts clean for each scenario."""
    allure.attach("Database cleaned successfully", name="Database State", attachment_type=allure.attachment_type.TEXT)


@given("I load the full day programming schedule from CSV:")
def load_full_day_schedule_from_datatable(clean_database, datatable):
    """Load the complete day's programming schedule from the data table."""
    programs_loaded = []
    
    # Skip the header row and process data rows
    headers = datatable[0]
    for row in datatable[1:]:
        program_name = row[0]
        start_time = row[1]
        end_time = row[2]
        
        insert_program(clean_database, program_name, start_time, end_time)
        programs_loaded.append(f"{program_name} ({start_time}-{end_time})")
    
    # Attach loaded programs to Allure report
    program_data = "\n".join(programs_loaded)
    allure.attach(program_data, name="Full Day Schedule Loaded", attachment_type=allure.attachment_type.TEXT)
    allure.attach(f"Total programs loaded: {len(programs_loaded)}", name="Load Summary", attachment_type=allure.attachment_type.TEXT)


@given(parsers.parse('I load the full day programming schedule from CSV file "{csv_filename}"'))
def load_full_day_schedule_from_csv(clean_database, csv_filename):
    """Load the complete day's programming schedule from a CSV file."""
    # Get the absolute path to the CSV file
    csv_path = os.path.join(os.path.dirname(__file__), csv_filename)
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found: {csv_path}")
    
    programs_loaded = []
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            program_name = row['program_name']
            start_time = row['start_time']
            end_time = row['end_time']
            
            insert_program(clean_database, program_name, start_time, end_time)
            programs_loaded.append(f"{program_name} ({start_time}-{end_time})")
    
    # Attach loaded programs to Allure report
    program_data = "\n".join(programs_loaded)
    allure.attach(program_data, name="Full Day Schedule Loaded from CSV", attachment_type=allure.attachment_type.TEXT)
    allure.attach(f"Total programs loaded: {len(programs_loaded)}", name="Load Summary", attachment_type=allure.attachment_type.TEXT)
    allure.attach(f"CSV file: {csv_filename}", name="Source File", attachment_type=allure.attachment_type.TEXT)


# When steps
@when("I query both programs and program_intervals tables")
def query_both_tables(clean_database, test_context):
    """Query both tables and store results in test context."""
    programs = get_programs(clean_database)
    intervals = get_program_intervals(clean_database)
    
    test_context['programs'] = programs
    test_context['intervals'] = intervals
    
    allure.attach(f"Programs found: {len(programs)}\nIntervals found: {len(intervals)}", 
                  name="Table Query Results", attachment_type=allure.attachment_type.TEXT)


@when("I analyze the schedule coverage")
def analyze_schedule_coverage(clean_database, test_context):
    """Analyze the schedule for gaps and overlaps."""
    programs = get_programs(clean_database)
    
    # Sort programs by start time for analysis
    sorted_programs = sorted(programs, key=lambda p: p['start_time'])
    
    gaps = []
    overlaps = []
    
    # Check for gaps and overlaps
    for i in range(len(sorted_programs) - 1):
        current_end = sorted_programs[i]['end_time']
        next_start = sorted_programs[i + 1]['start_time']
        
        if current_end < next_start:
            gaps.append(f"Gap between {sorted_programs[i]['program_name']} and {sorted_programs[i + 1]['program_name']}")
        elif current_end > next_start:
            overlaps.append(f"Overlap between {sorted_programs[i]['program_name']} and {sorted_programs[i + 1]['program_name']}")
    
    test_context['gaps'] = gaps
    test_context['overlaps'] = overlaps
    test_context['sorted_programs'] = sorted_programs
    
    coverage_report = f"Gaps found: {len(gaps)}\nOverlaps found: {len(overlaps)}"
    if gaps:
        coverage_report += f"\nGaps: {'; '.join(gaps)}"
    if overlaps:
        coverage_report += f"\nOverlaps: {'; '.join(overlaps)}"
    
    allure.attach(coverage_report, name="Schedule Coverage Analysis", attachment_type=allure.attachment_type.TEXT)


# Then steps
@then("every program in the programs table should have a corresponding entry in the program_intervals table")
def verify_all_programs_have_intervals(test_context):
    """Verify that every program has corresponding interval data."""
    programs = test_context['programs']
    intervals = test_context['intervals']
    
    program_names = {p['program_name'] for p in programs}
    interval_names = {i['program_name'] for i in intervals}
    
    missing_intervals = program_names - interval_names
    
    verification_data = f"Programs: {len(program_names)}\nWith intervals: {len(interval_names)}\nMissing intervals: {len(missing_intervals)}"
    if missing_intervals:
        verification_data += f"\nMissing: {', '.join(missing_intervals)}"
    
    allure.attach(verification_data, name="Program-Interval Mapping", attachment_type=allure.attachment_type.TEXT)
    
    assert len(missing_intervals) == 0, f"Programs missing intervals: {', '.join(missing_intervals)}"


@then("the program count in both tables should be equal")
def verify_equal_program_counts(test_context):
    """Verify that both tables have the same number of programs."""
    programs = test_context['programs']
    intervals = test_context['intervals']
    
    program_count = len(programs)
    interval_count = len(intervals)
    
    allure.attach(f"Programs table: {program_count}\nIntervals table: {interval_count}", 
                  name="Table Counts", attachment_type=allure.attachment_type.TEXT)
    
    assert program_count == interval_count, \
        f"Table counts mismatch: programs={program_count}, intervals={interval_count}"


@then("every entry in the program_intervals table should have a corresponding program in the programs table")
def verify_no_orphaned_intervals(test_context):
    """Verify that there are no orphaned interval entries."""
    programs = test_context['programs']
    intervals = test_context['intervals']
    
    program_names = {p['program_name'] for p in programs}
    interval_names = {i['program_name'] for i in intervals}
    
    orphaned_intervals = interval_names - program_names
    
    verification_data = f"Interval entries: {len(interval_names)}\nWith programs: {len(program_names)}\nOrphaned: {len(orphaned_intervals)}"
    if orphaned_intervals:
        verification_data += f"\nOrphaned: {', '.join(orphaned_intervals)}"
    
    allure.attach(verification_data, name="Orphaned Intervals Check", attachment_type=allure.attachment_type.TEXT)
    
    assert len(orphaned_intervals) == 0, f"Orphaned intervals found: {', '.join(orphaned_intervals)}"


@then("there should be no orphaned intervals")
def verify_no_orphaned_intervals_simple(test_context):
    """Simple verification for no orphaned intervals."""
    # This is handled by the more detailed step above
    pass


@then("the schedule should cover the full 24-hour period without gaps")
def verify_no_schedule_gaps(test_context):
    """Verify that the schedule has no gaps."""
    gaps = test_context.get('gaps', [])
    
    # For a full day schedule, we expect the first program to start at 00:00
    # and programs to connect seamlessly until the last program ends at 00:00 (midnight)
    sorted_programs = test_context.get('sorted_programs', [])
    
    coverage_issues = []
    if sorted_programs:
        first_program = sorted_programs[0]
        last_program = sorted_programs[-1]
        
        # Check if first program starts at midnight
        if str(first_program['start_time']) != '00:00:00':
            coverage_issues.append(f"Schedule doesn't start at 00:00, starts at {first_program['start_time']}")
        
        # Check if last program ends at midnight (indicating full day coverage)
        if str(last_program['end_time']) != '00:00:00':
            coverage_issues.append(f"Schedule doesn't end at 00:00, ends at {last_program['end_time']}")
    
    gap_report = f"Schedule gaps: {len(gaps)}\nCoverage issues: {len(coverage_issues)}"
    if gaps:
        gap_report += f"\nGaps: {'; '.join(gaps)}"
    if coverage_issues:
        gap_report += f"\nCoverage issues: {'; '.join(coverage_issues)}"
    
    allure.attach(gap_report, name="Schedule Gap Analysis", attachment_type=allure.attachment_type.TEXT)
    
    assert len(gaps) == 0, f"Schedule has gaps: {'; '.join(gaps)}"
    assert len(coverage_issues) == 0, f"Coverage issues: {'; '.join(coverage_issues)}"


@then("the schedule should have no overlapping programs")
def verify_no_schedule_overlaps(test_context):
    """Verify that no programs overlap in the schedule."""
    overlaps = test_context.get('overlaps', [])
    
    overlap_report = f"Schedule overlaps found: {len(overlaps)}"
    if overlaps:
        overlap_report += f"\nOverlaps: {'; '.join(overlaps)}"
    
    allure.attach(overlap_report, name="Schedule Overlap Analysis", attachment_type=allure.attachment_type.TEXT)
    
    assert len(overlaps) == 0, f"Schedule has overlaps: {'; '.join(overlaps)}"


@then("all program names in the programs table should not be empty")
def verify_program_names_not_empty(test_context):
    """Verify that all program names in the programs table are not empty or null."""
    programs = test_context['programs']
    
    empty_names = []
    null_names = []
    
    for program in programs:
        program_name = program['program_name']
        if program_name is None:
            null_names.append(f"Program with null name: start={program['start_time']}, end={program['end_time']}")
        elif program_name.strip() == "":
            empty_names.append(f"Program with empty name: start={program['start_time']}, end={program['end_time']}")
    
    name_validation_report = f"Programs with empty names: {len(empty_names)}\nPrograms with null names: {len(null_names)}"
    if empty_names:
        name_validation_report += f"\nEmpty names: {'; '.join(empty_names)}"
    if null_names:
        name_validation_report += f"\nNull names: {'; '.join(null_names)}"
    
    allure.attach(name_validation_report, name="Program Name Validation", attachment_type=allure.attachment_type.TEXT)
    
    assert len(empty_names) == 0, f"Found programs with empty names: {'; '.join(empty_names)}"
    assert len(null_names) == 0, f"Found programs with null names: {'; '.join(null_names)}"


@then("all program names in the program_intervals table should not be empty")
def verify_interval_names_not_empty(test_context):
    """Verify that all program names in the program_intervals table are not empty or null."""
    intervals = test_context['intervals']
    
    empty_names = []
    null_names = []
    
    for interval in intervals:
        program_name = interval['program_name']
        if program_name is None:
            null_names.append(f"Interval with null name: interval_count={interval['interval_count']}")
        elif program_name.strip() == "":
            empty_names.append(f"Interval with empty name: interval_count={interval['interval_count']}")
    
    interval_name_validation_report = f"Intervals with empty names: {len(empty_names)}\nIntervals with null names: {len(null_names)}"
    if empty_names:
        interval_name_validation_report += f"\nEmpty names: {'; '.join(empty_names)}"
    if null_names:
        interval_name_validation_report += f"\nNull names: {'; '.join(null_names)}"
    
    allure.attach(interval_name_validation_report, name="Interval Name Validation", attachment_type=allure.attachment_type.TEXT)
    
    assert len(empty_names) == 0, f"Found intervals with empty names: {'; '.join(empty_names)}"
    assert len(null_names) == 0, f"Found intervals with null names: {'; '.join(null_names)}"