# TV Show Intervals - Performance Testing Documentation

## Overview

This document provides comprehensive documentation for the performance testing system implemented in the TV Show Intervals Demo project. The performance testing framework is designed to validate system performance at scale, test database optimization strategies, and provide detailed insights into query performance characteristics.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema](#database-schema)
3. [Data Generator](#data-generator)
4. [Testing Approach](#testing-approach)
5. [Test Categories](#test-categories)
6. [Performance Tests Detailed](#performance-tests-detailed)
7. [Running Performance Tests](#running-performance-tests)
8. [CI/CD Integration](#cicd-integration)
9. [Interpreting Results](#interpreting-results)
10. [Optimization Strategies](#optimization-strategies)

## Architecture Overview

The performance testing system consists of several key components:

```
┌─────────────────────┐    ┌──────────────────────┐    ┌─────────────────────┐
│   Data Generator    │────│  Performance Tests   │────│   Result Analysis   │
│                     │    │                      │    │                     │
│ • Realistic Data    │    │ • 7 Test Categories  │    │ • HTML Reports      │
│ • Batch Processing  │    │ • 28+ Individual     │    │ • JSON Output       │
│ • Schema Enhancement│    │   Tests              │    │ • GitHub Pages      │
└─────────────────────┘    └──────────────────────┘    └─────────────────────┘
           │                          │                           │
           └──────────────────────────┼───────────────────────────┘
                                      │
                            ┌─────────▼──────────┐
                            │   PostgreSQL DB    │
                            │                    │
                            │ • Enhanced Schema  │
                            │ • Performance      │
                            │   Indexes          │
                            │ • Trigger System   │
                            └────────────────────┘
```

## Database Schema

### Core Tables

#### `programs` Table
```sql
CREATE TABLE programs (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    -- Performance testing columns
    channel_id INTEGER DEFAULT NULL,
    category VARCHAR(50) DEFAULT NULL,
    priority INTEGER DEFAULT 1,
    day_of_week INTEGER DEFAULT NULL,
    UNIQUE(program_name, start_time, end_time)
);
```

#### `program_intervals` Table
```sql
CREATE TABLE program_intervals (
    id SERIAL PRIMARY KEY,
    program_name VARCHAR(255) NOT NULL,
    interval_count INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Performance Indexes

The system creates 7 optimized indexes for different query patterns:

1. **`idx_programs_channel`** - Single-column index on `channel_id`
2. **`idx_programs_category`** - Single-column index on `category`
3. **`idx_programs_day`** - Single-column index on `day_of_week`
4. **`idx_programs_priority`** - Single-column index on `priority`
5. **`idx_programs_composite`** - Composite index on `(channel_id, day_of_week, start_time)`
6. **`idx_programs_category_priority`** - Composite index on `(category, priority)`
7. **`idx_programs_time_range`** - Composite index on `(start_time, end_time)`

### Business Logic Functions

#### `count_15min_intervals(start_time, end_time)`
- **Purpose**: Calculates the number of 15-minute intervals for a TV program
- **Key Feature**: Handles overnight programs (e.g., 23:30 - 01:15)
- **Algorithm**: 
  ```sql
  -- For overnight programs: (24:00 - start) + (end - 00:00)
  -- For regular programs: (end - start)
  -- Result: duration_minutes / 15 (integer division)
  ```

#### Trigger System
- **`trigger_update_program_intervals`**: Automatically maintains `program_intervals` table
- **Operations**: INSERT/UPDATE/DELETE on `programs` triggers recalculation
- **Performance Impact**: Tested extensively under high-load scenarios

## Data Generator

### `TVProgramDataGenerator` Class

The data generator creates realistic TV program data using the Faker library:

#### Categories and Scheduling Logic
```python
categories = [
    'News', 'Drama', 'Comedy', 'Sports', 'Documentary', 
    'Reality', 'Kids', 'Movies', 'Talk Show', 'Game Show'
]
```

#### Realistic Time Slot Generation
- **Prime Time (18:00-22:00)**: Drama, Movies, Reality shows
- **Morning (06:00-12:00)**: News, Talk Shows, Kids programs
- **Daytime (12:00-18:00)**: Game Shows, Talk Shows, Drama
- **Late Night (22:00-06:00)**: Movies, Comedy, Late-night shows

#### Program Name Generation
- **Pattern-based**: "Morning News Update", "Championship Sports Tonight"
- **Realistic suffixes**: "Live", "Update", "Tonight", "Special"
- **Category-appropriate**: Sports programs get sports-related names

#### Batch Processing
- **Configurable batch sizes**: 1K-50K records per batch
- **Progress monitoring**: Real-time ETA and throughput tracking
- **Memory optimization**: Efficient bulk insert using `execute_batch`

### Data Characteristics

For 1M records, the generator produces:
- **~100,000 programs per category** (balanced distribution)
- **~1,000 channels** (realistic TV channel count)
- **Realistic time distributions** (more programs in prime time)
- **Overnight programs**: ~10-15% of total (realistic for late-night programming)

## Testing Approach

### Test Philosophy

1. **Realistic Scale**: Tests use 50K-1M+ records to simulate real-world TV scheduling systems
2. **Real-world Queries**: Test patterns mirror actual TV guide application queries
3. **Performance Baselines**: Establish performance benchmarks for different data sizes
4. **Index Effectiveness**: Validate that indexes provide expected performance improvements
5. **Trigger Performance**: Ensure automatic interval calculation doesn't become a bottleneck

### Test Types

#### `full` - Comprehensive Testing
- **Data generation**: 500K-1M records
- **All test categories**: 28+ individual tests
- **Duration**: 5-15 minutes
- **Use case**: Weekly regression testing, major releases

#### `quick` - CI/PR Testing  
- **Data generation**: 50K-100K records
- **Essential categories**: Basic, Filtered, Aggregation queries
- **Duration**: 2-5 minutes
- **Use case**: Pull request validation, daily CI

#### `insert-only` - Data Generation Performance
- **Focus**: Bulk insert throughput testing
- **Metrics**: Records per second, batch performance
- **Duration**: 1-3 minutes
- **Use case**: Testing data loading strategies

#### `query-only` - Query Performance
- **Focus**: Query performance on existing data
- **No data generation**: Uses current database content
- **Duration**: 30 seconds - 2 minutes
- **Use case**: Testing query optimizations

## Test Categories

### 1. Basic Query Performance (`test_basic_queries`)
**Purpose**: Validate fundamental query operations at scale

- **Total record counts**: `SELECT COUNT(*) FROM programs`
- **Interval counts**: `SELECT COUNT(*) FROM program_intervals`
- **Top-N queries**: Most popular programs by interval count
- **Grouping operations**: Programs by category, channel, day, priority

### 2. Filtered Query Performance (`test_filtered_queries`)
**Purpose**: Test index effectiveness and WHERE clause performance

- **Single-column filters**: By category, channel range, day/priority
- **Time-based filters**: Prime time programs (18:00-22:00)
- **Multi-table joins**: Programs with interval calculations
- **Complex conditions**: Overnight programs (start_time > end_time)

### 3. Aggregation Performance (`test_aggregation_queries`)
**Purpose**: Validate complex analytical query performance

- **Statistical functions**: AVG, MAX, MIN interval counts by category
- **Multi-dimensional grouping**: Channel + day combinations
- **Time-based analysis**: Hourly program distribution
- **Cross-category analysis**: Category + priority statistics

### 4. JOIN Performance (`test_join_performance`)
**Purpose**: Test relationship query performance between main tables

- **INNER JOINs**: Programs with their calculated intervals
- **LEFT JOINs**: All programs with optional interval data
- **Complex JOINs**: Multi-condition joins with aggregation and HAVING clauses

### 5. Index Effectiveness (`test_index_effectiveness`)
**Purpose**: Validate that indexes provide expected performance improvements

- **Single-column indexes**: Category, channel, day filters
- **Composite indexes**: Multi-column query optimization
- **Query plan analysis**: EXPLAIN output validation (when available)

### 6. Update/Trigger Performance (`test_update_performance`)
**Purpose**: Test trigger system performance under update load

- **Single updates**: Individual program modifications
- **Batch updates**: Category-wide and channel-range updates
- **Trigger efficiency**: Interval recalculation performance
- **Concurrency impact**: Update performance at scale

### 7. Overnight Program Performance (`test_overnight_program_performance`)
**Purpose**: Test the core business logic performance for complex scheduling

- **Overnight identification**: Programs spanning midnight
- **Interval calculation**: Function performance for complex time calculations
- **Edge cases**: Various overnight duration scenarios
- **Bulk processing**: Performance of overnight program operations

## Performance Tests Detailed

### Basic Query Tests

#### Count Operations
```sql
-- Test: Count all programs
SELECT COUNT(*) FROM programs;
-- Expected: <1ms for 100K records, <10ms for 1M records
-- Purpose: Validate table scan performance

-- Test: Count all intervals  
SELECT COUNT(*) FROM program_intervals;
-- Expected: <1ms for 100K records, <10ms for 1M records
-- Purpose: Validate trigger-generated data integrity
```

#### Top-N and Ranking
```sql
-- Test: Top 100 by intervals
SELECT program_name, interval_count 
FROM program_intervals 
ORDER BY interval_count DESC 
LIMIT 100;
-- Expected: <20ms for 1M records
-- Purpose: Test ORDER BY performance on calculated data
```

#### Grouping and Categorization
```sql
-- Test: Programs by category
SELECT category, COUNT(*) 
FROM programs 
WHERE category IS NOT NULL 
GROUP BY category 
ORDER BY COUNT(*) DESC;
-- Expected: <50ms for 1M records with index
-- Purpose: Validate GROUP BY performance with indexes
```

### Filtered Query Tests

#### Index-Optimized Filters
```sql
-- Test: Filter by category (News)
SELECT * FROM programs WHERE category = 'News';
-- Expected: Uses idx_programs_category
-- Performance: <100ms for 100K matching records

-- Test: Channel range filter
SELECT * FROM programs WHERE channel_id BETWEEN 1 AND 50;
-- Expected: Uses idx_programs_channel
-- Performance: <200ms for large result sets
```

#### Time-Based Filtering
```sql
-- Test: Prime time programs (6-10 PM)
SELECT * FROM programs 
WHERE start_time >= '18:00' AND start_time < '22:00';
-- Expected: Uses idx_programs_time_range
-- Performance: <500ms for ~40% of total records

-- Test: Overnight programs
SELECT * FROM programs WHERE start_time > end_time;
-- Expected: Sequential scan (no suitable index)
-- Performance: <1s for 1M records (10-15% match rate)
```

### Aggregation Tests

#### Statistical Analysis
```sql
-- Test: Category statistics with intervals
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
ORDER BY avg_intervals DESC;
-- Expected: <1s for 1M records
-- Purpose: Test JOIN + aggregation performance
```

#### Multi-Dimensional Analysis
```sql
-- Test: Channel-day analysis
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
LIMIT 100;
-- Expected: <2s for 1M records
-- Purpose: Test complex multi-table aggregation
```

### JOIN Performance Tests

#### Standard JOINs
```sql
-- Test: Inner join with filter
SELECT p.program_name, p.category, pi.interval_count
FROM programs p
INNER JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.category = 'Movies';
-- Expected: <500ms for 100K matching records
-- Purpose: Test filtered JOIN performance
```

#### Complex JOINs with Aggregation
```sql
-- Test: JOIN with aggregation and HAVING
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
ORDER BY total_intervals DESC;
-- Expected: <1s for 1M records
-- Purpose: Test complex JOIN with aggregation logic
```

### Index Effectiveness Tests

#### Single-Column Index Tests
```sql
-- Test: Category filter (should use idx_programs_category)
SELECT * FROM programs WHERE category = 'Sports';
-- Expected: Index scan, <100ms for 100K matches
-- Validation: EXPLAIN shows index usage

-- Test: Channel filter (should use idx_programs_channel)  
SELECT * FROM programs WHERE channel_id = 100;
-- Expected: Index scan, <10ms for 1K matches
-- Validation: EXPLAIN shows index usage
```

#### Composite Index Tests
```sql
-- Test: Composite index effectiveness
SELECT * FROM programs 
WHERE channel_id = 50 AND day_of_week = 1 AND start_time >= '18:00';
-- Expected: Uses idx_programs_composite
-- Performance: <20ms for specific channel/day/time combinations
-- Purpose: Validate multi-column index optimization
```

### Update/Trigger Performance Tests

#### Single Update Performance
```sql
-- Test: Individual program updates
UPDATE programs SET priority = 2 WHERE program_name = 'Test Program';
-- Expected: <5ms per update including trigger execution
-- Purpose: Test trigger overhead for single updates
```

#### Batch Update Performance  
```sql
-- Test: Category-wide updates
UPDATE programs SET priority = 3 WHERE category = 'News';
-- Expected: 5K-15K records/second including trigger recalculation
-- Purpose: Test trigger performance under bulk operations

-- Test: Channel range updates
UPDATE programs SET priority = 1 WHERE channel_id BETWEEN 1 AND 50;
-- Expected: Similar throughput to category updates
-- Purpose: Test index-assisted bulk updates
```

### Overnight Program Tests

#### Core Function Performance
```sql
-- Test: Function performance for overnight calculations
SELECT count_15min_intervals('23:30'::time, '00:15'::time);
-- Expected: <1ms per calculation
-- Purpose: Test core business logic efficiency

-- Test cases:
-- 23:30-00:15 (45 min) → 3 intervals
-- 23:45-00:30 (45 min) → 3 intervals  
-- 22:00-02:00 (4 hours) → 16 intervals
-- 23:00-01:00 (2 hours) → 8 intervals
```

#### Overnight Program Queries
```sql
-- Test: Find all overnight programs
SELECT * FROM programs WHERE start_time > end_time;
-- Expected: <2s for 1M records (10-15% match rate)
-- Purpose: Test complex condition performance at scale

-- Test: Overnight programs with intervals
SELECT p.program_name, p.start_time, p.end_time, pi.interval_count
FROM programs p 
JOIN program_intervals pi ON p.program_name = pi.program_name
WHERE p.start_time > p.end_time;
-- Expected: <3s for 1M records  
-- Purpose: Test JOIN performance on complex filtered data
```

## Running Performance Tests

### Local Execution

#### Quick Test (Development)
```bash
# Install dependencies
pip install -r requirements.txt

# Start database
docker-compose up -d

# Run quick performance test
python run_performance_tests.py --records 50000 --batch-size 15000 --test-type quick
```

#### Full Test (Comprehensive)
```bash
# Run comprehensive performance test
python run_performance_tests.py --records 500000 --batch-size 15000 --test-type full

# With custom parameters
python run_performance_tests.py \
  --records 1000000 \
  --batch-size 20000 \
  --test-type full \
  --output-format json \
  --output-file results.json
```

#### Available Parameters

| Parameter | Description | Default | Options |
|-----------|-------------|---------|---------|
| `--records` | Number of test records | 100,000 | 1K-10M+ |
| `--batch-size` | Insert batch size | 5,000 | 1K-50K |
| `--test-type` | Test suite type | quick | full, quick, insert-only, query-only |
| `--output-format` | Result format | console | console, json, github |
| `--output-file` | Output file path | stdout | Any file path |
| `--timeout` | Test timeout (seconds) | 3600 | 60-7200 |
| `--cleanup` | Clean test data after completion | false | true, false |

### Optimal Batch Sizes

Based on performance testing:

| Record Count | Recommended Batch Size | Expected Throughput |
|--------------|----------------------|-------------------|
| 50K | 10,000 | 6,000-8,000 records/sec |
| 100K | 15,000 | 6,500-9,000 records/sec |
| 500K | 15,000 | 6,000-8,000 records/sec |
| 1M+ | 15,000-20,000 | 5,500-7,500 records/sec |

## CI/CD Integration

### GitHub Actions Workflow

The performance testing system integrates with GitHub Actions for automated testing:

#### Trigger Types

1. **Manual Trigger** (`workflow_dispatch`)
   - Configurable parameters via GitHub UI
   - Test any branch
   - Custom record counts and batch sizes

2. **Scheduled Testing** (`schedule`)
   - Weekly regression tests (Sundays 2 AM UTC)
   - 1M records with comprehensive test suite
   - Automated performance trend tracking

3. **Push Triggers** (`push` to main)
   - Quick performance validation (100K records)
   - Triggered by changes to performance-related files

#### Database Isolation

- **Neon Database Branches**: Each test run gets isolated database
- **Automatic Cleanup**: Database branches deleted after test completion
- **Schema Management**: Fresh schema applied for each test run

#### Results Publishing

1. **GitHub Pages**: Interactive HTML reports published automatically
2. **Performance Dashboard**: Historical trend tracking across test runs
3. **Artifacts**: Downloadable JSON results and logs
4. **PR Comments**: Performance summaries posted to pull requests

### Example Workflow Usage

```yaml
# Manual trigger with custom parameters
on:
  workflow_dispatch:
    inputs:
      record_count:
        description: 'Number of records to generate'
        default: '500000'
      batch_size:
        description: 'Batch size for inserts'  
        default: '15000'
      test_type:
        description: 'Type of performance test'
        default: 'full'
        options: ['full', 'quick', 'insert-only', 'query-only']
```

## Interpreting Results

### Key Performance Metrics

#### Data Generation Metrics
- **Insert Rate**: Records per second during bulk loading
- **Batch Performance**: Time per batch including overhead
- **Memory Usage**: Peak memory consumption during generation

#### Query Performance Metrics
- **Execution Time**: Query completion time in seconds
- **Rows Per Second**: Throughput for large result sets
- **Row Count**: Number of records returned/processed

#### System Performance Indicators
- **Index Effectiveness**: Query time reduction with indexes
- **Join Performance**: Multi-table query efficiency  
- **Trigger Overhead**: Update performance impact
- **Aggregation Speed**: Complex analysis query performance

### Performance Benchmarks

#### Excellent Performance (Green Zone)
- **Basic queries**: <50ms
- **Filtered queries**: <200ms  
- **Aggregations**: <1s
- **JOINs**: <500ms
- **Updates**: >5K records/sec

#### Acceptable Performance (Yellow Zone)
- **Basic queries**: 50-200ms
- **Filtered queries**: 200ms-1s
- **Aggregations**: 1-3s
- **JOINs**: 500ms-2s  
- **Updates**: 2K-5K records/sec

#### Performance Issues (Red Zone)
- **Basic queries**: >200ms
- **Filtered queries**: >1s
- **Aggregations**: >3s
- **JOINs**: >2s
- **Updates**: <2K records/sec

### Trend Analysis

The performance dashboard tracks key metrics over time:

1. **Insert Performance Trends**: Batch size optimization over time
2. **Query Performance Evolution**: Impact of schema changes
3. **Index Effectiveness**: Performance improvements from new indexes
4. **Regression Detection**: Performance degradation alerts

## Optimization Strategies

### Database Optimizations

#### Index Strategy
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_programs_composite ON programs(channel_id, day_of_week, start_time);

-- Partial indexes for specific conditions  
CREATE INDEX idx_overnight_programs ON programs(start_time, end_time) 
WHERE start_time > end_time;

-- Covering indexes to avoid table lookups
CREATE INDEX idx_programs_category_covering ON programs(category) 
INCLUDE (program_name, start_time, end_time);
```

#### Query Optimizations
```sql
-- Use LIMIT for large result sets
SELECT * FROM programs WHERE category = 'News' LIMIT 1000;

-- Optimize aggregations with appropriate GROUP BY order
SELECT category, COUNT(*) 
FROM programs 
WHERE category IS NOT NULL 
GROUP BY category;

-- Use EXISTS instead of IN for better performance
SELECT * FROM programs p 
WHERE EXISTS (
    SELECT 1 FROM program_intervals pi 
    WHERE pi.program_name = p.program_name
);
```

### Application-Level Optimizations

#### Batch Processing
- **Optimal batch sizes**: 15,000-20,000 records for PostgreSQL
- **Connection pooling**: Reuse database connections
- **Transaction management**: Group related operations

#### Caching Strategies
- **Query result caching**: Cache frequent aggregation results
- **Materialized views**: Pre-calculate complex aggregations
- **Application-level caching**: Cache category and channel lookups

### Monitoring and Alerting

#### Performance Monitoring
```sql
-- Monitor query performance
SELECT query, mean_time, calls, total_time 
FROM pg_stat_statements 
ORDER BY mean_time DESC;

-- Monitor index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

#### Alert Thresholds
- **Query time degradation**: >20% slower than baseline
- **Insert performance**: <3,000 records/sec sustained
- **Failed tests**: Any test exceeding timeout
- **Memory usage**: >80% of available memory during tests

## Conclusion

The TV Show Intervals performance testing system provides comprehensive validation of database performance characteristics at scale. With realistic data generation, extensive test coverage, and automated CI integration, it ensures the system can handle real-world TV scheduling workloads efficiently.

The system's modular design allows for easy extension with new test categories, and the detailed reporting provides clear insights into performance trends and optimization opportunities.

For questions or contributions to the performance testing system, see the main project README or open an issue in the repository.