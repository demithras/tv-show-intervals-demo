"""
Step definitions for TV program interval testing.
Implements the Gherkin scenarios for pytest-bdd.
"""

import pytest
from pytest_bdd import scenarios, given, when, then, parsers
from conftest import get_program_intervals, get_programs, insert_program


# Load all scenarios from the feature file
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
    pass


@given(parsers.parse('I have a program "{program_name}" that runs from "{start_time}" to "{end_time}"'))
def have_program(test_context, program_name, start_time, end_time):
    """Store program information in test context."""
    test_context['program'] = {
        'name': program_name,
        'start_time': start_time,
        'end_time': end_time
    }


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


# When steps
@when("I insert the program into the database")
def insert_single_program(clean_database, test_context):
    """Insert a single program from test context into the database."""
    program = test_context['program']
    insert_program(clean_database, program['name'], program['start_time'], program['end_time'])


@when("I insert all programs into the database")
def insert_all_programs(clean_database, test_context):
    """Insert all programs from test context into the database."""
    programs = test_context['programs']
    for program in programs:
        insert_program(clean_database, program['name'], program['start_time'], program['end_time'])


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


@when(parsers.parse('I delete the program "{program_name}"'))
def delete_program(clean_database, program_name):
    """Delete a program from the database."""
    clean_database.execute(
        "DELETE FROM programs WHERE program_name = %s",
        (program_name,)
    )


@when(parsers.parse('I rename the program "{old_name}" to "{new_name}"'))
def rename_program(clean_database, old_name, new_name):
    """Rename a program (which should update the intervals table)."""
    clean_database.execute(
        "UPDATE programs SET program_name = %s WHERE program_name = %s",
        (new_name, old_name)
    )


# Then steps
@then(parsers.parse('the program "{program_name}" should have {expected_intervals:d} intervals'))
def check_program_intervals(clean_database, program_name, expected_intervals):
    """Verify that a program has the expected number of intervals."""
    intervals = get_program_intervals(clean_database, program_name)
    assert len(intervals) == 1, f"Expected 1 row for program '{program_name}', found {len(intervals)}"
    
    actual_intervals = intervals[0]['interval_count']
    assert actual_intervals == expected_intervals, \
        f"Expected {expected_intervals} intervals for '{program_name}', got {actual_intervals}"


@then("the interval counts should be:")
def check_multiple_intervals(clean_database, datatable):
    """Verify interval counts for multiple programs."""
    # Skip the header row and process data rows
    headers = datatable[0]
    for row in datatable[1:]:
        program_name = row[0]  # program_name
        expected_intervals = int(row[1])  # intervals
        
        intervals = get_program_intervals(clean_database, program_name)
        assert len(intervals) == 1, f"Expected 1 row for program '{program_name}', found {len(intervals)}"
        
        actual_intervals = intervals[0]['interval_count']
        assert actual_intervals == expected_intervals, \
            f"Expected {expected_intervals} intervals for '{program_name}', got {actual_intervals}"


@then(parsers.parse("there should be {expected_count:d} rows in the program intervals table"))
def check_intervals_table_count(clean_database, expected_count):
    """Verify the total number of rows in the program intervals table."""
    intervals = get_program_intervals(clean_database)
    actual_count = len(intervals)
    assert actual_count == expected_count, \
        f"Expected {expected_count} rows in program_intervals table, got {actual_count}"


@then(parsers.parse('there should be no intervals for program "{program_name}"'))
def check_no_intervals_for_program(clean_database, program_name):
    """Verify that a specific program has no intervals recorded."""
    intervals = get_program_intervals(clean_database, program_name)
    assert len(intervals) == 0, \
        f"Expected no intervals for program '{program_name}', but found {len(intervals)} rows"