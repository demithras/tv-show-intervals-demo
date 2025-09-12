#!/usr/bin/env python3
"""
TAP to Allure Results Converter
Converts pgTAP TAP output to Allure-compatible JSON format
Maintains compatibility with existing Allure reporting infrastructure
"""

import sys
import json
import re
import hashlib
import uuid
from datetime import datetime
from pathlib import Path
import argparse

class TAPToAllureConverter:
    def __init__(self):
        self.test_results = []
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.start_time = None
        self.end_time = None
        self.test_metadata = {}

    def parse_tap_output(self, tap_content):
        """Parse TAP output and convert to Allure format."""
        lines = tap_content.strip().split('\n')
        
        self.start_time = int(datetime.now().timestamp() * 1000)
        
        for line in lines:
            line = line.strip()
            
            # Parse test plan
            if line.startswith('1..'):
                self.total_tests = int(line.split('..')[1])
                continue
            
            # Parse test results
            if re.match(r'^(ok|not ok)\s+\d+', line):
                self.parse_test_result(line)
                
            # Capture additional metadata from PostgreSQL output
            elif 'Database:' in line or 'User:' in line or 'Timestamp:' in line:
                key_value = line.split(':', 1)
                if len(key_value) == 2:
                    self.test_metadata[key_value[0].strip()] = key_value[1].strip()
        
        self.end_time = int(datetime.now().timestamp() * 1000)

    def parse_test_result(self, line):
        """Parse individual test result line."""
        # Match: "ok 1 - Test description" or "not ok 1 - Test description"
        match = re.match(r'^(ok|not ok)\s+(\d+)\s*-?\s*(.*)', line)
        if not match:
            return
        
        status = match.group(1)
        test_number = int(match.group(2))
        description = match.group(3).strip() or f"Test {test_number}"
        
        # Generate consistent UUID for test based on description for history tracking
        test_id = hashlib.md5(f"pgTAP-{description}".encode()).hexdigest()[:16]
        test_uuid = str(uuid.uuid4())
        
        is_passed = status == 'ok'
        if is_passed:
            allure_status = "passed"
            self.passed_tests += 1
        else:
            allure_status = "failed"
            self.failed_tests += 1
        
        # Map test descriptions to appropriate categories
        feature, story = self.categorize_test(description)
        
        # Create Allure test result
        test_result = {
            "uuid": test_uuid,
            "historyId": test_id,
            "testCaseId": test_id,
            "name": description,
            "fullName": f"pgTAP Data Integrity: {description}",
            "labels": [
                {"name": "framework", "value": "pgTAP"},
                {"name": "testType", "value": "DataIntegrity"},
                {"name": "suite", "value": "Data Integrity Tests"},
                {"name": "feature", "value": feature},
                {"name": "story", "value": story},
                {"name": "testClass", "value": "DataIntegrityTests"},
                {"name": "testMethod", "value": f"test_{test_number:02d}"}
            ],
            "status": allure_status,
            "statusDetails": {
                "known": False,
                "muted": False,
                "flaky": False
            },
            "stage": "finished",
            "start": self.start_time + (test_number * 100),  # Slight offset per test
            "stop": self.start_time + (test_number * 100) + 200,
            "steps": [
                {
                    "name": f"Execute pgTAP assertion: {description}",
                    "status": allure_status,
                    "stage": "finished",
                    "start": self.start_time + (test_number * 100),
                    "stop": self.start_time + (test_number * 100) + 200
                }
            ],
            "attachments": [],
            "parameters": []
        }
        
        # Add failure details if test failed
        if not is_passed:
            test_result["statusDetails"]["message"] = f"pgTAP assertion failed: {description}"
            test_result["statusDetails"]["trace"] = f"TAP output: {line}\nTest Number: {test_number}"
        
        # Add metadata as parameters
        for key, value in self.test_metadata.items():
            test_result["parameters"].append({
                "name": key,
                "value": value
            })
        
        self.test_results.append(test_result)

    def categorize_test(self, description):
        """Categorize tests based on description for better Allure organization."""
        description_lower = description.lower()
        
        if 'program count' in description_lower or 'equal' in description_lower:
            return "Table Consistency", "Program Count Validation"
        elif 'orphaned' in description_lower:
            return "Data Integrity", "Orphaned Records"
        elif 'corresponding' in description_lower:
            return "Data Integrity", "Referential Integrity"
        elif 'program names' in description_lower or 'empty' in description_lower or 'null' in description_lower:
            return "Data Quality", "Name Validation"
        elif 'schedule' in description_lower or 'coverage' in description_lower:
            return "Business Logic", "Schedule Coverage"
        elif 'interval' in description_lower and 'count' in description_lower:
            return "Business Logic", "Interval Calculation"
        elif 'test data' in description_lower:
            return "Test Setup", "Data Preparation"
        else:
            return "Database Integrity", "General Validation"

    def generate_allure_results(self, output_dir):
        """Generate Allure result files."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Generate individual result files
        for test_result in self.test_results:
            result_file = output_path / f"{test_result['uuid']}-result.json"
            with open(result_file, 'w') as f:
                json.dump(test_result, f, indent=2)
        
        # Generate test results summary attachment
        summary = {
            "total": self.total_tests,
            "passed": self.passed_tests,
            "failed": self.failed_tests,
            "duration": self.end_time - self.start_time if self.end_time else 0
        }
        
        # Create summary attachment
        summary_uuid = str(uuid.uuid4())
        summary_attachment = {
            "name": "pgTAP Test Summary",
            "type": "text/plain",
            "source": f"summary-{summary_uuid}.txt"
        }
        
        summary_file = output_path / summary_attachment["source"]
        with open(summary_file, 'w') as f:
            f.write("pgTAP Data Integrity Test Results\n")
            f.write("==================================\n\n")
            f.write(f"Total Tests: {summary['total']}\n")
            f.write(f"Passed: {summary['passed']}\n")
            f.write(f"Failed: {summary['failed']}\n")
            f.write(f"Duration: {summary['duration']}ms\n")
            
            if summary['total'] > 0:
                success_rate = (summary['passed'] / summary['total']) * 100
                f.write(f"Success Rate: {success_rate:.1f}%\n")
            
            f.write(f"\nTest Framework: pgTAP\n")
            f.write(f"Database: PostgreSQL\n")
            f.write(f"Generated: {datetime.now().isoformat()}\n")
            
            # Add metadata if available
            if self.test_metadata:
                f.write(f"\nEnvironment Information:\n")
                f.write("========================\n")
                for key, value in self.test_metadata.items():
                    f.write(f"{key}: {value}\n")
        
        # Add the summary as an attachment to the first test result if available
        if self.test_results:
            self.test_results[0]["attachments"].append(summary_attachment)
        
        # Generate categories file for better Allure organization
        categories = [
            {
                "name": "Data Integrity Failures",
                "matchedStatuses": ["failed"],
                "messageRegex": ".*integrity.*|.*orphaned.*|.*corresponding.*"
            },
            {
                "name": "Data Quality Issues", 
                "matchedStatuses": ["failed"],
                "messageRegex": ".*empty.*|.*null.*|.*name.*"
            },
            {
                "name": "Business Logic Errors",
                "matchedStatuses": ["failed"], 
                "messageRegex": ".*interval.*|.*count.*|.*schedule.*"
            }
        ]
        
        categories_file = output_path / "categories.json"
        with open(categories_file, 'w') as f:
            json.dump(categories, f, indent=2)
        
        print(f"✅ Generated {len(self.test_results)} Allure result files in {output_dir}")
        print(f"📊 Test Summary: {self.passed_tests}/{self.total_tests} passed")
        
        if self.failed_tests > 0:
            print(f"❌ {self.failed_tests} test(s) failed")
            return 1
        else:
            print(f"🎉 All tests passed!")
            return 0

def main():
    parser = argparse.ArgumentParser(description='Convert TAP output to Allure results')
    parser.add_argument('tap_file', help='Path to TAP output file')
    parser.add_argument('--output-dir', '-o', default='allure-results', 
                       help='Output directory for Allure results (default: allure-results)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        print(f"🔍 Reading TAP output from: {args.tap_file}")
        print(f"📁 Output directory: {args.output_dir}")
    
    # Read TAP content
    try:
        with open(args.tap_file, 'r') as f:
            tap_content = f.read()
    except FileNotFoundError:
        print(f"❌ Error: TAP file '{args.tap_file}' not found")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading TAP file: {e}")
        sys.exit(1)
    
    if args.verbose:
        print(f"📝 TAP content length: {len(tap_content)} characters")
    
    # Convert to Allure format
    converter = TAPToAllureConverter()
    converter.parse_tap_output(tap_content)
    exit_code = converter.generate_allure_results(args.output_dir)
    
    sys.exit(exit_code)

if __name__ == "__main__":
    main()