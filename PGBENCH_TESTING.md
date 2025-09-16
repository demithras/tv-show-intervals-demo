# pgbench Performance Testing for TV Show Intervals Demo

This directory contains a complete pgbench-based performance testing solution that complements the existing Python performance tests. The pgbench approach provides industry-standard database benchmarking capabilities and can be used to validate and compare performance characteristics.

## Overview

The pgbench test suite replicates the same test categories as the Python implementation:

- **Basic Queries**: Simple SELECT operations (counts, aggregations, top-N queries)
- **Filtered Queries**: WHERE clause performance with various indexes
- **Aggregation Queries**: Complex GROUP BY operations with JOINs
- **JOIN Performance**: Multi-table operations between programs and intervals
- **Update Performance**: UPDATE operations and trigger overhead testing
- **Index Effectiveness**: Queries designed to utilize specific indexes
- **Overnight Programs**: Testing the midnight-crossing calculation logic

## Quick Start

### Prerequisites

1. **PostgreSQL with pgbench**: Install postgresql-contrib package
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql-client postgresql-contrib
   
   # macOS with Homebrew
   brew install postgresql
   ```

2. **Python dependencies**: Ensure you have the project requirements installed
   ```bash
   pip install -r requirements.txt
   ```

3. **Database**: A PostgreSQL database with the schema applied

### Validation Test

Run the validation script to ensure everything is set up correctly:

```bash
python test_pgbench_setup.py
```

### Basic Usage

1. **Quick test** (small dataset, essential tests only):
   ```bash
   python run_pgbench_performance_tests.py \
     --database-url "postgresql://user:pass@host:port/dbname" \
     --test-type quick \
     --records 50000
   ```

2. **Full test suite** (large dataset, all test categories):
   ```bash
   python run_pgbench_performance_tests.py \
     --database-url "postgresql://user:pass@host:port/dbname" \
     --test-type full \
     --records 1000000 \
     --clients 4
   ```

3. **Compare with existing data** (skip data generation):
   ```bash
   python run_pgbench_performance_tests.py \
     --database-url "postgresql://user:pass@host:port/dbname" \
     --test-type quick \
     --skip-data-generation
   ```

## Command Line Options

- `--database-url`: PostgreSQL connection URL (required)
- `--records`: Number of test records to generate (default: 500,000)
- `--batch-size`: Batch size for data insertion (default: 10,000)
- `--clients`: Number of concurrent pgbench clients (default: 1)
- `--test-type`: Type of test suite (`quick` or `full`, default: `quick`)
- `--output-file`: JSON file to save results
- `--skip-data-generation`: Use existing data instead of generating new records
- `--log-level`: Logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`)

## Test Files

The `pgbench-tests/` directory contains SQL scripts for each test category:

- `01-basic-queries.sql`: Basic SELECT operations
- `02-filtered-queries.sql`: WHERE clause and index usage tests
- `03-aggregation-queries.sql`: Complex GROUP BY and aggregate functions
- `04-join-queries.sql`: JOIN performance between tables
- `05-update-queries.sql`: UPDATE operations and trigger testing
- `06-index-queries.sql`: Index effectiveness validation
- `07-overnight-queries.sql`: Overnight program calculation testing

## Performance Comparison

Compare Python and pgbench results using the comparison utility:

```bash
# Run both test engines
python run_performance_tests.py --test-type quick --output-file python-results.json
python run_pgbench_performance_tests.py --database-url "$DATABASE_URL" --test-type quick --output-file pgbench-results.json

# Compare results
python compare_performance_results.py \
  --python-results python-results.json \
  --pgbench-results pgbench-results.json \
  --output-html comparison-report.html
```

## GitHub Actions Integration

The GitHub Actions workflow (`performance-tests.yml`) supports pgbench testing:

### Manual Workflow Dispatch

1. Go to Actions → Performance Tests
2. Click "Run workflow"
3. Select test parameters:
   - **Test Engine**: Choose `python`, `pgbench`, or `both`
   - **pgbench Clients**: Number of concurrent clients for pgbench tests
   - **Test Type**: `quick` for fast validation, `full` for comprehensive testing

### Automatic Triggers

- **Push to main**: Quick Python tests (for fast feedback)
- **Weekly schedule**: Full test suite with both engines
- **Manual dispatch**: Configurable parameters for specific testing needs

## Understanding pgbench Output

pgbench provides several key metrics:

- **TPS (Transactions Per Second)**: How many transactions pgbench can execute per second
- **Latency**: Average time to complete each transaction
- **Failed Transactions**: Number of transactions that failed (should be 0 for most tests)

### Example Output Interpretation

```
basic_queries_pgbench: 2.4567s, 40.61 TPS, 24.62ms avg latency, 100 transactions
```

This means:
- Test took 2.46 seconds total
- Achieved 40.61 transactions per second
- Average latency was 24.62 milliseconds per transaction
- Successfully completed 100 transactions

## Advanced Usage

### Concurrent Testing

Test database behavior under concurrent load:

```bash
python run_pgbench_performance_tests.py \
  --database-url "$DATABASE_URL" \
  --clients 8 \
  --test-type full
```

### Custom Transaction Counts

For longer-running tests with more statistical significance:

```bash
# Modify the script or SQL files to adjust transaction counts
# Default: 20-100 transactions per test depending on complexity
```

### Integration with CI/CD

The pgbench tests integrate seamlessly with existing CI/CD pipelines:

1. **Pull Request Testing**: Quick validation that changes don't regress performance
2. **Release Testing**: Full test suite before production deployments
3. **Continuous Monitoring**: Scheduled tests to detect performance degradation

## Troubleshooting

### Common Issues

1. **pgbench not found**:
   ```bash
   sudo apt-get install postgresql-contrib
   ```

2. **Connection refused**:
   - Verify database URL is correct
   - Ensure PostgreSQL is running
   - Check firewall/network connectivity

3. **Permission denied**:
   - Verify database user has appropriate permissions
   - Ensure database exists and schema is applied

4. **Failed transactions**:
   - Check for connection pool limits
   - Reduce concurrent clients
   - Increase database connection limits

### Debugging

Enable debug logging for detailed information:

```bash
python run_pgbench_performance_tests.py \
  --database-url "$DATABASE_URL" \
  --log-level DEBUG
```

## Performance Optimization Tips

1. **Baseline Testing**: Run tests on a clean database first
2. **Consistent Environment**: Use the same database configuration for comparisons
3. **Multiple Runs**: pgbench results can vary; run multiple times for averages
4. **Resource Monitoring**: Monitor CPU, memory, and I/O during tests
5. **Index Analysis**: Use `EXPLAIN ANALYZE` to verify index usage in custom tests

## Integration with Existing Tools

The pgbench results are compatible with existing performance monitoring tools:

- **Allure Reports**: Results integrate with existing Allure test reporting
- **GitHub Actions**: Artifacts and summaries work with existing workflow
- **Performance Dashboard**: JSON output can be ingested by monitoring systems

## Contributing

To add new pgbench test scenarios:

1. Create a new `.sql` file in `pgbench-tests/`
2. Use pgbench variables for randomization: `\set random_value random(1, 100)`
3. Add conditional execution: `WHERE :query_type = 1`
4. Update `run_pgbench_performance_tests.py` to include the new test
5. Test thoroughly with `test_pgbench_setup.py`

This pgbench implementation provides a comprehensive, industry-standard approach to database performance testing while maintaining compatibility with the existing Python-based test infrastructure.