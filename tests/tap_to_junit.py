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
    
    # Parse test results
    tests = []
    for line in tap_content.split('\n'):
        if re.match(r'^(ok|not ok)\s+\d+', line.strip()):
            tests.append(line.strip())
    
    # Create JUnit XML
    testsuite = ET.Element('testsuite')
    testsuite.set('name', 'pgTAP Data Integrity Tests')
    testsuite.set('tests', str(len(tests)))
    
    failed = 0
    for i, test_line in enumerate(tests, 1):
        testcase = ET.SubElement(testsuite, 'testcase')
        
        # Extract test description
        match = re.match(r'^(ok|not ok)\s+\d+\s*-?\s*(.*)', test_line)
        if match:
            status = match.group(1)
            description = match.group(2).strip() or f'Test {i}'
        else:
            status = 'not ok'
            description = f'Test {i}'
        
        testcase.set('name', description)
        testcase.set('classname', 'DataIntegrityTests')
        
        if status == 'not ok':
            failed += 1
            failure = ET.SubElement(testcase, 'failure')
            failure.set('message', f'pgTAP assertion failed: {description}')
            failure.text = test_line
    
    testsuite.set('failures', str(failed))
    
    # Write JUnit XML
    tree = ET.ElementTree(testsuite)
    ET.indent(tree, space='  ', level=0)
    tree.write(junit_file, encoding='utf-8', xml_declaration=True)
    
    print(f"✅ Generated JUnit XML: {junit_file}")
    print(f"📊 Tests: {len(tests)}, Failed: {failed}")

if __name__ == '__main__':
    tap_file = sys.argv[1] if len(sys.argv) > 1 else 'tap_output.txt'
    junit_file = sys.argv[2] if len(sys.argv) > 2 else 'test-results.xml'
    tap_to_junit(tap_file, junit_file)