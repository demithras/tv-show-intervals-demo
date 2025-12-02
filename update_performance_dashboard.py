"""
Update performance dashboard with historical trend tracking.
Maintains performance history and generates trend analysis.
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


def load_history(history_file):
    """Load existing performance history."""
    if not history_file.exists():
        return []
    
    try:
        with open(history_file, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Warning: Corrupted history file, starting fresh")
        return []


def extract_key_metrics(results):
    """Extract key metrics from test results for trend tracking."""
    meta = results.get('meta', {})
    summary = results.get('summary', {})
    detailed = results.get('detailed_results', {})
    
    metrics = {
        'timestamp': meta.get('timestamp', datetime.now().timestamp()),
        'iso_timestamp': meta.get('iso_timestamp', datetime.now().isoformat()),
        'run_number': meta.get('github_run_number'),
        'commit_sha': meta.get('github_sha'),
        'test_type': meta.get('test_type'),
        'total_execution_time': meta.get('total_execution_time', 0),
        'total_tests': summary.get('total_tests', 0),
        'average_query_time': summary.get('average_time', 0),
        'test_parameters': meta.get('test_parameters', {}),
    }
    
    # Data generation metrics
    if 'data_generation' in detailed and not detailed['data_generation'].get('skipped'):
        dg = detailed['data_generation']
        metrics['data_generation'] = {
            'records': dg.get('total_records', 0),
            'time': dg.get('total_time', 0),
            'records_per_second': dg.get('records_per_second', 0)
        }
    
    # Query performance metrics
    query_metrics = {}
    for category in ['basic_queries', 'filtered_queries', 'aggregation_queries', 'join_performance']:
        if category in detailed:
            category_times = []
            for result in detailed[category].values():
                if isinstance(result, dict) and 'execution_time' in result:
                    category_times.append(result['execution_time'])
            
            if category_times:
                query_metrics[category] = {
                    'count': len(category_times),
                    'avg_time': sum(category_times) / len(category_times),
                    'min_time': min(category_times),
                    'max_time': max(category_times)
                }
    
    if query_metrics:
        metrics['query_performance'] = query_metrics
    
    # Update performance metrics
    if 'update_performance' in detailed:
        update_perf = detailed['update_performance']
        metrics['update_performance'] = {
            'single_update_avg': update_perf.get('single_update_avg', 0),
            'single_update_median': update_perf.get('single_update_median', 0),
        }
        
        if 'batch_updates' in update_perf:
            batch_summary = {}
            for update_type, result in update_perf['batch_updates'].items():
                batch_summary[update_type] = {
                    'time': result['time'],
                    'rows_per_second': result['rows_per_second']
                }
            metrics['update_performance']['batch_updates'] = batch_summary
    
    return metrics


def generate_trend_analysis(history):
    """Generate trend analysis from historical data."""
    if len(history) < 2:
        return {"message": "Insufficient data for trend analysis (need at least 2 runs)"}
    
    # Sort by timestamp
    history.sort(key=lambda x: x.get('timestamp', 0))
    
    analysis = {
        'total_runs': len(history),
        'date_range': {
            'first': history[0].get('iso_timestamp'),
            'last': history[-1].get('iso_timestamp')
        },
        'trends': {}
    }
    
    # Analyze key metrics trends
    metrics_to_analyze = [
        ('total_execution_time', 'Total Execution Time'),
        ('average_query_time', 'Average Query Time'),
    ]
    
    for metric_key, metric_name in metrics_to_analyze:
        values = [run.get(metric_key) for run in history if run.get(metric_key) is not None]
        if len(values) >= 2:
            first_val = values[0]
            last_val = values[-1]
            change_percent = ((last_val - first_val) / first_val) * 100 if first_val > 0 else 0
            
            # Calculate trend direction
            if abs(change_percent) < 5:
                trend = "stable"
                emoji = "➡️"
            elif change_percent > 0:
                trend = "increasing"
                emoji = "📈" if change_percent > 20 else "↗️"
            else:
                trend = "decreasing"
                emoji = "📉" if change_percent < -20 else "↘️"
            
            analysis['trends'][metric_key] = {
                'name': metric_name,
                'first_value': first_val,
                'last_value': last_val,
                'change_percent': change_percent,
                'trend': trend,
                'emoji': emoji,
                'values': values
            }
    
    # Analyze data generation performance if available
    data_gen_rates = []
    for run in history:
        if 'data_generation' in run and 'records_per_second' in run['data_generation']:
            data_gen_rates.append(run['data_generation']['records_per_second'])
    
    if len(data_gen_rates) >= 2:
        first_rate = data_gen_rates[0]
        last_rate = data_gen_rates[-1]
        rate_change = ((last_rate - first_rate) / first_rate) * 100 if first_rate > 0 else 0
        
        analysis['trends']['data_generation_rate'] = {
            'name': 'Data Generation Rate',
            'first_value': first_rate,
            'last_value': last_rate,
            'change_percent': rate_change,
            'trend': 'improving' if rate_change > 5 else 'stable' if abs(rate_change) <= 5 else 'degrading',
            'emoji': "🚀" if rate_change > 20 else "↗️" if rate_change > 5 else "➡️" if abs(rate_change) <= 5 else "↘️",
            'values': data_gen_rates
        }
    
    return analysis


def generate_dashboard_html(history, trend_analysis):
    """Generate HTML dashboard with historical trends."""
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Performance Dashboard - TV Show Intervals Demo</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; 
                line-height: 1.6; 
                color: #333; 
                background: #f8f9fa;
            }}
            .container {{ max-width: 1400px; margin: 0 auto; padding: 2rem; }}
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
            
            .stats-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); 
                gap: 1.5rem; 
                margin-bottom: 2rem; 
            }}
            .stat-card {{ 
                background: white; 
                padding: 1.5rem; 
                border-radius: 8px; 
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                border-left: 4px solid #667eea;
            }}
            .stat-card h3 {{ color: #667eea; margin-bottom: 1rem; }}
            .stat-value {{ font-size: 2rem; font-weight: bold; color: #333; }}
            .stat-label {{ color: #666; font-size: 0.9rem; }}
            .trend {{ margin-top: 0.5rem; font-size: 0.9rem; }}
            
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
            
            .chart-container {{ 
                position: relative; 
                height: 400px; 
                margin-bottom: 2rem; 
            }}
            
            .run-list {{ max-height: 400px; overflow-y: auto; }}
            .run-item {{ 
                padding: 1rem; 
                border-bottom: 1px solid #eee; 
                display: flex; 
                justify-content: space-between; 
                align-items: center; 
            }}
            .run-item:hover {{ background: #f8f9fa; }}
            .run-meta {{ color: #666; font-size: 0.9rem; }}
            
            .trend-positive {{ color: #28a745; }}
            .trend-negative {{ color: #dc3545; }}
            .trend-stable {{ color: #6c757d; }}
            
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
                <h1>📊 Performance Dashboard</h1>
                <div class="meta">
                    TV Show Intervals Demo • Historical Performance Tracking
                </div>
            </header>
            
            <div class="stats-grid">
                <div class="stat-card">
                    <h3>📈 Total Test Runs</h3>
                    <div class="stat-value">{trend_analysis.get('total_runs', 0)}</div>
                    <div class="stat-label">Performance test executions</div>
                </div>
    """
    
    # Add trend cards
    for metric_key, trend_data in trend_analysis.get('trends', {}).items():
        trend_class = "trend-positive" if "improving" in trend_data.get('trend', '') or "decreasing" in trend_data.get('trend', '') else \
                     "trend-negative" if "degrading" in trend_data.get('trend', '') or "increasing" in trend_data.get('trend', '') else "trend-stable"
        
        # Format values based on metric type
        last_val = trend_data['last_value']
        if 'time' in metric_key:
            if last_val < 1:
                formatted_val = f"{last_val*1000:.1f}ms"
            else:
                formatted_val = f"{last_val:.3f}s"
        elif 'rate' in metric_key:
            formatted_val = f"{last_val:,.0f}/sec"
        else:
            formatted_val = f"{last_val:.3f}"
        
        html_content += f"""
                <div class="stat-card">
                    <h3>{trend_data['emoji']} {trend_data['name']}</h3>
                    <div class="stat-value">{formatted_val}</div>
                    <div class="trend {trend_class}">
                        {trend_data['change_percent']:+.1f}% from first run
                    </div>
                </div>
        """
    
    html_content += """
            </div>
            
            <div class="section">
                <div class="section-header">📈 Performance Trends</div>
                <div class="section-content">
                    <div class="chart-container">
                        <canvas id="trendsChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="section">
                <div class="section-header">📋 Recent Test Runs</div>
                <div class="section-content">
                    <div class="run-list">
    """
    
    # Add recent runs (last 10)
    recent_runs = sorted(history, key=lambda x: x.get('timestamp', 0), reverse=True)[:10]
    for run in recent_runs:
        run_number = run.get('run_number', 'Unknown')
        test_type = run.get('test_type', 'unknown')
        exec_time = run.get('total_execution_time', 0)
        timestamp = run.get('iso_timestamp', 'Unknown')
        
        html_content += f"""
                        <div class="run-item">
                            <div>
                                <strong>Run #{run_number}</strong> • {test_type.title()} Test
                                <div class="run-meta">{timestamp}</div>
                            </div>
                            <div>
                                <strong>{exec_time:.2f}s</strong>
                            </div>
                        </div>
        """
    
    html_content += """
                    </div>
                </div>
            </div>
            
            <footer class="footer">
                <p>Dashboard automatically updated by GitHub Actions</p>
                <p>Last updated: """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
            </footer>
        </div>
        
        <script>
            // Prepare chart data
            const history = """ + json.dumps(history) + """;
            const labels = history.map(run => run.run_number ? `#${run.run_number}` : new Date(run.timestamp * 1000).toLocaleDateString());
            
            // Chart.js configuration
            const ctx = document.getElementById('trendsChart').getContext('2d');
            new Chart(ctx, {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [
                        {
                            label: 'Total Execution Time (s)',
                            data: history.map(run => run.total_execution_time || 0),
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y'
                        },
                        {
                            label: 'Average Query Time (ms)',
                            data: history.map(run => (run.average_query_time || 0) * 1000),
                            borderColor: '#f093fb',
                            backgroundColor: 'rgba(240, 147, 251, 0.1)',
                            tension: 0.4,
                            yAxisID: 'y1'
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    interaction: {
                        mode: 'index',
                        intersect: false,
                    },
                    scales: {
                        x: {
                            display: true,
                            title: {
                                display: true,
                                text: 'Test Run'
                            }
                        },
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                            title: {
                                display: true,
                                text: 'Total Execution Time (s)'
                            }
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            title: {
                                display: true,
                                text: 'Average Query Time (ms)'
                            },
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    },
                    plugins: {
                        legend: {
                            display: true,
                            position: 'top'
                        },
                        title: {
                            display: true,
                            text: 'Performance Trends Over Time'
                        }
                    }
                }
            });
        </script>
    </body>
    </html>
    """
    
    return html_content


def main():
    parser = argparse.ArgumentParser(description='Update performance dashboard with trend tracking')
    parser.add_argument('--results-file', required=True, help='JSON results file path')
    parser.add_argument('--output-dir', default='dashboard', help='Output directory for dashboard')
    parser.add_argument('--history-file', help='Performance history file path (default: {output_dir}/history.json)')
    parser.add_argument('--run-number', help='GitHub run number')
    parser.add_argument('--commit-sha', help='Git commit SHA')
    parser.add_argument('--branch', help='Git branch name')
    parser.add_argument('--max-history', type=int, default=50, help='Maximum number of runs to keep in history')
    
    args = parser.parse_args()
    
    # Setup paths
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    history_file = Path(args.history_file) if args.history_file else output_dir / 'history.json'
    
    # Load current results and history
    results = load_results(args.results_file)
    history = load_history(history_file)
    
    # Update metadata with CLI arguments
    if args.run_number:
        results.setdefault('meta', {})['github_run_number'] = args.run_number
    if args.commit_sha:
        results.setdefault('meta', {})['github_sha'] = args.commit_sha
    if args.branch:
        results.setdefault('meta', {})['github_ref'] = args.branch
    
    # Extract metrics and add to history
    metrics = extract_key_metrics(results)
    history.append(metrics)
    
    # Keep only the most recent runs
    if len(history) > args.max_history:
        history = history[-args.max_history:]
    
    # Save updated history
    with open(history_file, 'w') as f:
        json.dump(history, f, indent=2)
    
    # Generate trend analysis
    trend_analysis = generate_trend_analysis(history)
    
    # Generate dashboard HTML
    dashboard_html = generate_dashboard_html(history, trend_analysis)
    
    # Save dashboard
    dashboard_file = output_dir / 'index.html'
    with open(dashboard_file, 'w') as f:
        f.write(dashboard_html)
    
    # Save trend analysis as JSON for other tools
    trends_file = output_dir / 'trends.json'
    with open(trends_file, 'w') as f:
        json.dump(trend_analysis, f, indent=2)
    
    print(f"Dashboard updated: {dashboard_file}")
    print(f"History updated: {history_file}")
    print(f"Trends analysis: {trends_file}")
    print(f"Total runs in history: {len(history)}")
    
    # Print trend summary
    if trend_analysis.get('trends'):
        print("\nTrend Summary:")
        for metric_key, trend_data in trend_analysis['trends'].items():
            print(f"  {trend_data['emoji']} {trend_data['name']}: {trend_data['change_percent']:+.1f}% ({trend_data['trend']})")


if __name__ == '__main__':
    main()