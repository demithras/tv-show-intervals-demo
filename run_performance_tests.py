"""
CI-optimized performance test runner with multiple output formats and test types.
Main entry point for running performance tests in both local and CI environments.
"""

import argparse
import json
import logging
import os
import sys
import time
from pathlib import Path
from performance_tests import PerformanceTestSuite
from performance_test_generator import TVProgramDataGenerator
import psycopg2
from urllib.parse import urlparse


def get_db_connection():
    """Get database connection (CI-compatible)."""
    database_url = os.getenv('DATABASE_URL')
    
    if database_url:
        url_parts = urlparse(database_url)
        return psycopg2.connect(
            host=url_parts.hostname,
            port=url_parts.port,
            database=url_parts.path[1:],
            user=url_parts.username,
            password=url_parts.password,
            sslmode='require'
        )
    else:
        return psycopg2.connect(
            host=os.getenv('DB_HOST', 'localhost'),
            port=os.getenv('DB_PORT', '5432'),
            database=os.getenv('DB_NAME', 'demo'),
            user=os.getenv('DB_USER', 'demo'),
            password=os.getenv('DB_PASSWORD', 'demo_password')
        )


def run_test_suite(test_type, records, batch_size, db_connection):
    """Run performance tests based on type."""
    suite = PerformanceTestSuite(db_connection)
    
    logger = logging.getLogger(__name__)
    logger.info(f"Running {test_type} performance tests with {records:,} records")
    
    start_time = time.time()
    
    if test_type == 'full':
        report = suite.run_full_performance_suite(records=records, batch_size=batch_size, skip_data_generation=False)
    elif test_type == 'quick':
        report = suite.run_quick_performance_suite(records=records, batch_size=batch_size)
    elif test_type == 'insert-only':
        # Only test data generation performance
        suite.generator.enhance_schema_for_performance()
        insert_time, insert_rate = suite.generator.bulk_insert_programs(
            total_records=records,
            batch_size=batch_size
        )
        report = {
            'summary': {
                'total_tests': 1,
                'total_time': insert_time,
                'average_time': insert_time
            },
            'detailed_results': {
                'data_generation': {
                    'total_records': records,
                    'batch_size': batch_size,
                    'total_time': insert_time,
                    'records_per_second': insert_rate
                }
            }
        }
    elif test_type == 'query-only':
        # Skip data generation, run queries on existing data
        logger.info("Running query-only tests on existing data...")
        suite.test_basic_queries()
        suite.test_filtered_queries()
        suite.test_aggregation_queries()
        suite.test_join_performance()
        suite.test_index_effectiveness()
        
        report = suite.generate_performance_report()
    else:
        raise ValueError(f"Unknown test type: {test_type}")
    
    total_execution_time = time.time() - start_time
    
    # Add metadata to report
    if 'summary' not in report:
        report['summary'] = {}
    
    report['meta'] = {
        'total_execution_time': total_execution_time,
        'test_type': test_type,
        'test_parameters': {
            'records': records,
            'batch_size': batch_size
        },
        'timestamp': time.time(),
        'iso_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
        'ci_environment': bool(os.getenv('CI')),
        'github_run_number': os.getenv('GITHUB_RUN_NUMBER'),
        'github_sha': os.getenv('GITHUB_SHA'),
        'github_ref': os.getenv('GITHUB_REF'),
        'database_url_host': urlparse(os.getenv('DATABASE_URL', '')).hostname if os.getenv('DATABASE_URL') else 'localhost'
    }
    
    return report


def format_results_for_ci(results, output_format='json'):
    """Format results for CI consumption."""
    if output_format == 'json':
        return json.dumps(results, indent=2, default=str)
    
    elif output_format == 'github':
        # GitHub Actions summary format
        summary = []
        summary.append("## 📊 Performance Test Results")
        
        meta = results.get('meta', {})
        summary.append(f"- **Test Type**: {meta.get('test_type', 'unknown')}")
        summary.append(f"- **Total Execution Time**: {meta.get('total_execution_time', 0):.2f}s")
        summary.append(f"- **Timestamp**: {meta.get('iso_timestamp', 'unknown')}")
        
        if 'test_parameters' in meta:
            params = meta['test_parameters']
            summary.append(f"- **Records**: {params.get('records', 0):,}")
            summary.append(f"- **Batch Size**: {params.get('batch_size', 0):,}")
        
        # Data generation results
        detailed = results.get('detailed_results', {})
        if 'data_generation' in detailed:
            dg = detailed['data_generation']
            if not dg.get('skipped'):
                summary.append(f"\n### 🚀 Data Generation")
                summary.append(f"- **Records Generated**: {dg.get('total_records', 0):,}")
                summary.append(f"- **Generation Time**: {dg.get('total_time', 0):.2f}s")
                summary.append(f"- **Insert Rate**: {dg.get('records_per_second', 0):,.0f} records/sec")
        
        # Query performance results
        if 'basic_queries' in detailed:
            summary.append(f"\n### 🔍 Query Performance")
            for test_name, result in detailed['basic_queries'].items():
                if isinstance(result, dict) and 'execution_time' in result:
                    summary.append(f"- **{test_name}**: {result['execution_time']:.4f}s ({result['row_count']:,} rows)")
        
        # Aggregation results
        if 'aggregation_queries' in detailed:
            summary.append(f"\n### 📈 Aggregation Performance")
            agg_times = []
            for test_name, result in detailed['aggregation_queries'].items():
                if isinstance(result, dict) and 'execution_time' in result:
                    agg_times.append(result['execution_time'])
                    summary.append(f"- **{test_name}**: {result['execution_time']:.4f}s")
            
            if agg_times:
                avg_agg_time = sum(agg_times) / len(agg_times)
                summary.append(f"- **Average Aggregation Time**: {avg_agg_time:.4f}s")
        
        # Update performance
        if 'update_performance' in detailed:
            update_perf = detailed['update_performance']
            summary.append(f"\n### ⚡ Update Performance")
            summary.append(f"- **Single Update Average**: {update_perf.get('single_update_avg', 0):.4f}s")
            summary.append(f"- **Single Update Median**: {update_perf.get('single_update_median', 0):.4f}s")
            
            if 'batch_updates' in update_perf:
                for update_type, batch_result in update_perf['batch_updates'].items():
                    summary.append(f"- **{update_type}**: {batch_result['time']:.4f}s ({batch_result['rows_updated']} rows)")
        
        # Overall summary
        if 'summary' in results:
            summary_data = results['summary']
            summary.append(f"\n### 📋 Test Summary")
            summary.append(f"- **Total Tests**: {summary_data.get('total_tests', 0)}")
            summary.append(f"- **Total Query Time**: {summary_data.get('total_time', 0):.4f}s")
            if summary_data.get('total_tests', 0) > 0:
                summary.append(f"- **Average Query Time**: {summary_data.get('average_time', 0):.4f}s")
        
        return "\n".join(summary)
    
    elif output_format == 'console':
        # Console-friendly format
        lines = []
        lines.append("=" * 60)
        lines.append("PERFORMANCE TEST RESULTS")
        lines.append("=" * 60)
        
        meta = results.get('meta', {})
        lines.append(f"Test Type: {meta.get('test_type', 'unknown')}")
        lines.append(f"Execution Time: {meta.get('total_execution_time', 0):.2f}s")
        lines.append(f"Timestamp: {meta.get('iso_timestamp', 'unknown')}")
        
        if 'test_parameters' in meta:
            params = meta['test_parameters']
            lines.append(f"Records: {params.get('records', 0):,}")
            lines.append(f"Batch Size: {params.get('batch_size', 0):,}")
        
        lines.append("")
        
        # Show key metrics
        detailed = results.get('detailed_results', {})
        
        if 'data_generation' in detailed:
            dg = detailed['data_generation']
            if not dg.get('skipped'):
                lines.append("DATA GENERATION:")
                lines.append(f"  Records: {dg.get('total_records', 0):,}")
                lines.append(f"  Time: {dg.get('total_time', 0):.2f}s")
                lines.append(f"  Rate: {dg.get('records_per_second', 0):,.0f} records/sec")
                lines.append("")
        
        for category in ['basic_queries', 'filtered_queries', 'aggregation_queries', 'join_performance']:
            if category in detailed:
                lines.append(f"{category.upper().replace('_', ' ')}:")
                for test_name, result in detailed[category].items():
                    if isinstance(result, dict) and 'execution_time' in result:
                        lines.append(f"  {test_name}: {result['execution_time']:.4f}s ({result['row_count']:,} rows)")
                lines.append("")
        
        lines.append("=" * 60)
        return "\n".join(lines)
    
    return str(results)


def setup_logging(log_level='INFO', log_file=None):
    """Setup logging for both console and file output."""
    numeric_level = getattr(logging, log_level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f'Invalid log level: {log_level}')
    
    handlers = [logging.StreamHandler(sys.stdout)]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    elif not os.getenv('CI'):
        # Add file handler for local development
        handlers.append(logging.FileHandler('performance.log'))
    
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )


def main():
    parser = argparse.ArgumentParser(
        description='TV Show Intervals Performance Tests',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full performance test with 1M records
  python run_performance_tests.py --records 1000000 --test-type full
  
  # Quick test for CI/PR
  python run_performance_tests.py --records 50000 --test-type quick
  
  # Test only data insertion
  python run_performance_tests.py --records 100000 --test-type insert-only
  
  # Test queries on existing data
  python run_performance_tests.py --test-type query-only
        """
    )
    
    parser.add_argument('--records', type=int, default=100000,
                       help='Number of records to generate (default: 100,000)')
    parser.add_argument('--batch-size', type=int, default=5000,
                       help='Batch size for inserts (default: 5,000)')
    parser.add_argument('--test-type', 
                       choices=['full', 'quick', 'insert-only', 'query-only'], 
                       default='quick',
                       help='Type of performance test to run (default: quick)')
    parser.add_argument('--output-format', 
                       choices=['json', 'github', 'console'], 
                       default='console',
                       help='Output format (default: console)')
    parser.add_argument('--output-file', 
                       help='Output file for results (default: stdout)')
    parser.add_argument('--timeout', type=int, default=3600,
                       help='Timeout in seconds (default: 3600)')
    parser.add_argument('--log-level', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO',
                       help='Logging level (default: INFO)')
    parser.add_argument('--log-file',
                       help='Log file path (default: performance.log for local, none for CI)')
    parser.add_argument('--cleanup', action='store_true',
                       help='Clean up test data after completion')
    parser.add_argument('--skip-schema-setup', action='store_true',
                       help='Skip schema enhancement setup')
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.log_level, args.log_file)
    logger = logging.getLogger(__name__)
    
    logger.info(f"Starting performance tests: {args.test_type} with {args.records:,} records")
    logger.info(f"Configuration: batch_size={args.batch_size}, timeout={args.timeout}s, output={args.output_format}")
    
    try:
        # Set timeout alarm for CI
        if os.getenv('CI') and args.timeout > 0:
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError(f"Performance test timed out after {args.timeout} seconds")
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(args.timeout)
        
        # Connect to database
        logger.info("Connecting to database...")
        db_connection = get_db_connection()
        logger.info("Database connection established")
        
        # Run tests
        start_time = time.time()
        results = run_test_suite(args.test_type, args.records, args.batch_size, db_connection)
        total_time = time.time() - start_time
        
        logger.info(f"Performance tests completed in {total_time:.2f} seconds")
        
        # Cleanup if requested
        if args.cleanup:
            logger.info("Cleaning up test data...")
            generator = TVProgramDataGenerator(db_connection)
            cleaned_count = generator.cleanup_test_data()
            logger.info(f"Cleaned up {cleaned_count:,} test records")
        
        # Format and output results
        formatted_results = format_results_for_ci(results, args.output_format)
        
        if args.output_file:
            Path(args.output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output_file, 'w') as f:
                f.write(formatted_results)
            logger.info(f"Results written to {args.output_file}")
        
        if args.output_format == 'console' or not args.output_file:
            print(formatted_results)
        
        # GitHub Actions summary
        if os.getenv('GITHUB_STEP_SUMMARY'):
            github_summary = format_results_for_ci(results, 'github')
            with open(os.getenv('GITHUB_STEP_SUMMARY'), 'a') as f:
                f.write(github_summary + '\n')
        
        # Set GitHub Actions outputs
        if os.getenv('GITHUB_OUTPUT'):
            with open(os.getenv('GITHUB_OUTPUT'), 'a') as f:
                summary = results.get('summary', {})
                f.write(f"total_tests={summary.get('total_tests', 0)}\n")
                f.write(f"total_time={summary.get('total_time', 0):.4f}\n")
                f.write(f"execution_time={total_time:.4f}\n")
                
                # Add data generation metrics if available
                detailed = results.get('detailed_results', {})
                if 'data_generation' in detailed:
                    dg = detailed['data_generation']
                    f.write(f"records_generated={dg.get('total_records', 0)}\n")
                    f.write(f"insert_rate={dg.get('records_per_second', 0):.0f}\n")
        
        logger.info("Performance tests completed successfully!")
        
    except KeyboardInterrupt:
        logger.warning("Performance tests interrupted by user")
        sys.exit(130)  # Standard exit code for SIGINT
    except TimeoutError as e:
        logger.error(f"Performance tests timed out: {e}")
        sys.exit(124)  # Standard exit code for timeout
    except Exception as e:
        logger.error(f"Performance test failed: {e}")
        if args.log_level == 'DEBUG':
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)
    finally:
        if 'db_connection' in locals():
            db_connection.close()
            logger.debug("Database connection closed")


if __name__ == '__main__':
    main()