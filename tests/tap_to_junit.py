#!/usr/bin/env python3
"""
Convert TAP output to JUnit XML format for GitHub Actions integration.
"""
import xml.etree.ElementTree as ET
import re
import sys

def tap_to_junit(tap_file, junit_file='test-results.xml'):
    """Convert TAP output to JUnit XML format."""
    
    # Read TAP output
    with open(tap_file, 'r') as f:
        tap_content = f.read()
    
    # Parse test results - handle both standard TAP and pgTAP format
    tests = []
    test_plan = 0
    
    # Look for test plan (1..N)
    plan_match = re.search(r'1\.\.(\d+)', tap_content)
    if plan_match:
        test_plan = int(plan_match.group(1))
    
    # Find all test result lines (handle whitespace and pgTAP format)
    for line in tap_content.split('\n'):
        # Match both "ok N" and "not ok N" with optional leading whitespace
        if re.match(r'^\s*(ok|not ok)\s+\d+', line.strip()):
            tests.append(line.strip())
    
    # Use plan if we have it and it's reasonable, otherwise use actual count
    total_tests = test_plan if test_plan > 0 else len(tests)
    
    # Create JUnit XML
    testsuite = ET.Element('testsuite')
    testsuite.set('name', 'pgTAP Data Integrity Tests')
    testsuite.set('tests', str(total_tests))
    
    failed = 0
    errors = 0
    
    for i, test_line in enumerate(tests, 1):
        testcase = ET.SubElement(testsuite, 'testcase')
        
        # Extract test description - handle pgTAP format
        match = re.match(r'^\s*(ok|not ok)\s+\d+\s*-?\s*(.*)', test_line)
        if match:
            status = match.group(1)
            description = match.group(2).strip() or f'Test {i}'
        else:
            status = 'not ok'
            description = f'Test {i}'
            errors += 1
        
        testcase.set('name', description)
        testcase.set('classname', 'DataIntegrityTests')
        
        if status == 'not ok':
            failed += 1
            failure = ET.SubElement(testcase, 'failure')
            failure.set('message', f'pgTAP assertion failed: {description}')
            failure.text = test_line
    
    testsuite.set('failures', str(failed))
    testsuite.set('errors', str(errors))
    
    # Write JUnit XML
    tree = ET.ElementTree(testsuite)
    ET.indent(tree, space='  ', level=0)
    tree.write(junit_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Generated JUnit XML: {junit_file}")
    print(f"📊 Tests: {total_tests} (plan: {test_plan}, actual: {len(tests)}), Failed: {failed}, Errors: {errors}")
    
    return total_tests, failed, errors

if __name__ == '__main__':
    tap_file = sys.argv[1] if len(sys.argv) > 1 else 'tap_output.txt'
    junit_file = sys.argv[2] if len(sys.argv) > 2 else 'test-results.xml'
    tap_to_junit(tap_file, junit_file)