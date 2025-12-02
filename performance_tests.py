"""
Comprehensive performance test suite for TV Show Intervals Demo.
Tests various scenarios to demonstrate system performance characteristics.
"""

import time
import statistics
import psycopg2
from psycopg2.extras import RealDictCursor
import logging
from performance_test_generator import TVProgramDataGenerator

logger = logging.getLogger(__name__)


class PerformanceTestSuite:
    def __init__(self, db_connection):
        self.db = db_connection
        self.generator = TVProgramDataGenerator(db_connection)
        self.results = {}

    def time_query(self, query, params=None, description="Query", fetch_all=True):
        """Execute a query and measure its performance."""
        with self.db.cursor(cursor_factory=RealDictCursor) as cursor:
            start_time = time.time()
            cursor.execute(query, params or ())
            
            if fetch_all:
                results = cursor.fetchall()
                row_count = len(results)
            else:
                # For queries where we don't need to fetch all results (like large result sets)
                row_count = cursor.rowcount if cursor.rowcount >= 0 else 0
            
            end_time = time.time()
            
            execution_time = end_time - start_time
            logger.info(f"{description}: {execution_time:.4f}s, {row_count:,} rows")
            
            return {
                'execution_time': execution_time,
                'row_count': row_count,
                'rows_per_second': row_count / execution_time if execution_time > 0 else 0,
                'description': description
            }

    def test_basic_queries(self):
        """Test basic query performance on large dataset."""
        logger.info("=== Testing Basic Query Performance ===")
        
        queries = [
            ("SELECT COUNT(*) FROM programs", "Count all programs"),
            ("SELECT COUNT(*) FROM program_intervals", "Count all intervals"),
            ("SELECT program_name, interval_count FROM program_intervals ORDER BY interval_count DESC LIMIT 100", "Top 100 by intervals"),
            ("SELECT category, COUNT(*) FROM programs WHERE category IS NOT NULL GROUP BY category ORDER BY COUNT(*) DESC", "Programs by category"),
            ("SELECT channel_id, COUNT(*) FROM programs WHERE channel_id IS NOT NULL GROUP BY channel_id ORDER BY COUNT(*) DESC LIMIT 10", "Top 10 channels by program count"),
            ("SELECT day_of_week, COUNT(*) FROM programs WHERE day_of_week IS NOT NULL GROUP BY day_of_week ORDER BY day_of_week", "Programs by day of week"),
            ("SELECT priority, COUNT(*) FROM programs WHERE priority IS NOT NULL GROUP BY priority ORDER BY priority", "Programs by priority"),
        ]
        
        self.results['basic_queries'] = {}
        for query, description in queries:
            result = self.time_query(query, description=description)
            self.results['basic_queries'][description] = result

    def test_filtered_queries(self):
        """Test performance of filtered queries using indexes."""
        logger.info("=== Testing Filtered Query Performance ===")
        
        queries = [
            ("SELECT * FROM programs WHERE category = %s", ('News',), "Filter by category (News)"),
            ("SELECT * FROM programs WHERE channel_id BETWEEN %s AND %s", (1, 50), "Filter by channel range (1-50)"),
            ("SELECT * FROM programs WHERE day_of_week = %s AND priority = %s", (1, 1), "Filter by day and priority"),
            ("SELECT * FROM programs WHERE start_time >= %s AND start_time < %s", ('18:00', '22:00'), "Prime time programs (6-10 PM)"),
            ("SELECT * FROM programs WHERE category = %s AND channel_id BETWEEN %s AND %s", ('Sports', 1, 100), "Sports on channels 1-100"),
            ("SELECT p.*, pi.interval_count FROM programs p JOIN program_intervals pi ON p.program_name = pi.program_name WHERE p.category = %s AND pi.interval_count > %s", ('Movies', 5), "Movies longer than 5 intervals"),
            ("SELECT * FROM programs WHERE start_time > end_time", (), "Overnight programs"),
        ]
        
        self.results['filtered_queries'] = {}
        for query, params, description in queries:
            result = self.time_query(query, params, description)
            self.results['filtered_queries'][description] = result

    def test_aggregation_queries(self):
        """Test complex aggregation performance."""
        logger.info("=== Testing Aggregation Performance ===")
        
        queries = [
            ("""
            SELECT 
                category,
                AVG(interval_count) as avg_intervals,
                MAX(interval_count) as max_intervals,
                MIN(interval_count) as min_intervals,
                COUNT(*) as program_count
            FROM programs p 
            JOIN program_intervals pi ON p.program_name = pi.program_name 
            WHERE p.category IS NOT NULL
            GROUP BY category 
            ORDER BY avg_intervals DESC
            """, "Category statistics with intervals"),
            
            ("""
            SELECT 
                channel_id,
                day_of_week,
                COUNT(*) as program_count,
                SUM(interval_count) as total_intervals,
                AVG(interval_count) as avg_intervals
            FROM programs p 
            JOIN program_intervals pi ON p.program_name = pi.program_name 
            WHERE p.channel_id IS NOT NULL AND p.day_of_week IS NOT NULL
            GROUP BY channel_id, day_of_week 
            HAVING COUNT(*) > 5
            ORDER BY total_intervals DESC 
            LIMIT 100
            """, "Channel-day analysis (top 100)"),
            
            ("""
            SELECT 
                EXTRACT(HOUR FROM start_time) as hour,
                COUNT(*) as programs_starting,
                AVG(interval_count) as avg_duration,
                COUNT(DISTINCT category) as unique_categories
            FROM programs p 
            JOIN program_intervals pi ON p.program_name = pi.program_name 
            GROUP BY EXTRACT(HOUR FROM start_time) 
            ORDER BY hour
            """, "Hourly program distribution with duration"),
            
            ("""
            SELECT 
                category,
                priority,
                COUNT(*) as program_count,
                AVG(interval_count) as avg_intervals,
                STDDEV(interval_count) as stddev_intervals
            FROM programs p 
            JOIN program_intervals pi ON p.program_name = pi.program_name 
            WHERE p.category IS NOT NULL AND p.priority IS NOT NULL
            GROUP BY category, priority
            ORDER BY category, priority
            """, "Category-priority cross-analysis"),
            
            ("""
            SELECT 
                day_of_week,
                COUNT(CASE WHEN start_time > end_time THEN 1 END) as overnight_programs,
                COUNT(*) as total_programs,
                ROUND(100.0 * COUNT(CASE WHEN start_time > end_time THEN 1 END) / COUNT(*), 2) as overnight_percentage
            FROM programs
            WHERE day_of_week IS NOT NULL
            GROUP BY day_of_week
            ORDER BY day_of_week
            """, "Overnight programs by day of week"),
        ]
        
        self.results['aggregation_queries'] = {}
        for query, description in queries:
            result = self.time_query(query, description=description)
            self.results['aggregation_queries'][description] = result

    def test_update_performance(self):
        """Test trigger performance during updates."""
        logger.info("=== Testing Update/Trigger Performance ===")
        
        # Test single updates
        single_update_times = []
        with self.db.cursor() as cursor:
            # Get a sample of program names for testing
            cursor.execute("SELECT program_name FROM programs LIMIT 100")
            program_names = [row[0] for row in cursor.fetchall()]
            
            for program_name in program_names:
                start_time = time.time()
                cursor.execute(
                    "UPDATE programs SET priority = %s WHERE program_name = %s",
                    (2, program_name)
                )
                self.db.commit()
                end_time = time.time()
                
                single_update_times.append(end_time - start_time)
        
        # Test batch updates
        batch_update_results = {}
        
        # Update by category
        start_time = time.time()
        with self.db.cursor() as cursor:
            cursor.execute("UPDATE programs SET priority = 3 WHERE category = %s", ('News',))
            updated_count = cursor.rowcount
            self.db.commit()
        batch_update_time = time.time() - start_time
        batch_update_results['category_update'] = {
            'time': batch_update_time,
            'rows_updated': updated_count,
            'rows_per_second': updated_count / batch_update_time if batch_update_time > 0 else 0
        }
        
        # Update by channel range
        start_time = time.time()
        with self.db.cursor() as cursor:
            cursor.execute("UPDATE programs SET priority = 1 WHERE channel_id BETWEEN %s AND %s", (1, 50))
            updated_count = cursor.rowcount
            self.db.commit()
        batch_update_time = time.time() - start_time
        batch_update_results['channel_range_update'] = {
            'time': batch_update_time,
            'rows_updated': updated_count,
            'rows_per_second': updated_count / batch_update_time if batch_update_time > 0 else 0
        }
        
        self.results['update_performance'] = {
            'single_update_avg': statistics.mean(single_update_times),
            'single_update_median': statistics.median(single_update_times),
            'single_update_min': min(single_update_times),
            'single_update_max': max(single_update_times),
            'batch_updates': batch_update_results
        }
        
        logger.info(f"Single update avg: {self.results['update_performance']['single_update_avg']:.4f}s")
        logger.info(f"Single update median: {self.results['update_performance']['single_update_median']:.4f}s")
        for update_type, result in batch_update_results.items():
            logger.info(f"{update_type}: {result['time']:.4f}s ({result['rows_updated']} rows, {result['rows_per_second']:.0f} rows/sec)")

    def test_overnight_program_performance(self):
        """Test performance of overnight program calculations."""
        logger.info("=== Testing Overnight Program Performance ===")
        
        # Insert specific overnight programs for testing
        overnight_programs = [
            (f"Overnight Performance Test {i}", "23:30", "00:15", 999, "Test", 1, 1)
            for i in range(1000)
        ]
        
        with self.db.cursor() as cursor:
            start_time = time.time()
            cursor.executemany(
                "INSERT INTO programs (program_name, start_time, end_time, channel_id, category, priority, day_of_week) VALUES (%s, %s, %s, %s, %s, %s, %s)",
                overnight_programs
            )
            self.db.commit()
            end_time = time.time()
        
        insert_time = end_time - start_time
        insert_rate = len(overnight_programs) / insert_time if insert_time > 0 else 0
        
        # Query overnight programs
        query_result = self.time_query(
            "SELECT * FROM programs WHERE start_time > end_time",
            description="Find all overnight programs"
        )
        
        # Test interval calculation for overnight programs
        interval_query_result = self.time_query(
            """
            SELECT p.program_name, p.start_time, p.end_time, pi.interval_count
            FROM programs p 
            JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE p.start_time > p.end_time
            """,
            description="Overnight programs with interval calculations"
        )
        
        # Test the count_15min_intervals function directly
        function_test_times = []
        with self.db.cursor() as cursor:
            test_cases = [
                ("23:30", "00:15"),  # 45 minutes overnight
                ("23:45", "00:30"),  # 45 minutes overnight
                ("22:00", "02:00"),  # 4 hours overnight
                ("23:00", "01:00"),  # 2 hours overnight
            ]
            
            for start_time, end_time in test_cases:
                start = time.time()
                cursor.execute("SELECT count_15min_intervals(%s::time, %s::time)", (start_time, end_time))
                result = cursor.fetchone()[0]
                end = time.time()
                function_test_times.append(end - start)
                logger.info(f"Function test {start_time}-{end_time}: {result} intervals in {end - start:.6f}s")
        
        self.results['overnight_performance'] = {
            'insert_time': insert_time,
            'insert_rate': insert_rate,
            'insert_count': len(overnight_programs),
            'query_result': query_result,
            'interval_query_result': interval_query_result,
            'function_performance': {
                'avg_time': statistics.mean(function_test_times),
                'min_time': min(function_test_times),
                'max_time': max(function_test_times),
                'test_count': len(function_test_times)
            }
        }
        
        logger.info(f"Overnight insert: {insert_time:.4f}s ({insert_rate:.0f} records/sec)")
        logger.info(f"Function avg time: {statistics.mean(function_test_times):.6f}s")

    def test_join_performance(self):
        """Test JOIN performance between programs and intervals tables."""
        logger.info("=== Testing JOIN Performance ===")
        
        queries = [
            ("""
            SELECT p.program_name, p.category, pi.interval_count
            FROM programs p
            INNER JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE p.category = %s
            """, ('Movies',), "Inner join programs-intervals filtered by category"),
            
            ("""
            SELECT p.*, pi.interval_count
            FROM programs p
            LEFT JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE p.channel_id BETWEEN %s AND %s
            """, (1, 100), "Left join programs-intervals filtered by channel"),
            
            ("""
            SELECT 
                p.category,
                COUNT(p.program_name) as program_count,
                SUM(pi.interval_count) as total_intervals,
                AVG(pi.interval_count) as avg_intervals_per_program
            FROM programs p
            INNER JOIN program_intervals pi ON p.program_name = pi.program_name
            WHERE p.category IS NOT NULL
            GROUP BY p.category
            HAVING SUM(pi.interval_count) > 1000
            ORDER BY total_intervals DESC
            """, (), "Join with aggregation and HAVING clause"),
        ]
        
        self.results['join_performance'] = {}
        for query, params, description in queries:
            result = self.time_query(query, params, description)
            self.results['join_performance'][description] = result

    def test_index_effectiveness(self):
        """Test query performance with and without specific indexes."""
        logger.info("=== Testing Index Effectiveness ===")
        
        # Test queries that should benefit from indexes
        index_test_queries = [
            ("SELECT * FROM programs WHERE category = %s", ('Sports',), "Category filter (should use idx_programs_category)"),
            ("SELECT * FROM programs WHERE channel_id = %s", (100,), "Channel filter (should use idx_programs_channel)"),
            ("SELECT * FROM programs WHERE day_of_week = %s", (1,), "Day filter (should use idx_programs_day)"),
            ("SELECT * FROM programs WHERE channel_id = %s AND day_of_week = %s AND start_time >= %s", (50, 1, '18:00'), "Composite index test"),
        ]
        
        self.results['index_effectiveness'] = {}
        for query, params, description in index_test_queries:
            # Time the query
            result = self.time_query(query, params, description)
            
            # Get query plan (EXPLAIN)
            with self.db.cursor() as cursor:
                explain_query = f"EXPLAIN (ANALYZE, BUFFERS) {query}"
                cursor.execute(explain_query, params)
                explain_result = cursor.fetchall()
                result['explain_plan'] = [row[0] for row in explain_result]
            
            self.results['index_effectiveness'][description] = result

    def generate_performance_report(self):
        """Generate a comprehensive performance report."""
        logger.info("=== PERFORMANCE TEST REPORT ===")
        
        total_tests = 0
        total_time = 0
        
        for category, tests in self.results.items():
            logger.info(f"\n{category.upper().replace('_', ' ')}:")
            category_tests = 0
            category_time = 0
            
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    if isinstance(result, dict) and 'execution_time' in result:
                        logger.info(f"  {test_name}: {result['execution_time']:.4f}s ({result['row_count']:,} rows)")
                        category_tests += 1
                        category_time += result['execution_time']
                        total_tests += 1
                        total_time += result['execution_time']
                    elif test_name == 'batch_updates' and isinstance(result, dict):
                        for update_type, update_result in result.items():
                            logger.info(f"  {update_type}: {update_result['time']:.4f}s ({update_result['rows_updated']} rows)")
                    else:
                        logger.info(f"  {test_name}: {result}")
            
            if category_tests > 0:
                logger.info(f"  Category total: {category_tests} tests, {category_time:.4f}s")
        
        logger.info(f"\n=== SUMMARY ===")
        logger.info(f"Total tests executed: {total_tests}")
        logger.info(f"Total execution time: {total_time:.4f}s")
        logger.info(f"Average test time: {total_time/total_tests:.4f}s" if total_tests > 0 else "No tests executed")
        
        return {
            'summary': {
                'total_tests': total_tests,
                'total_time': total_time,
                'average_time': total_time/total_tests if total_tests > 0 else 0
            },
            'detailed_results': self.results
        }

    def run_full_performance_suite(self, records=1000000, batch_size=10000, skip_data_generation=False):
        """Run the complete performance test suite."""
        if not skip_data_generation:
            logger.info("Enhancing schema for performance testing...")
            self.generator.enhance_schema_for_performance()
            
            logger.info("Generating test data...")
            self.generator.bulk_insert_programs(total_records=records, batch_size=batch_size)
        
        logger.info("Running performance tests...")
        
        # Run all test categories
        self.test_basic_queries()
        self.test_filtered_queries() 
        self.test_aggregation_queries()
        self.test_join_performance()
        self.test_index_effectiveness()
        self.test_update_performance()
        self.test_overnight_program_performance()
        
        # Generate comprehensive report
        report = self.generate_performance_report()
        
        return report

    def run_quick_performance_suite(self, records=50000, batch_size=5000):
        """Run a quick performance test suite for CI/PR testing."""
        logger.info("Running quick performance test suite...")
        
        # Enhance schema
        self.generator.enhance_schema_for_performance()
        
        # Generate smaller dataset
        logger.info(f"Generating {records:,} test records...")
        self.generator.bulk_insert_programs(total_records=records, batch_size=batch_size)
        
        # Run essential tests only
        self.test_basic_queries()
        self.test_filtered_queries()
        self.test_aggregation_queries()
        
        # Generate report
        report = self.generate_performance_report()
        
        return report