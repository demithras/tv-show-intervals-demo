#!/usr/bin/env python3
"""
pgbench Performance Test Runner for TV Show Intervals Demo.
Orchestrates pgbench execution and produces results compatible with the existing performance test framework.
"""

import os
import sys
import time
import json
import logging
import argparse
import subprocess
import tempfile
from pathlib import Path
from urllib.parse import urlparse
import psycopg2
from psycopg2.extras import RealDictCursor

# Import our existing data generator for setup
from performance_test_generator import TVProgramDataGenerator

logger = logging.getLogger(__name__)


class PgbenchPerformanceRunner:
    """Runs pgbench-based performance tests equivalent to the Python test suite."""
    
    def __init__(self, database_url, pgbench_tests_dir="pgbench-tests"):
        self.database_url = database_url
        self.pgbench_tests_dir = Path(pgbench_tests_dir)
        self.results = {}
        
        # Parse database URL for pgbench
        parsed = urlparse(database_url)
        self.pgbench_args = {
            'host': parsed.hostname,
            'port': parsed.port or 5432,
            'dbname': parsed.path.lstrip('/'),
            'user': parsed.username,
            'password': parsed.password
        }
        
        # Create database connection for setup
        self.db = psycopg2.connect(database_url)
        self.generator = TVProgramDataGenerator(self.db)

    def run_pgbench_test(self, test_file, clients=1, transactions=100, time_limit=None, 
                        description="pgbench test"):
        """Run a single pgbench test and return results."""
        
        # Build pgbench command
        cmd = [
            'pgbench',
            '-h', str(self.pgbench_args['host']),
            '-p', str(self.pgbench_args['port']),
            '-d', self.pgbench_args['dbname'],
            '-U', self.pgbench_args['user'],
            '-c', str(clients),  # number of concurrent clients
            '-j', str(min(clients, 4)),  # number of threads
            '-f', str(test_file),
            '--no-vacuum',  # Don't vacuum, we're testing existing data
            '--protocol=extended'  # Use extended protocol for better performance
        ]
        
        # Set connection limit: either by time or transactions
        if time_limit:
            cmd.extend(['-T', str(time_limit)])  # time-based
        else:
            cmd.extend(['-t', str(transactions)])  # transaction-based
        
        # Set environment for password
        env = os.environ.copy()
        if self.pgbench_args['password']:
            env['PGPASSWORD'] = self.pgbench_args['password']
        
        logger.info(f"Running {description}: {test_file.name}")
        logger.debug(f"pgbench command: {' '.join(cmd)}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                timeout=300  # 5-minute timeout
            )
            
            end_time = time.time()
            
            if result.returncode != 0:
                logger.error(f"pgbench failed for {test_file.name}: {result.stderr}")
                return {
                    'execution_time': end_time - start_time,
                    'error': result.stderr,
                    'success': False,
                    'description': description
                }
            
            # Parse pgbench output
            output_lines = result.stdout.strip().split('\n')
            pgbench_stats = self.parse_pgbench_output(output_lines)
            
            return {
                'execution_time': end_time - start_time,
                'pgbench_stats': pgbench_stats,
                'success': True,
                'description': description,
                'clients': clients,
                'transactions_per_client': transactions,
                'raw_output': result.stdout
            }
            
        except subprocess.TimeoutExpired:
            logger.error(f"pgbench timeout for {test_file.name}")
            return {
                'execution_time': 300,
                'error': 'Timeout after 300 seconds',
                'success': False,
                'description': description
            }
        except Exception as e:
            logger.error(f"Error running pgbench for {test_file.name}: {e}")
            return {
                'execution_time': time.time() - start_time,
                'error': str(e),
                'success': False,
                'description': description
            }

    def parse_pgbench_output(self, output_lines):
        """Parse pgbench output to extract performance metrics."""
        stats = {}
        
        for line in output_lines:
            line = line.strip()
            
            # Parse key metrics from pgbench output
            if 'number of transactions actually processed:' in line:
                stats['transactions_processed'] = int(line.split(':')[1].strip())
            elif 'latency average =' in line:
                # Extract latency value (format: "latency average = 123.456 ms")
                latency_part = line.split('=')[1].strip()
                stats['latency_avg_ms'] = float(latency_part.split()[0])
            elif 'initial connection time =' in line:
                conn_time = line.split('=')[1].strip()
                stats['connection_time_ms'] = float(conn_time.split()[0])
            elif 'tps =' in line:
                # Extract TPS (format: "tps = 123.456 (including connections establishing)")
                tps_part = line.split('=')[1].strip()
                stats['tps'] = float(tps_part.split()[0])
            elif 'number of failed transactions:' in line:
                stats['failed_transactions'] = int(line.split(':')[1].strip())
                
        return stats

    def test_basic_queries(self, clients=1, transactions=50):
        """Run basic query performance tests."""
        logger.info("=== Testing Basic Query Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "01-basic-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file, 
            clients=clients, 
            transactions=transactions,
            description="Basic queries (count, aggregations, top-N)"
        )
        
        self.results['basic_queries_pgbench'] = result

    def test_filtered_queries(self, clients=1, transactions=50):
        """Run filtered query performance tests."""
        logger.info("=== Testing Filtered Query Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "02-filtered-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="Filtered queries (WHERE clauses, indexes)"
        )
        
        self.results['filtered_queries_pgbench'] = result

    def test_aggregation_queries(self, clients=1, transactions=30):
        """Run aggregation performance tests."""
        logger.info("=== Testing Aggregation Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "03-aggregation-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="Complex aggregations (GROUP BY, HAVING)"
        )
        
        self.results['aggregation_queries_pgbench'] = result

    def test_join_performance(self, clients=1, transactions=40):
        """Run JOIN performance tests."""
        logger.info("=== Testing JOIN Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "04-join-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="JOIN queries (INNER, LEFT, with aggregations)"
        )
        
        self.results['join_performance_pgbench'] = result

    def test_update_performance(self, clients=1, transactions=20):
        """Run UPDATE performance tests."""
        logger.info("=== Testing UPDATE Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "05-update-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="UPDATE queries (single, batch, trigger overhead)"
        )
        
        self.results['update_performance_pgbench'] = result

    def test_index_effectiveness(self, clients=1, transactions=50):
        """Run index effectiveness tests."""
        logger.info("=== Testing Index Effectiveness (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "06-index-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="Index utilization tests"
        )
        
        self.results['index_effectiveness_pgbench'] = result

    def test_overnight_program_performance(self, clients=1, transactions=30):
        """Run overnight program performance tests."""
        logger.info("=== Testing Overnight Program Performance (pgbench) ===")
        
        test_file = self.pgbench_tests_dir / "07-overnight-queries.sql"
        if not test_file.exists():
            logger.error(f"Test file not found: {test_file}")
            return
        
        result = self.run_pgbench_test(
            test_file,
            clients=clients,
            transactions=transactions,
            description="Overnight program calculations"
        )
        
        self.results['overnight_performance_pgbench'] = result

    def run_concurrent_tests(self, clients=4, time_limit=60):
        """Run tests with multiple concurrent clients to test concurrency."""
        logger.info(f"=== Testing Concurrent Performance ({clients} clients, {time_limit}s) ===")
        
        # Run a subset of tests with higher concurrency
        concurrent_tests = [
            ("01-basic-queries.sql", "Concurrent basic queries"),
            ("02-filtered-queries.sql", "Concurrent filtered queries"),
            ("05-update-queries.sql", "Concurrent updates (contention test)")
        ]
        
        concurrent_results = {}
        
        for test_file, description in concurrent_tests:
            full_path = self.pgbench_tests_dir / test_file
            if full_path.exists():
                result = self.run_pgbench_test(
                    full_path,
                    clients=clients,
                    time_limit=time_limit,
                    description=f"{description} ({clients} clients)"
                )
                concurrent_results[test_file.replace('.sql', '')] = result
        
        self.results['concurrent_performance_pgbench'] = concurrent_results

    def generate_performance_report(self):
        """Generate a performance report compatible with the Python version."""
        logger.info("=== PGBENCH PERFORMANCE TEST REPORT ===")
        
        total_tests = 0
        total_execution_time = 0
        successful_tests = 0
        
        for category, result in self.results.items():
            logger.info(f"\n{category.upper().replace('_', ' ')}:")
            
            if isinstance(result, dict):
                if 'pgbench_stats' in result:
                    # Single test result
                    self.log_test_result(category, result)
                    total_tests += 1
                    total_execution_time += result['execution_time']
                    if result['success']:
                        successful_tests += 1
                else:
                    # Multiple test results (like concurrent tests)
                    for test_name, test_result in result.items():
                        self.log_test_result(f"{category}.{test_name}", test_result)
                        total_tests += 1
                        total_execution_time += test_result['execution_time']
                        if test_result['success']:
                            successful_tests += 1
        
        logger.info(f"\n=== PGBENCH SUMMARY ===")
        logger.info(f"Total tests executed: {total_tests}")
        logger.info(f"Successful tests: {successful_tests}")
        logger.info(f"Failed tests: {total_tests - successful_tests}")
        logger.info(f"Total execution time: {total_execution_time:.4f}s")
        logger.info(f"Average test time: {total_execution_time/total_tests:.4f}s" if total_tests > 0 else "No tests executed")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'total_time': total_execution_time,
                'average_time': total_execution_time/total_tests if total_tests > 0 else 0
            },
            'detailed_results': self.results
        }

    def log_test_result(self, test_name, result):
        """Log individual test result in a consistent format."""
        if result['success'] and 'pgbench_stats' in result:
            stats = result['pgbench_stats']
            tps = stats.get('tps', 0)
            latency = stats.get('latency_avg_ms', 0)
            transactions = stats.get('transactions_processed', 0)
            
            logger.info(
                f"  {test_name}: {result['execution_time']:.4f}s, "
                f"{tps:.2f} TPS, {latency:.2f}ms avg latency, {transactions} transactions"
            )
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.info(f"  {test_name}: FAILED - {error_msg}")

    def run_full_pgbench_suite(self, records=1000000, batch_size=10000, clients=1, 
                              skip_data_generation=False):
        """Run the complete pgbench performance test suite."""
        
        if not skip_data_generation:
            logger.info("Setting up database for pgbench performance testing...")
            self.generator.enhance_schema_for_performance()
            
            logger.info(f"Generating {records:,} test records...")
            self.generator.bulk_insert_programs(total_records=records, batch_size=batch_size)
        
        logger.info("Running pgbench performance tests...")
        
        # Calculate appropriate transaction counts based on dataset size
        base_transactions = max(10, min(100, records // 10000))
        
        # Run all test categories
        self.test_basic_queries(clients=clients, transactions=base_transactions)
        self.test_filtered_queries(clients=clients, transactions=base_transactions)
        self.test_aggregation_queries(clients=clients, transactions=max(10, base_transactions // 2))
        self.test_join_performance(clients=clients, transactions=base_transactions)
        self.test_index_effectiveness(clients=clients, transactions=base_transactions)
        self.test_update_performance(clients=clients, transactions=max(5, base_transactions // 4))
        self.test_overnight_program_performance(clients=clients, transactions=base_transactions)
        
        # Run concurrent tests if clients > 1
        if clients > 1:
            self.run_concurrent_tests(clients=clients, time_limit=30)
        
        # Generate comprehensive report
        report = self.generate_performance_report()
        
        return report

    def run_quick_pgbench_suite(self, records=50000, batch_size=5000, clients=1):
        """Run a quick pgbench performance test suite for CI/PR testing."""
        logger.info("Running quick pgbench performance test suite...")
        
        # Setup database
        self.generator.enhance_schema_for_performance()
        
        # Generate smaller dataset
        logger.info(f"Generating {records:,} test records...")
        self.generator.bulk_insert_programs(total_records=records, batch_size=batch_size)
        
        # Run essential tests only with fewer transactions
        self.test_basic_queries(clients=clients, transactions=20)
        self.test_filtered_queries(clients=clients, transactions=20)
        self.test_aggregation_queries(clients=clients, transactions=10)
        
        # Generate report
        report = self.generate_performance_report()
        
        return report


def main():
    """Main entry point for pgbench performance testing."""
    parser = argparse.ArgumentParser(description="Run pgbench-based performance tests")
    parser.add_argument('--database-url', required=True, help='PostgreSQL database URL')
    parser.add_argument('--records', type=int, default=500000, help='Number of records to generate')
    parser.add_argument('--batch-size', type=int, default=10000, help='Batch size for inserts')
    parser.add_argument('--clients', type=int, default=1, help='Number of concurrent pgbench clients')
    parser.add_argument('--test-type', choices=['full', 'quick'], default='quick', 
                       help='Type of test suite to run')
    parser.add_argument('--output-file', help='JSON output file for results')
    parser.add_argument('--skip-data-generation', action='store_true', 
                       help='Skip data generation (use existing data)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    try:
        # Create pgbench runner
        runner = PgbenchPerformanceRunner(args.database_url)
        
        # Run appropriate test suite
        if args.test_type == 'full':
            results = runner.run_full_pgbench_suite(
                records=args.records,
                batch_size=args.batch_size,
                clients=args.clients,
                skip_data_generation=args.skip_data_generation
            )
        else:
            results = runner.run_quick_pgbench_suite(
                records=min(args.records, 50000),
                batch_size=args.batch_size,
                clients=args.clients
            )
        
        # Save results if requested
        if args.output_file:
            with open(args.output_file, 'w') as f:
                json.dump(results, f, indent=2, default=str)
            logger.info(f"Results saved to {args.output_file}")
        
        # Print summary
        summary = results['summary']
        print(f"\n=== PGBENCH PERFORMANCE SUMMARY ===")
        print(f"Tests: {summary['successful_tests']}/{summary['total_tests']} successful")
        print(f"Total time: {summary['total_time']:.2f}s")
        print(f"Average time per test: {summary['average_time']:.4f}s")
        
        # Exit with error code if any tests failed
        sys.exit(0 if summary['failed_tests'] == 0 else 1)
        
    except Exception as e:
        logger.error(f"Error running pgbench performance tests: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()