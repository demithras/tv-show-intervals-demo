#!/usr/bin/env python3
"""
Performance Test Comparison Utility for TV Show Intervals Demo.
Compares results between Python and pgbench test runs to validate consistency.
"""

import json
import argparse
import logging
from pathlib import Path
from datetime import datetime
import statistics

logger = logging.getLogger(__name__)


class PerformanceComparer:
    """Compares performance test results between Python and pgbench implementations."""
    
    def __init__(self):
        self.comparison_results = {}
    
    def load_results(self, python_file, pgbench_file):
        """Load results from both test engines."""
        try:
            with open(python_file, 'r') as f:
                python_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load Python results from {python_file}: {e}")
            python_data = None
        
        try:
            with open(pgbench_file, 'r') as f:
                pgbench_data = json.load(f)
        except Exception as e:
            logger.error(f"Failed to load pgbench results from {pgbench_file}: {e}")
            pgbench_data = None
        
        return python_data, pgbench_data
    
    def compare_query_performance(self, python_data, pgbench_data):
        """Compare query performance between the two engines."""
        comparisons = {}
        
        if not python_data or not pgbench_data:
            logger.warning("Missing data for query performance comparison")
            return comparisons
        
        # Map similar test categories
        category_mapping = {
            'basic_queries': 'basic_queries_pgbench',
            'filtered_queries': 'filtered_queries_pgbench', 
            'aggregation_queries': 'aggregation_queries_pgbench',
            'join_performance': 'join_performance_pgbench',
            'overnight_performance': 'overnight_performance_pgbench',
            'index_effectiveness': 'index_effectiveness_pgbench'
        }
        
        python_results = python_data.get('detailed_results', {})
        pgbench_results = pgbench_data.get('detailed_results', {})
        
        for python_category, pgbench_category in category_mapping.items():
            if python_category in python_results and pgbench_category in pgbench_results:
                comparison = self.compare_category(
                    python_results[python_category],
                    pgbench_results[pgbench_category],
                    python_category
                )
                if comparison:
                    comparisons[python_category] = comparison
        
        return comparisons
    
    def compare_category(self, python_tests, pgbench_result, category_name):
        """Compare a specific test category between engines."""
        if not isinstance(python_tests, dict) or not isinstance(pgbench_result, dict):
            return None
        
        # Extract timing information
        python_times = []
        python_total_time = 0
        
        for test_name, result in python_tests.items():
            if isinstance(result, dict) and 'execution_time' in result:
                python_times.append(result['execution_time'])
                python_total_time += result['execution_time']
            elif isinstance(result, (int, float)):
                python_times.append(result)
                python_total_time += result
        
        # Get pgbench timing
        pgbench_time = pgbench_result.get('execution_time', 0)
        pgbench_stats = pgbench_result.get('pgbench_stats', {})
        
        if not python_times or pgbench_time <= 0:
            return None
        
        # Calculate comparison metrics
        python_avg = statistics.mean(python_times) if python_times else 0
        python_median = statistics.median(python_times) if python_times else 0
        
        comparison = {
            'category': category_name,
            'python_stats': {
                'total_time': python_total_time,
                'average_time': python_avg,
                'median_time': python_median,
                'test_count': len(python_times),
                'min_time': min(python_times) if python_times else 0,
                'max_time': max(python_times) if python_times else 0
            },
            'pgbench_stats': {
                'execution_time': pgbench_time,
                'tps': pgbench_stats.get('tps', 0),
                'latency_ms': pgbench_stats.get('latency_avg_ms', 0),
                'transactions': pgbench_stats.get('transactions_processed', 0),
                'failed_transactions': pgbench_stats.get('failed_transactions', 0)
            },
            'comparison': {
                'time_ratio': pgbench_time / python_avg if python_avg > 0 else 0,
                'performance_difference_pct': ((pgbench_time - python_avg) / python_avg * 100) if python_avg > 0 else 0
            }
        }
        
        # Add insights
        insights = []
        if comparison['comparison']['time_ratio'] < 0.5:
            insights.append("pgbench significantly faster (>50% improvement)")
        elif comparison['comparison']['time_ratio'] < 0.8:
            insights.append("pgbench moderately faster")
        elif comparison['comparison']['time_ratio'] > 1.5:
            insights.append("Python implementation faster")
        else:
            insights.append("Performance similar between engines")
        
        if pgbench_stats.get('failed_transactions', 0) > 0:
            insights.append(f"pgbench had {pgbench_stats['failed_transactions']} failed transactions")
        
        comparison['insights'] = insights
        
        return comparison
    
    def compare_overall_performance(self, python_data, pgbench_data):
        """Compare overall performance metrics."""
        if not python_data or not pgbench_data:
            return {}
        
        python_summary = python_data.get('summary', {})
        pgbench_summary = pgbench_data.get('summary', {})
        
        return {
            'python_total_time': python_summary.get('total_time', 0),
            'python_test_count': python_summary.get('total_tests', 0),
            'python_avg_time': python_summary.get('average_time', 0),
            'pgbench_total_time': pgbench_summary.get('total_time', 0),
            'pgbench_test_count': pgbench_summary.get('total_tests', 0),
            'pgbench_avg_time': pgbench_summary.get('average_time', 0),
            'pgbench_successful_tests': pgbench_summary.get('successful_tests', 0),
            'pgbench_failed_tests': pgbench_summary.get('failed_tests', 0)
        }
    
    def generate_comparison_report(self, python_file, pgbench_file, output_file=None):
        """Generate a comprehensive comparison report."""
        python_data, pgbench_data = self.load_results(python_file, pgbench_file)
        
        if not python_data and not pgbench_data:
            logger.error("No valid data found in either file")
            return
        
        # Perform comparisons
        query_comparisons = self.compare_query_performance(python_data, pgbench_data)
        overall_comparison = self.compare_overall_performance(python_data, pgbench_data)
        
        # Generate report
        report = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'python_file': str(python_file),
                'pgbench_file': str(pgbench_file),
                'python_data_available': python_data is not None,
                'pgbench_data_available': pgbench_data is not None
            },
            'overall_comparison': overall_comparison,
            'category_comparisons': query_comparisons,
            'recommendations': self.generate_recommendations(query_comparisons, overall_comparison)
        }
        
        # Save report if output file specified
        if output_file:
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Comparison report saved to {output_file}")
        
        # Log summary
        self.log_comparison_summary(report)
        
        return report
    
    def generate_recommendations(self, query_comparisons, overall_comparison):
        """Generate recommendations based on comparison results."""
        recommendations = []
        
        if not query_comparisons:
            recommendations.append("No comparable test categories found between engines")
            return recommendations
        
        # Analyze performance patterns
        faster_pgbench = 0
        faster_python = 0
        similar_performance = 0
        
        for category, comparison in query_comparisons.items():
            ratio = comparison['comparison']['time_ratio']
            if ratio < 0.8:
                faster_pgbench += 1
            elif ratio > 1.2:
                faster_python += 1
            else:
                similar_performance += 1
        
        total_categories = len(query_comparisons)
        
        # Generate recommendations
        if faster_pgbench > total_categories * 0.6:
            recommendations.append(
                "pgbench shows consistently better performance. Consider using pgbench for "
                "load testing and high-throughput scenarios."
            )
        elif faster_python > total_categories * 0.6:
            recommendations.append(
                "Python implementation shows better performance. The custom test logic may be "
                "more efficient for your specific use cases."
            )
        else:
            recommendations.append(
                "Performance is similar between engines. Choose based on other factors like "
                "test complexity, maintainability, and tooling preferences."
            )
        
        # Check for failed transactions
        failed_tests = overall_comparison.get('pgbench_failed_tests', 0)
        if failed_tests > 0:
            recommendations.append(
                f"pgbench had {failed_tests} failed tests. Investigate database connection "
                "limits, query timeouts, or concurrency issues."
            )
        
        # Throughput recommendations
        pgbench_avg = overall_comparison.get('pgbench_avg_time', 0)
        python_avg = overall_comparison.get('python_avg_time', 0)
        
        if pgbench_avg > 0 and python_avg > 0:
            if pgbench_avg < python_avg * 0.5:
                recommendations.append(
                    "pgbench's high throughput makes it ideal for stress testing and "
                    "identifying database bottlenecks under load."
                )
        
        return recommendations
    
    def log_comparison_summary(self, report):
        """Log a summary of the comparison results."""
        logger.info("=== PERFORMANCE COMPARISON SUMMARY ===")
        
        metadata = report['metadata']
        logger.info(f"Comparing: {metadata['python_file']} vs {metadata['pgbench_file']}")
        
        overall = report['overall_comparison']
        if overall:
            logger.info(f"Python: {overall.get('python_test_count', 0)} tests, "
                       f"{overall.get('python_total_time', 0):.4f}s total")
            logger.info(f"pgbench: {overall.get('pgbench_successful_tests', 0)}/{overall.get('pgbench_test_count', 0)} successful tests, "
                       f"{overall.get('pgbench_total_time', 0):.4f}s total")
        
        categories = report['category_comparisons']
        if categories:
            logger.info(f"\nCategory Comparisons ({len(categories)} categories):")
            for category, comp in categories.items():
                ratio = comp['comparison']['time_ratio']
                pct_diff = comp['comparison']['performance_difference_pct']
                logger.info(f"  {category}: pgbench {ratio:.2f}x Python time ({pct_diff:+.1f}%)")
                
                for insight in comp.get('insights', []):
                    logger.info(f"    • {insight}")
        
        recommendations = report['recommendations']
        if recommendations:
            logger.info(f"\nRecommendations:")
            for i, rec in enumerate(recommendations, 1):
                logger.info(f"  {i}. {rec}")
    
    def create_html_comparison_report(self, report, output_file):
        """Create an HTML version of the comparison report."""
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Performance Test Comparison Report</title>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin: 2rem; }}
        .header {{ border-bottom: 2px solid #eee; padding-bottom: 1rem; margin-bottom: 2rem; }}
        .section {{ margin: 2rem 0; padding: 1rem; border-radius: 8px; }}
        .overview {{ background: #f8f9fa; border-left: 4px solid #0969da; }}
        .comparison {{ background: #fff3cd; border-left: 4px solid #856404; }}
        .recommendations {{ background: #d1edff; border-left: 4px solid #0969da; }}
        table {{ width: 100%; border-collapse: collapse; margin: 1rem 0; }}
        th, td {{ padding: 0.75rem; text-align: left; border-bottom: 1px solid #dee2e6; }}
        th {{ background-color: #f8f9fa; font-weight: 600; }}
        .number {{ font-family: 'SF Mono', Consolas, monospace; }}
        .better {{ color: #28a745; font-weight: 600; }}
        .worse {{ color: #dc3545; font-weight: 600; }}
        .similar {{ color: #6c757d; }}
        .insight {{ background: #e3f2fd; padding: 0.5rem; margin: 0.25rem 0; border-radius: 4px; font-size: 0.9em; }}
        .meta {{ color: #586069; font-size: 0.9em; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Performance Test Comparison Report</h1>
        <div class="meta">Generated: {report['metadata']['generated_at']}</div>
    </div>
    
    <div class="section overview">
        <h2>📈 Overall Performance</h2>
        {self._format_overall_html(report['overall_comparison'])}
    </div>
    
    <div class="section comparison">
        <h2>🔍 Category Comparisons</h2>
        {self._format_category_comparisons_html(report['category_comparisons'])}
    </div>
    
    <div class="section recommendations">
        <h2>💡 Recommendations</h2>
        {self._format_recommendations_html(report['recommendations'])}
    </div>
</body>
</html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        logger.info(f"HTML comparison report saved to {output_file}")
    
    def _format_overall_html(self, overall):
        """Format overall comparison for HTML."""
        if not overall:
            return "<p>No overall comparison data available.</p>"
        
        return f"""
        <table>
            <tr>
                <th>Metric</th>
                <th>Python</th>
                <th>pgbench</th>
                <th>Comparison</th>
            </tr>
            <tr>
                <td>Total Tests</td>
                <td class="number">{overall.get('python_test_count', 0)}</td>
                <td class="number">{overall.get('pgbench_successful_tests', 0)}/{overall.get('pgbench_test_count', 0)}</td>
                <td></td>
            </tr>
            <tr>
                <td>Total Time</td>
                <td class="number">{overall.get('python_total_time', 0):.4f}s</td>
                <td class="number">{overall.get('pgbench_total_time', 0):.4f}s</td>
                <td class="number">{self._compare_values(overall.get('pgbench_total_time', 0), overall.get('python_total_time', 0))}</td>
            </tr>
            <tr>
                <td>Average Test Time</td>
                <td class="number">{overall.get('python_avg_time', 0):.4f}s</td>
                <td class="number">{overall.get('pgbench_avg_time', 0):.4f}s</td>
                <td class="number">{self._compare_values(overall.get('pgbench_avg_time', 0), overall.get('python_avg_time', 0))}</td>
            </tr>
        </table>
        """
    
    def _format_category_comparisons_html(self, comparisons):
        """Format category comparisons for HTML."""
        if not comparisons:
            return "<p>No category comparisons available.</p>"
        
        html = "<table><tr><th>Category</th><th>Python Time</th><th>pgbench Time</th><th>Ratio</th><th>Insights</th></tr>"
        
        for category, comp in comparisons.items():
            python_time = comp['python_stats']['average_time']
            pgbench_time = comp['pgbench_stats']['execution_time']
            ratio = comp['comparison']['time_ratio']
            insights = comp.get('insights', [])
            
            ratio_class = 'better' if ratio < 0.8 else 'worse' if ratio > 1.2 else 'similar'
            
            insights_html = "".join(f'<div class="insight">{insight}</div>' for insight in insights)
            
            html += f"""
            <tr>
                <td>{category.replace('_', ' ').title()}</td>
                <td class="number">{python_time:.4f}s</td>
                <td class="number">{pgbench_time:.4f}s</td>
                <td class="number {ratio_class}">{ratio:.2f}x</td>
                <td>{insights_html}</td>
            </tr>
            """
        
        html += "</table>"
        return html
    
    def _format_recommendations_html(self, recommendations):
        """Format recommendations for HTML."""
        if not recommendations:
            return "<p>No specific recommendations available.</p>"
        
        html = "<ol>"
        for rec in recommendations:
            html += f"<li>{rec}</li>"
        html += "</ol>"
        return html
    
    def _compare_values(self, val1, val2):
        """Compare two values and return a formatted string."""
        if val2 == 0:
            return "N/A"
        
        ratio = val1 / val2
        pct_diff = (val1 - val2) / val2 * 100
        
        if ratio < 0.8:
            return f'<span class="better">{ratio:.2f}x ({pct_diff:+.1f}%)</span>'
        elif ratio > 1.2:
            return f'<span class="worse">{ratio:.2f}x ({pct_diff:+.1f}%)</span>'
        else:
            return f'<span class="similar">{ratio:.2f}x ({pct_diff:+.1f}%)</span>'


def main():
    """Main entry point for performance comparison."""
    parser = argparse.ArgumentParser(description="Compare Python and pgbench performance test results")
    parser.add_argument('--python-results', required=True, help='Path to Python test results JSON file')
    parser.add_argument('--pgbench-results', required=True, help='Path to pgbench test results JSON file')
    parser.add_argument('--output-json', help='Output JSON file for comparison results')
    parser.add_argument('--output-html', help='Output HTML file for comparison report')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], 
                       default='INFO', help='Logging level')
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Create comparer and generate report
    comparer = PerformanceComparer()
    
    try:
        report = comparer.generate_comparison_report(
            args.python_results,
            args.pgbench_results,
            args.output_json
        )
        
        if args.output_html and report:
            comparer.create_html_comparison_report(report, args.output_html)
        
        logger.info("Performance comparison completed successfully")
        
    except Exception as e:
        logger.error(f"Error comparing performance results: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())