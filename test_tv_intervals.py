"""
Step definitions for TV program interval testing.
Implements the Gherkin scenarios for pytest-bdd with Allure reporting.
"""

import pytest
import allure
from pytest_bdd import scenarios, given, when, then, parsers
from conftest import get_program_intervals, get_programs, insert_program


# Load all scenarios from the feature file with automatic BDD-Allure integration
scenarios('features/tv_intervals.feature')


# Test context to store program data between steps
@pytest.fixture
def test_context():
    """Fixture to maintain test context between steps."""
    return {}


# Given steps
@given("the database is clean")
def database_is_clean(clean_database):
    """Ensure the database starts clean for each scenario."""
    # The clean_database fixture already handles this
    allure.attach("Database cleaned successfully", name="Database State", attachment_type=allure.attachment_type.TEXT)


@given(parsers.parse('I have a program "{program_name}" that runs from "{start_time}" to "{end_time}"'))
def have_program(test_context, program_name, start_time, end_time):
    """Store program information in test context."""
    test_context['program'] = {
        'name': program_name,
        'start_time': start_time,
        'end_time': end_time
    }
    allure.attach(f"Program: {program_name}\nStart: {start_time}\nEnd: {end_time}", 
                  name="Program Definition", attachment_type=allure.attachment_type.TEXT)


@given("I have the following programs:")
def have_multiple_programs(test_context, datatable):
    """Store multiple programs in test context from a data table."""
    programs = []
    # Skip the header row and process data rows
    headers = datatable[0]
    for row in datatable[1:]:
        programs.append({
            'name': row[0],  # program_name
            'start_time': row[1],  # start_time
            'end_time': row[2]  # end_time
        })
    test_context['programs'] = programs
    
    # Attach program data to Allure report
    program_data = "\n".join([f"{p['name']}: {p['start_time']} - {p['end_time']}" for p in programs])
    allure.attach(program_data, name="Programs Data", attachment_type=allure.attachment_type.TEXT)


# When steps
@when("I insert the program into the database")
def insert_single_program(clean_database, test_context):
    """Insert a single program from test context into the database."""
    program = test_context['program']
    insert_program(clean_database, program['name'], program['start_time'], program['end_time'])
    allure.attach(f"Inserted: {program['name']}", name="Database Operation", attachment_type=allure.attachment_type.TEXT)


@when("I insert all programs into the database")
def insert_all_programs(clean_database, test_context):
    """Insert all programs from test context into the database."""
    programs = test_context['programs']
    inserted_programs = []
    for program in programs:
        insert_program(clean_database, program['name'], program['start_time'], program['end_time'])
        inserted_programs.append(program['name'])
    
    allure.attach(f"Inserted programs: {', '.join(inserted_programs)}", 
                  name="Database Operations", attachment_type=allure.attachment_type.TEXT)


@when("I check the program intervals table")
def check_intervals_table(clean_database):
    """Action to check the intervals table (no actual operation needed)."""
    pass


@when(parsers.parse('I update the program "{program_name}" to run from "{start_time}" to "{end_time}"'))
def update_program(clean_database, program_name, start_time, end_time):
    """Update an existing program's times."""
    clean_database.execute(
        "UPDATE programs SET start_time = %s, end_time = %s WHERE program_name = %s",
        (start_time, end_time, program_name)
    )
    allure.attach(f"Updated {program_name}: {start_time} - {end_time}", 
                  name="Update Operation", attachment_type=allure.attachment_type.TEXT)


@when(parsers.parse('I delete the program "{program_name}"'))
def delete_program(clean_database, program_name):
    """Delete a program from the database."""
    clean_database.execute(
        "DELETE FROM programs WHERE program_name = %s",
        (program_name,)
    )
    allure.attach(f"Deleted: {program_name}", name="Delete Operation", attachment_type=allure.attachment_type.TEXT)


@when(parsers.parse('I rename the program "{old_name}" to "{new_name}"'))
def rename_program(clean_database, old_name, new_name):
    """Rename a program (which should update the intervals table)."""
    clean_database.execute(
        "UPDATE programs SET program_name = %s WHERE program_name = %s",
        (new_name, old_name)
    )
    allure.attach(f"Renamed: {old_name} → {new_name}", name="Rename Operation", attachment_type=allure.attachment_type.TEXT)


# Then steps
@then(parsers.parse('the program "{program_name}" should have {expected_intervals:d} intervals'))
def check_program_intervals(clean_database, program_name, expected_intervals):
    """Verify that a program has the expected number of intervals."""
    intervals = get_program_intervals(clean_database, program_name)
    assert len(intervals) == 1, f"Expected 1 row for program '{program_name}', found {len(intervals)}"
    
    actual_intervals = intervals[0]['interval_count']
    
    # Attach verification details to Allure
    allure.attach(f"Program: {program_name}\nExpected: {expected_intervals}\nActual: {actual_intervals}", 
                  name="Interval Verification", attachment_type=allure.attachment_type.TEXT)
    
    assert actual_intervals == expected_intervals, \
        f"Expected {expected_intervals} intervals for '{program_name}', got {actual_intervals}"


@then("the interval counts should be:")
def check_multiple_intervals(clean_database, datatable):
    """Verify interval counts for multiple programs."""
    # Skip the header row and process data rows
    headers = datatable[0]
    results = []
    
    for row in datatable[1:]:
        program_name = row[0]  # program_name
        expected_intervals = int(row[1])  # intervals
        
        intervals = get_program_intervals(clean_database, program_name)
        assert len(intervals) == 1, f"Expected 1 row for program '{program_name}', found {len(intervals)}"
        
        actual_intervals = intervals[0]['interval_count']
        results.append(f"{program_name}: Expected {expected_intervals}, Got {actual_intervals}")
        
        assert actual_intervals == expected_intervals, \
            f"Expected {expected_intervals} intervals for '{program_name}', got {actual_intervals}"
    
    # Attach results summary to Allure
    allure.attach("\n".join(results), name="Multiple Program Results", attachment_type=allure.attachment_type.TEXT)


@then(parsers.parse("there should be {expected_count:d} rows in the program intervals table"))
def check_intervals_table_count(clean_database, expected_count):
    """Verify the total number of rows in the program intervals table."""
    intervals = get_program_intervals(clean_database)
    actual_count = len(intervals)
    
    allure.attach(f"Expected rows: {expected_count}\nActual rows: {actual_count}", 
                  name="Table Row Count", attachment_type=allure.attachment_type.TEXT)
    
    assert actual_count == expected_count, \
        f"Expected {expected_count} rows in program_intervals table, got {actual_count}"


@then(parsers.parse('there should be no intervals for program "{program_name}"'))
def check_no_intervals_for_program(clean_database, program_name):
    """Verify that a specific program has no intervals recorded."""
    intervals = get_program_intervals(clean_database, program_name)
    allure.attach(f"Program: {program_name}\nFound intervals: {len(intervals)}", 
                  name="No Intervals Check", attachment_type=allure.attachment_type.TEXT)
    
    assert len(intervals) == 0, \
        f"Expected no intervals for program '{program_name}', but found {len(intervals)} rows"