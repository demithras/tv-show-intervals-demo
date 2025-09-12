"""
Create performance summary for GitHub integration.
Generates concise summaries for PR comments and GitHub Actions output.
"""

import argparse
import json
import sys
from pathlib import Path


def load_results(results_file):
    """Load performance test results from JSON file."""
    try:
        with open(results_file, 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: Results file not found: {results_file}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in results file: {e}")
        sys.exit(1)


def format_duration(seconds):
    """Format duration in a human-readable way."""
    if seconds < 0.001:
        return f"{seconds*1000000:.0f}μs"
    elif seconds < 1:
        return f"{seconds*1000:.1f}ms"
    else:
        return f"{seconds:.3f}s"


def format_number(num):
    """Format numbers with thousands separators."""
    if isinstance(num, (int, float)):
        return f"{num:,.0f}" if num == int(num) else f"{num:,.2f}"
    return str(num)


def get_performance_rating(execution_time):
    """Get performance rating emoji and text."""
    if execution_time < 0.1:
        return "🟢", "Excellent"
    elif execution_time < 0.5:
        return "🟡", "Good" 
    elif execution_time < 2.0:
        return "🟠", "Fair"
    else:
        return "🔴", "Needs Optimization"


def create_github_summary(results):
    """Create GitHub-style summary for PR comments."""
    meta = results.get('meta', {})
    summary = results.get('summary', {})
    detailed = results.get('detailed_results', {})
    
    # Header with basic info
    github_summary = [
        "## 📊 Performance Test Results",
        "",
        f"**🔧 Test Configuration**",
        f"- **Type**: {meta.get('test_type', 'unknown')}",
        f"- **Total Execution**: {format_duration(meta.get('total_execution_time', 0))}",
        f"- **Tests Run**: {format_number(summary.get('total_tests', 0))}",
        f"- **Average Query Time**: {format_duration(summary.get('average_time', 0))}",
    ]
    
    # Add test parameters if available
    if 'test_parameters' in meta:
        params = meta['test_parameters']
        github_summary.extend([
            f"- **Records**: {format_number(params.get('records', 0))}",
            f"- **Batch Size**: {format_number(params.get('batch_size', 0))}",
        ])
    
    github_summary.append("")
    
    # Data generation performance
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        dg = detailed['data_generation']
        insert_rate = dg.get('records_per_second', 0)
        rate_emoji, rate_rating = get_performance_rating(1/max(insert_rate/10000, 0.001))  # Scale for insert rate
        
        github_summary.extend([
            f"### 🚀 Data Generation Performance",
            f"- **Records Generated**: {format_number(dg.get('total_records', 0))}",
            f"- **Generation Time**: {format_duration(dg.get('total_time', 0))}",
            f"- **Insert Rate**: {format_number(insert_rate)} records/sec {rate_emoji} {rate_rating}",
            "",
        ])
    
    # Query performance highlights
    if 'basic_queries' in detailed:
        github_summary.extend([
            "### 🔍 Query Performance Highlights",
            "",
            "| Test | Time | Rows | Rating |",
            "|------|------|------|--------|",
        ])
        
        # Show top 5 most important queries
        important_queries = []
        for test_name, result in detailed['basic_queries'].items():
            if isinstance(result, dict) and 'execution_time' in result:
                important_queries.append((test_name, result))
        
        # Sort by execution time (show slowest first as they're most important to optimize)
        important_queries.sort(key=lambda x: x[1]['execution_time'], reverse=True)
        
        for test_name, result in important_queries[:5]:
            exec_time = result['execution_time']
            row_count = result.get('row_count', 0)
            emoji, rating = get_performance_rating(exec_time)
            
            github_summary.append(
                f"| {test_name[:40]}{'...' if len(test_name) > 40 else ''} | "
                f"{format_duration(exec_time)} | "
                f"{format_number(row_count)} | "
                f"{emoji} {rating} |"
            )
        
        github_summary.append("")
    
    # Aggregation performance
    if 'aggregation_queries' in detailed:
        agg_times = []
        for result in detailed['aggregation_queries'].values():
            if isinstance(result, dict) and 'execution_time' in result:
                agg_times.append(result['execution_time'])
        
        if agg_times:
            avg_agg_time = sum(agg_times) / len(agg_times)
            max_agg_time = max(agg_times)
            emoji, rating = get_performance_rating(avg_agg_time)
            
            github_summary.extend([
                "### 📈 Aggregation Performance",
                f"- **Tests Run**: {len(agg_times)}",
                f"- **Average Time**: {format_duration(avg_agg_time)} {emoji} {rating}",
                f"- **Slowest Query**: {format_duration(max_agg_time)}",
                "",
            ])
    
    # Update performance (if tested)
    if 'update_performance' in detailed:
        update_perf = detailed['update_performance']
        single_avg = update_perf.get('single_update_avg', 0)
        emoji, rating = get_performance_rating(single_avg)
        
        github_summary.extend([
            "### ⚡ Update/Trigger Performance",
            f"- **Single Update (Avg)**: {format_duration(single_avg)} {emoji} {rating}",
            f"- **Single Update (Median)**: {format_duration(update_perf.get('single_update_median', 0))}",
        ])
        
        if 'batch_updates' in update_perf:
            batch_updates = update_perf['batch_updates']
            for update_type, batch_result in batch_updates.items():
                github_summary.append(
                    f"- **{update_type.replace('_', ' ').title()}**: "
                    f"{format_duration(batch_result['time'])} "
                    f"({format_number(batch_result['rows_updated'])} rows)"
                )
        
        github_summary.append("")
    
    # Performance recommendations
    github_summary.extend([
        "### 💡 Performance Insights",
    ])
    
    # Analyze results and provide insights
    insights = []
    
    # Check data generation rate
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        insert_rate = detailed['data_generation'].get('records_per_second', 0)
        if insert_rate > 20000:
            insights.append("✅ **Excellent insert performance** - Database handles bulk operations efficiently")
        elif insert_rate > 10000:
            insights.append("✅ **Good insert performance** - Bulk operations are well-optimized")
        else:
            insights.append("⚠️ **Insert performance could be improved** - Consider optimizing batch sizes or indexes")
    
    # Check query performance
    if 'basic_queries' in detailed:
        slow_queries = []
        for test_name, result in detailed['basic_queries'].items():
            if isinstance(result, dict) and 'execution_time' in result:
                if result['execution_time'] > 1.0:
                    slow_queries.append(test_name)
        
        if not slow_queries:
            insights.append("✅ **All basic queries perform well** - Good indexing strategy")
        else:
            insights.append(f"⚠️ **{len(slow_queries)} queries need optimization** - Consider additional indexes")
    
    # Check aggregation performance
    if 'aggregation_queries' in detailed:
        agg_times = [
            result['execution_time'] for result in detailed['aggregation_queries'].values()
            if isinstance(result, dict) and 'execution_time' in result
        ]
        if agg_times and max(agg_times) < 2.0:
            insights.append("✅ **Aggregation queries are efficient** - Good for analytics workloads")
        elif agg_times:
            insights.append("⚠️ **Some aggregation queries are slow** - May need query optimization")
    
    if not insights:
        insights.append("ℹ️ **Performance analysis complete** - Review detailed results for optimization opportunities")
    
    github_summary.extend(insights)
    github_summary.extend([
        "",
        f"---",
        f"*📅 Generated on {meta.get('iso_timestamp', 'unknown')} • "
        f"🏃‍♂️ Run #{meta.get('github_run_number', 'unknown')} • "
        f"🔧 {meta.get('test_type', 'unknown').title()} Test*"
    ])
    
    return "\n".join(github_summary)


def create_console_summary(results):
    """Create concise console summary."""
    meta = results.get('meta', {})
    summary = results.get('summary', {})
    detailed = results.get('detailed_results', {})
    
    lines = [
        "=" * 60,
        "PERFORMANCE TEST SUMMARY",
        "=" * 60,
        f"Test Type: {meta.get('test_type', 'unknown')}",
        f"Total Execution Time: {format_duration(meta.get('total_execution_time', 0))}",
        f"Tests Run: {format_number(summary.get('total_tests', 0))}",
        f"Average Query Time: {format_duration(summary.get('average_time', 0))}",
    ]
    
    if 'test_parameters' in meta:
        params = meta['test_parameters']
        lines.extend([
            f"Records: {format_number(params.get('records', 0))}",
            f"Batch Size: {format_number(params.get('batch_size', 0))}",
        ])
    
    lines.append("")
    
    # Key metrics
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        dg = detailed['data_generation']
        lines.extend([
            "DATA GENERATION:",
            f"  Insert Rate: {format_number(dg.get('records_per_second', 0))} records/sec",
            f"  Time: {format_duration(dg.get('total_time', 0))}",
            "",
        ])
    
    if 'basic_queries' in detailed:
        basic_times = [
            result['execution_time'] for result in detailed['basic_queries'].values()
            if isinstance(result, dict) and 'execution_time' in result
        ]
        if basic_times:
            lines.extend([
                "QUERY PERFORMANCE:",
                f"  Fastest Query: {format_duration(min(basic_times))}",
                f"  Slowest Query: {format_duration(max(basic_times))}",
                f"  Total Queries: {len(basic_times)}",
                "",
            ])
    
    lines.append("=" * 60)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description='Create performance summary for GitHub integration')
    parser.add_argument('--results-file', required=True, help='JSON results file path')
    parser.add_argument('--output-file', help='Output file path (default: stdout)')
    parser.add_argument('--format', choices=['github', 'console'], default='github', help='Summary format')
    
    args = parser.parse_args()
    
    # Load results
    results = load_results(args.results_file)
    
    # Generate summary
    if args.format == 'github':
        summary_content = create_github_summary(results)
    else:
        summary_content = create_console_summary(results)
    
    # Output summary
    if args.output_file:
        output_path = Path(args.output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write(summary_content)
        print(f"Summary written to {output_path}")
    else:
        print(summary_content)


if __name__ == '__main__':
    main()