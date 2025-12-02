"""
Generate comprehensive performance reports from test results.
Creates HTML reports with visualizations and detailed analysis.
"""

import argparse
import json
import os
import sys
from datetime import datetime
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


def generate_html_report(results, output_dir):
    """Generate comprehensive HTML performance report."""
    report_path = Path(output_dir) / "performance_report.html"
    
    meta = results.get('meta', {})
    summary = results.get('summary', {})
    detailed = results.get('detailed_results', {})
    
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Performance Test Report - TV Show Intervals Demo</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                background: #f8f9fa;
            }}
            .container {{ max-width: 1200px; margin: 0 auto; padding: 2rem; }}
            .header {{ 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white; 
                padding: 2rem; 
                border-radius: 12px; 
                margin-bottom: 2rem;
                box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            }}
            .header h1 {{ font-size: 2.5rem; margin-bottom: 0.5rem; }}
            .header .meta {{ opacity: 0.9; font-size: 1.1rem; }}
            
            .summary-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 1.5rem; 
                margin-bottom: 2rem; 
            }}
            .summary-card {{ 
                background: white; 
                padding: 1.5rem; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #667eea;
            }}
            .summary-card h3 {{ color: #667eea; margin-bottom: 1rem; }}
            .summary-card .value {{ font-size: 2rem; font-weight: bold; color: #333; }}
            .summary-card .label {{ color: #666; font-size: 0.9rem; }}
            
            .section {{ 
                background: white; 
                margin-bottom: 2rem; 
                border-radius: 8px; 
                overflow: hidden;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .section-header {{ 
                background: #667eea; 
                color: white; 
                padding: 1rem 1.5rem; 
                font-size: 1.2rem; 
                font-weight: 600; 
            }}
            .section-content {{ padding: 1.5rem; }}
            
            .test-table {{ width: 100%; border-collapse: collapse; }}
            .test-table th, .test-table td {{ 
                padding: 0.75rem; 
                text-align: left; 
                border-bottom: 1px solid #eee; 
            }}
            .test-table th {{ 
                background: #f8f9fa; 
                font-weight: 600; 
                color: #333;
            }}
            .test-table tr:hover {{ background: #f8f9fa; }}
            
            .performance-indicator {{ 
                display: inline-block; 
                padding: 0.25rem 0.5rem; 
                border-radius: 4px; 
                font-size: 0.8rem; 
                font-weight: 600; 
            }}
            .fast {{ background: #d4edda; color: #155724; }}
            .medium {{ background: #fff3cd; color: #856404; }}
            .slow {{ background: #f8d7da; color: #721c24; }}
            
            .number {{ font-family: 'SF Mono', Consolas, monospace; }}
            .progress-bar {{ 
                background: #e9ecef; 
                border-radius: 4px; 
                overflow: hidden; 
                height: 8px; 
                margin-top: 0.5rem; 
            }}
            .progress-fill {{ 
                background: linear-gradient(90deg, #28a745, #20c997); 
                height: 100%; 
                transition: width 0.3s ease; 
            }}
            
            .chart-placeholder {{ 
                background: #f8f9fa; 
                border: 2px dashed #dee2e6; 
                border-radius: 8px; 
                height: 300px; 
                display: flex; 
                align-items: center; 
                justify-content: center; 
                color: #6c757d; 
                font-style: italic; 
            }}
            
            .footer {{ 
                text-align: center; 
                padding: 2rem; 
                color: #6c757d; 
                border-top: 1px solid #eee; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <header class="header">
                <h1>📊 Performance Test Report</h1>
                <div class="meta">
                    TV Show Intervals Demo • 
                    {meta.get('iso_timestamp', 'Unknown time')} • 
                    Test Type: {meta.get('test_type', 'unknown')}
                </div>
            </header>
            
            <div class="summary-grid">
                <div class="summary-card">
                    <h3>⚡ Total Execution</h3>
                    <div class="value">{format_duration(meta.get('total_execution_time', 0))}</div>
                    <div class="label">End-to-end runtime</div>
                </div>
                <div class="summary-card">
                    <h3>🔍 Tests Executed</h3>
                    <div class="value">{format_number(summary.get('total_tests', 0))}</div>
                    <div class="label">Individual test operations</div>
                </div>
                <div class="summary-card">
                    <h3>📈 Query Performance</h3>
                    <div class="value">{format_duration(summary.get('average_time', 0))}</div>
                    <div class="label">Average query time</div>
                </div>
                <div class="summary-card">
                    <h3>🗄️ Database</h3>
                    <div class="value">{meta.get('database_url_host', 'localhost')}</div>
                    <div class="label">Test environment</div>
                </div>
            </div>
    """
    
    # Test configuration section
    if 'test_parameters' in meta:
        params = meta['test_parameters']
        html_content += f"""
        <div class="section">
            <div class="section-header">🔧 Test Configuration</div>
            <div class="section-content">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem;">
                    <div><strong>Records:</strong> {format_number(params.get('records', 0))}</div>
                    <div><strong>Batch Size:</strong> {format_number(params.get('batch_size', 0))}</div>
                    <div><strong>Test Type:</strong> {params.get('test_type', 'unknown')}</div>
                    <div><strong>CI Environment:</strong> {'Yes' if meta.get('ci_environment') else 'No'}</div>
                </div>
            </div>
        </div>
        """
    
    # Data generation results
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        dg = detailed['data_generation']
        html_content += f"""
        <div class="section">
            <div class="section-header">🚀 Data Generation Performance</div>
            <div class="section-content">
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>📊 Records Generated</h3>
                        <div class="value">{format_number(dg.get('total_records', 0))}</div>
                    </div>
                    <div class="summary-card">
                        <h3>⏱️ Generation Time</h3>
                        <div class="value">{format_duration(dg.get('total_time', 0))}</div>
                    </div>
                    <div class="summary-card">
                        <h3>🔥 Insert Rate</h3>
                        <div class="value">{format_number(dg.get('records_per_second', 0))}</div>
                        <div class="label">records/second</div>
                    </div>
                </div>
            </div>
        </div>
        """
    
    # Query performance sections
    query_sections = {
        'basic_queries': '🔍 Basic Query Performance',
        'filtered_queries': '🎯 Filtered Query Performance', 
        'aggregation_queries': '📈 Aggregation Performance',
        'join_performance': '🔗 JOIN Performance',
        'index_effectiveness': '📋 Index Effectiveness'
    }
    
    for section_key, section_title in query_sections.items():
        if section_key in detailed:
            tests = detailed[section_key]
            html_content += f"""
            <div class="section">
                <div class="section-header">{section_title}</div>
                <div class="section-content">
                    <table class="test-table">
                        <thead>
                            <tr>
                                <th>Test Name</th>
                                <th>Execution Time</th>
                                <th>Rows Returned</th>
                                <th>Performance</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for test_name, result in tests.items():
                if isinstance(result, dict) and 'execution_time' in result:
                    exec_time = result['execution_time']
                    row_count = result.get('row_count', 0)
                    
                    # Determine performance indicator
                    if exec_time < 0.1:
                        perf_class = "fast"
                        perf_text = "Fast"
                    elif exec_time < 1.0:
                        perf_class = "medium" 
                        perf_text = "Medium"
                    else:
                        perf_class = "slow"
                        perf_text = "Slow"
                    
                    html_content += f"""
                    <tr>
                        <td>{test_name}</td>
                        <td class="number">{format_duration(exec_time)}</td>
                        <td class="number">{format_number(row_count)}</td>
                        <td><span class="performance-indicator {perf_class}">{perf_text}</span></td>
                    </tr>
                    """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            </div>
            """
    
    # Update performance section
    if 'update_performance' in detailed:
        update_perf = detailed['update_performance']
        html_content += f"""
        <div class="section">
            <div class="section-header">⚡ Update/Trigger Performance</div>
            <div class="section-content">
                <div class="summary-grid">
                    <div class="summary-card">
                        <h3>Single Update (Avg)</h3>
                        <div class="value">{format_duration(update_perf.get('single_update_avg', 0))}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Single Update (Median)</h3>
                        <div class="value">{format_duration(update_perf.get('single_update_median', 0))}</div>
                    </div>
                    <div class="summary-card">
                        <h3>Range</h3>
                        <div class="value">
                            {format_duration(update_perf.get('single_update_min', 0))} - 
                            {format_duration(update_perf.get('single_update_max', 0))}
                        </div>
                    </div>
                </div>
        """
        
        if 'batch_updates' in update_perf:
            html_content += """
                <h4 style="margin-top: 2rem; margin-bottom: 1rem;">Batch Updates</h4>
                <table class="test-table">
                    <thead>
                        <tr>
                            <th>Update Type</th>
                            <th>Execution Time</th>
                            <th>Rows Updated</th>
                            <th>Rate (rows/sec)</th>
                        </tr>
                    </thead>
                    <tbody>
            """
            
            for update_type, batch_result in update_perf['batch_updates'].items():
                html_content += f"""
                <tr>
                    <td>{update_type.replace('_', ' ').title()}</td>
                    <td class="number">{format_duration(batch_result['time'])}</td>
                    <td class="number">{format_number(batch_result['rows_updated'])}</td>
                    <td class="number">{format_number(batch_result['rows_per_second'])}</td>
                </tr>
                """
            
            html_content += """
                    </tbody>
                </table>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    # Footer
    html_content += f"""
            <footer class="footer">
                <p>Generated by TV Show Intervals Performance Test Suite</p>
                <p>Report created on {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            </footer>
        </div>
        
        <script>
            // Add some interactivity
            document.addEventListener('DOMContentLoaded', function() {{
                // Highlight rows on hover
                const tables = document.querySelectorAll('.test-table');
                tables.forEach(table => {{
                    const rows = table.querySelectorAll('tbody tr');
                    rows.forEach(row => {{
                        row.addEventListener('mouseenter', function() {{
                            this.style.backgroundColor = '#e3f2fd';
                        }});
                        row.addEventListener('mouseleave', function() {{
                            this.style.backgroundColor = '';
                        }});
                    }});
                }});
                
                // Add click to copy functionality for numbers
                const numbers = document.querySelectorAll('.number');
                numbers.forEach(num => {{
                    num.style.cursor = 'pointer';
                    num.title = 'Click to copy';
                    num.addEventListener('click', function() {{
                        navigator.clipboard.writeText(this.textContent);
                        const original = this.textContent;
                        this.textContent = '✓ Copied';
                        setTimeout(() => {{
                            this.textContent = original;
                        }}, 1000);
                    }});
                }});
            }});
        </script>
    </body>
    </html>
    """
    
    # Write the HTML file
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, 'w') as f:
        f.write(html_content)
    
    return report_path


def generate_markdown_summary(results, output_dir):
    """Generate a Markdown summary for GitHub integration."""
    summary_path = Path(output_dir) / "summary.md"
    
    meta = results.get('meta', {})
    summary = results.get('summary', {})
    detailed = results.get('detailed_results', {})
    
    markdown_content = f"""# Performance Test Summary

**Test Type:** {meta.get('test_type', 'unknown')}  
**Execution Time:** {format_duration(meta.get('total_execution_time', 0))}  
**Timestamp:** {meta.get('iso_timestamp', 'unknown')}  

## Key Metrics

- **Total Tests:** {format_number(summary.get('total_tests', 0))}
- **Average Query Time:** {format_duration(summary.get('average_time', 0))}
- **Database:** {meta.get('database_url_host', 'localhost')}
"""
    
    # Add data generation summary
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        dg = detailed['data_generation']
        markdown_content += f"""
## Data Generation

- **Records:** {format_number(dg.get('total_records', 0))}
- **Time:** {format_duration(dg.get('total_time', 0))}
- **Rate:** {format_number(dg.get('records_per_second', 0))} records/sec
"""
    
    # Add query performance highlights
    if 'basic_queries' in detailed:
        markdown_content += "\n## Query Performance Highlights\n\n"
        for test_name, result in list(detailed['basic_queries'].items())[:5]:  # Top 5
            if isinstance(result, dict) and 'execution_time' in result:
                markdown_content += f"- **{test_name}:** {format_duration(result['execution_time'])} ({format_number(result.get('row_count', 0))} rows)\n"
    
    with open(summary_path, 'w') as f:
        f.write(markdown_content)
    
    return summary_path


def main():
    parser = argparse.ArgumentParser(description='Generate performance reports from test results')
    parser.add_argument('--results-file', required=True, help='JSON results file path')
    parser.add_argument('--output-dir', default='performance-reports', help='Output directory for reports')
    parser.add_argument('--format', choices=['html', 'markdown', 'both'], default='both', help='Report format')
    
    args = parser.parse_args()
    
    # Load results
    results = load_results(args.results_file)
    
    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    generated_files = []
    
    # Generate reports
    if args.format in ['html', 'both']:
        html_path = generate_html_report(results, output_dir)
        generated_files.append(html_path)
        print(f"Generated HTML report: {html_path}")
    
    if args.format in ['markdown', 'both']:
        md_path = generate_markdown_summary(results, output_dir)
        generated_files.append(md_path)
        print(f"Generated Markdown summary: {md_path}")
    
    print(f"\nReport generation completed. Files created in {output_dir}")
    return generated_files


if __name__ == '__main__':
    main()