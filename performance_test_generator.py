"""
Performance test data generator for TV Show Intervals Demo.
Generates realistic test data at scale to demonstrate system performance.
"""

import random
import time
from datetime import datetime, timedelta
from faker import Faker
import psycopg2
from psycopg2.extras import execute_batch
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TVProgramDataGenerator:
    def __init__(self, db_connection):
        self.db = db_connection
        self.fake = Faker()
        
        # TV show categories for realistic data
        self.categories = [
            'News', 'Drama', 'Comedy', 'Sports', 'Documentary', 
            'Reality', 'Kids', 'Movies', 'Talk Show', 'Game Show'
        ]
        
        # Common TV show name patterns
        self.show_prefixes = [
            'Morning', 'Evening', 'Late Night', 'Prime Time', 'Weekend',
            'Daily', 'Weekly', 'Special', 'Live', 'Breaking'
        ]
        
        self.show_types = [
            'News', 'Update', 'Report', 'Show', 'Talk', 'Movie',
            'Series', 'Special', 'Live', 'Hour', 'Block', 'Zone'
        ]

    def generate_realistic_show_name(self, category=None):
        """Generate realistic TV show names based on category."""
        if category == 'News':
            return f"{random.choice(self.show_prefixes)} {random.choice(['News', 'Update', 'Report', 'Brief'])}"
        elif category == 'Sports':
            sports = ['Football', 'Basketball', 'Baseball', 'Soccer', 'Tennis', 'Golf']
            return f"{random.choice(sports)} {random.choice(['Live', 'Tonight', 'Weekly', 'Update'])}"
        elif category == 'Movies':
            return f"{self.fake.catch_phrase().replace(',', '')} Movie"
        elif category == 'Drama':
            return f"{self.fake.word().title()} {random.choice(['Chronicles', 'Stories', 'Drama', 'Series'])}"
        elif category == 'Comedy':
            return f"{self.fake.word().title()} {random.choice(['Comedy', 'Laughs', 'Fun', 'Show'])}"
        elif category == 'Kids':
            return f"{self.fake.first_name()}'s {random.choice(['Adventure', 'World', 'Fun Time', 'Show'])}"
        else:
            return f"{random.choice(self.show_prefixes)} {random.choice(self.show_types)}"

    def generate_realistic_time_slot(self, category=None):
        """Generate realistic time slots based on program category."""
        if category == 'News':
            # News typically at top of hour: 6AM, 7AM, 12PM, 6PM, 11PM
            hours = [6, 7, 12, 18, 23]
            start_hour = random.choice(hours)
            duration_minutes = random.choice([15, 30, 60])  # Common news durations
        elif category == 'Movies':
            # Movies typically 90-180 minutes, starting at reasonable times
            start_hour = random.randint(18, 22)  # Prime time movies
            duration_minutes = random.choice([90, 120, 150, 180])
        elif category == 'Sports':
            # Sports events can be long and at various times
            start_hour = random.randint(12, 22)
            duration_minutes = random.choice([120, 180, 240])  # 2-4 hours
        elif category == 'Kids':
            # Kids shows typically morning and afternoon
            start_hour = random.choice([7, 8, 9, 15, 16, 17])
            duration_minutes = random.choice([15, 30, 60])
        elif category in ['Drama', 'Comedy']:
            # Prime time shows
            start_hour = random.randint(19, 22)
            duration_minutes = random.choice([30, 60])
        else:
            # Regular programming
            start_hour = random.randint(6, 23)
            duration_minutes = random.choice([15, 30, 45, 60, 90, 120])
        
        # Generate start time
        start_minute = random.choice([0, 15, 30, 45])  # On quarter hours
        start_time = f"{start_hour:02d}:{start_minute:02d}"
        
        # Calculate end time (may cross midnight)
        end_total_minutes = (start_hour * 60 + start_minute + duration_minutes) % (24 * 60)
        end_hour = end_total_minutes // 60
        end_minute = end_total_minutes % 60
        end_time = f"{end_hour:02d}:{end_minute:02d}"
        
        return start_time, end_time

    def generate_program_batch(self, batch_size=1000, start_id=0):
        """Generate a batch of realistic TV programs."""
        programs = []
        
        for i in range(batch_size):
            # Select category and generate appropriate data
            category = random.choice(self.categories)
            channel_id = random.randint(1, 500)  # 500 channels
            day_of_week = random.randint(1, 7)
            priority = random.choices([1, 2, 3], weights=[70, 25, 5])[0]  # Most shows are priority 1
            
            # Generate show name and times
            program_name = self.generate_realistic_show_name(category)
            start_time, end_time = self.generate_realistic_time_slot(category)
            
            # Make names unique by adding channel and day info
            unique_name = f"{program_name} (Ch{channel_id:03d}-D{day_of_week})-{start_id + i}"
            
            programs.append((
                unique_name,      # program_name
                start_time,       # start_time
                end_time,         # end_time
                channel_id,       # channel_id
                category,         # category
                priority,         # priority
                day_of_week       # day_of_week
            ))
        
        return programs

    def bulk_insert_programs(self, total_records=1000000, batch_size=5000):
        """Insert programs in batches with performance monitoring."""
        logger.info(f"Starting bulk insert of {total_records:,} records in batches of {batch_size:,}")
        
        insert_query = """
        INSERT INTO programs (program_name, start_time, end_time, channel_id, category, priority, day_of_week)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        
        total_batches = (total_records + batch_size - 1) // batch_size
        total_time = 0
        
        with self.db.cursor() as cursor:
            for batch_num in range(total_batches):
                batch_start = batch_num * batch_size
                current_batch_size = min(batch_size, total_records - batch_start)
                
                # Generate batch data
                batch_start_time = time.time()
                programs = self.generate_program_batch(current_batch_size, batch_start)
                generation_time = time.time() - batch_start_time
                
                # Insert batch
                insert_start_time = time.time()
                execute_batch(cursor, insert_query, programs, page_size=1000)
                self.db.commit()
                insert_time = time.time() - insert_start_time
                
                batch_total_time = generation_time + insert_time
                total_time += batch_total_time
                
                # Log progress
                records_inserted = batch_start + current_batch_size
                avg_time_per_batch = total_time / (batch_num + 1)
                estimated_remaining = avg_time_per_batch * (total_batches - batch_num - 1)
                
                logger.info(
                    f"Batch {batch_num + 1}/{total_batches}: "
                    f"{records_inserted:,}/{total_records:,} records "
                    f"({records_inserted/total_records*100:.1f}%) - "
                    f"Batch time: {batch_total_time:.2f}s "
                    f"(Gen: {generation_time:.2f}s, Insert: {insert_time:.2f}s) - "
                    f"ETA: {estimated_remaining:.0f}s"
                )
        
        logger.info(f"Bulk insert completed in {total_time:.2f} seconds")
        logger.info(f"Average rate: {total_records/total_time:.0f} records/second")
        
        return total_time, total_records/total_time

    def enhance_schema_for_performance(self):
        """Add performance testing enhancements to the schema."""
        enhancements = [
            "ALTER TABLE programs ADD COLUMN IF NOT EXISTS channel_id INTEGER DEFAULT 1",
            "ALTER TABLE programs ADD COLUMN IF NOT EXISTS category VARCHAR(50) DEFAULT 'General'",
            "ALTER TABLE programs ADD COLUMN IF NOT EXISTS priority INTEGER DEFAULT 1",
            "ALTER TABLE programs ADD COLUMN IF NOT EXISTS day_of_week INTEGER DEFAULT 1",
            
            "CREATE INDEX IF NOT EXISTS idx_programs_channel ON programs(channel_id)",
            "CREATE INDEX IF NOT EXISTS idx_programs_category ON programs(category)",
            "CREATE INDEX IF NOT EXISTS idx_programs_day ON programs(day_of_week)",
            "CREATE INDEX IF NOT EXISTS idx_programs_priority ON programs(priority)",
            "CREATE INDEX IF NOT EXISTS idx_programs_composite ON programs(channel_id, day_of_week, start_time)",
            "CREATE INDEX IF NOT EXISTS idx_programs_category_priority ON programs(category, priority)",
            "CREATE INDEX IF NOT EXISTS idx_programs_time_range ON programs(start_time, end_time)",
        ]
        
        with self.db.cursor() as cursor:
            for sql in enhancements:
                try:
                    cursor.execute(sql)
                    logger.info(f"Executed: {sql}")
                except Exception as e:
                    logger.warning(f"Failed to execute {sql}: {e}")
            
            self.db.commit()
        
        logger.info("Schema enhancements completed")

    def cleanup_test_data(self):
        """Remove all test data (for cleanup after performance tests)."""
        with self.db.cursor() as cursor:
            # Delete all programs (triggers will handle interval cleanup)
            cursor.execute("DELETE FROM programs WHERE program_name LIKE '%(Ch%-%)'")
            deleted_count = cursor.rowcount
            self.db.commit()
            
            logger.info(f"Cleaned up {deleted_count:,} test records")
            return deleted_count

    def get_data_statistics(self):
        """Get statistics about current data in the database."""
        with self.db.cursor() as cursor:
            stats = {}
            
            # Program count
            cursor.execute("SELECT COUNT(*) FROM programs")
            stats['total_programs'] = cursor.fetchone()[0]
            
            # Interval count
            cursor.execute("SELECT COUNT(*) FROM program_intervals")
            stats['total_intervals'] = cursor.fetchone()[0]
            
            # Category distribution
            cursor.execute("""
                SELECT category, COUNT(*) 
                FROM programs 
                WHERE category IS NOT NULL 
                GROUP BY category 
                ORDER BY COUNT(*) DESC
            """)
            stats['category_distribution'] = dict(cursor.fetchall())
            
            # Channel distribution
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT channel_id) as unique_channels,
                    MIN(channel_id) as min_channel,
                    MAX(channel_id) as max_channel
                FROM programs 
                WHERE channel_id IS NOT NULL
            """)
            result = cursor.fetchone()
            if result:
                stats['channel_stats'] = {
                    'unique_channels': result[0],
                    'min_channel': result[1], 
                    'max_channel': result[2]
                }
            
            # Time slot distribution
            cursor.execute("""
                SELECT 
                    EXTRACT(HOUR FROM start_time) as hour,
                    COUNT(*) as program_count
                FROM programs 
                GROUP BY EXTRACT(HOUR FROM start_time)
                ORDER BY hour
            """)
            stats['hourly_distribution'] = dict(cursor.fetchall())
            
            logger.info(f"Database statistics: {stats['total_programs']:,} programs, {stats['total_intervals']:,} intervals")
            return stats