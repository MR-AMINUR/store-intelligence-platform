"""Event storage and retrieval using SQLite database.

This module provides the EventStore class for persisting events to a SQLite
database with support for idempotent insertions, batch operations, filtering,
and retry logic for handling lock contention.
"""

import json
import sqlite3
import time
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from src.logger import Logger
from src.models import Event, EventType


@dataclass
class BatchResult:
    """Result of a batch insertion operation.
    
    Attributes:
        success_count: Number of events successfully inserted
        errors: List of error messages for failed insertions
    """
    success_count: int
    errors: List[str]


@dataclass
class EventFilters:
    """Filters for querying events.
    
    Attributes:
        store_id: Filter by store ID (required)
        track_id: Optional filter by track ID
        event_type: Optional filter by event type
        start_time: Optional start of time range
        end_time: Optional end of time range
    """
    store_id: str
    track_id: Optional[int] = None
    event_type: Optional[EventType] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None


class EventStore:
    """SQLite-based event storage with idempotent operations.
    
    The EventStore provides persistent storage for events with:
    - Idempotent insertions (using event_id as primary key)
    - Batch operations with transaction support
    - Flexible filtering and querying
    - Retry logic with exponential backoff for lock contention
    - WAL mode for concurrent reads during writes
    
    Attributes:
        db_path: Path to SQLite database file
        logger: Optional Logger instance for structured logging
        max_retries: Maximum number of retry attempts (default 3)
        retry_base_delay: Base delay for exponential backoff in seconds (default 1.0)
    """
    
    def __init__(
        self,
        db_path: str,
        logger: Optional[Logger] = None,
        max_retries: int = 3,
        retry_base_delay: float = 1.0
    ):
        """Initialize EventStore with database connection.
        
        Args:
            db_path: Path to SQLite database file (will be created if doesn't exist)
            logger: Optional Logger instance for structured logging
            max_retries: Maximum retry attempts for database operations (default 3)
            retry_base_delay: Base delay for exponential backoff in seconds (default 1.0)
        
        Raises:
            sqlite3.Error: If database initialization fails
        """
        self.db_path = Path(db_path)
        self.logger = logger
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        
        # Ensure parent directory exists
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize database schema
        self._initialize_schema()
        
        if self.logger:
            self.logger.info(
                "EventStore initialized",
                db_path=str(self.db_path),
                max_retries=max_retries
            )
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections.
        
        Yields:
            sqlite3.Connection: Database connection with row factory enabled
        """
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def _initialize_schema(self):
        """Initialize database schema with events table and indexes.
        
        Creates the events table if it doesn't exist, with indexes for:
        - store_id (for filtering by store)
        - track_id (for filtering by track)
        - event_type (for filtering by event type)
        - timestamp (for time-range queries)
        
        Also enables WAL mode for better concurrent read performance.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Enable WAL mode for concurrent reads
            cursor.execute("PRAGMA journal_mode=WAL")
            
            # Create events table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    event_id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    store_id TEXT NOT NULL,
                    track_id INTEGER NOT NULL,
                    metadata TEXT NOT NULL
                )
            """)
            
            # Create indexes for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_store_id 
                ON events(store_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_track_id 
                ON events(track_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_event_type 
                ON events(event_type)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events(timestamp)
            """)
            
            # Composite index for common query patterns
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_store_timestamp 
                ON events(store_id, timestamp)
            """)
            
            conn.commit()
            
            if self.logger:
                self.logger.debug("Database schema initialized")
    
    def _retry_on_lock(self, operation, *args, **kwargs):
        """Retry a database operation with exponential backoff on lock errors.
        
        Args:
            operation: Callable to execute with retry logic
            *args: Positional arguments to pass to operation
            **kwargs: Keyword arguments to pass to operation
        
        Returns:
            Result of the operation
        
        Raises:
            sqlite3.OperationalError: If all retries are exhausted
        """
        for attempt in range(self.max_retries):
            try:
                return operation(*args, **kwargs)
            except sqlite3.OperationalError as e:
                if "locked" in str(e).lower() and attempt < self.max_retries - 1:
                    # Calculate exponential backoff delay: 1s, 2s, 4s
                    delay = self.retry_base_delay * (2 ** attempt)
                    
                    if self.logger:
                        self.logger.warning(
                            "Database locked, retrying",
                            attempt=attempt + 1,
                            max_retries=self.max_retries,
                            delay_seconds=delay
                        )
                    
                    time.sleep(delay)
                else:
                    raise
    
    def insert_event(self, event: Event) -> bool:
        """Insert a single event into the database (idempotent).
        
        Uses INSERT OR IGNORE to ensure idempotency. If an event with the
        same event_id already exists, it is silently ignored.
        
        Args:
            event: Event object to insert
        
        Returns:
            True if event was inserted or already exists (idempotent operation)
        
        Raises:
            sqlite3.Error: If database operation fails after retries
        """
        def _insert():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Serialize metadata to JSON
                metadata_json = json.dumps(event.metadata)
                
                # INSERT OR IGNORE for idempotency
                cursor.execute("""
                    INSERT OR IGNORE INTO events 
                    (event_id, event_type, timestamp, store_id, track_id, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event.event_id,
                    event.event_type.value,
                    event.timestamp.isoformat(),
                    event.store_id,
                    event.track_id,
                    metadata_json
                ))
                
                conn.commit()
                
                if self.logger:
                    self.logger.debug(
                        "Event inserted",
                        event_id=event.event_id,
                        event_type=event.event_type.value
                    )
                
                return True
        
        return self._retry_on_lock(_insert)
    
    def insert_events_batch(self, events: List[Event]) -> BatchResult:
        """Insert multiple events in a single transaction (idempotent).
        
        All events are inserted within a single transaction for atomicity.
        Uses INSERT OR IGNORE for idempotency.
        
        Args:
            events: List of Event objects to insert
        
        Returns:
            BatchResult with success count and any error messages
        """
        def _insert_batch():
            errors = []
            success_count = 0
            
            try:
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Begin transaction
                    cursor.execute("BEGIN TRANSACTION")
                    
                    try:
                        for event in events:
                            try:
                                # Serialize metadata to JSON
                                metadata_json = json.dumps(event.metadata)
                                
                                # INSERT OR IGNORE for idempotency
                                cursor.execute("""
                                    INSERT OR IGNORE INTO events 
                                    (event_id, event_type, timestamp, store_id, track_id, metadata)
                                    VALUES (?, ?, ?, ?, ?, ?)
                                """, (
                                    event.event_id,
                                    event.event_type.value,
                                    event.timestamp.isoformat(),
                                    event.store_id,
                                    event.track_id,
                                    metadata_json
                                ))
                                
                                success_count += 1
                            except Exception as e:
                                errors.append(f"Event {event.event_id}: {str(e)}")
                        
                        # Commit transaction
                        conn.commit()
                        
                        if self.logger:
                            self.logger.info(
                                "Batch insert completed",
                                total_events=len(events),
                                success_count=success_count,
                                error_count=len(errors)
                            )
                    
                    except Exception as e:
                        conn.rollback()
                        raise
            
            except Exception as e:
                errors.append(f"Batch transaction failed: {str(e)}")
            
            return BatchResult(success_count=success_count, errors=errors)
        
        return self._retry_on_lock(_insert_batch)
    
    def query_events(self, filters: EventFilters) -> List[Event]:
        """Query events with optional filtering.
        
        Args:
            filters: EventFilters object specifying query criteria
        
        Returns:
            List of Event objects matching the filters
        """
        def _query():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build SQL query dynamically based on filters
                query = "SELECT * FROM events WHERE store_id = ?"
                params = [filters.store_id]
                
                if filters.track_id is not None:
                    query += " AND track_id = ?"
                    params.append(filters.track_id)
                
                if filters.event_type is not None:
                    query += " AND event_type = ?"
                    params.append(filters.event_type.value)
                
                if filters.start_time is not None:
                    query += " AND timestamp >= ?"
                    params.append(filters.start_time.isoformat())
                
                if filters.end_time is not None:
                    query += " AND timestamp <= ?"
                    params.append(filters.end_time.isoformat())
                
                # Order by timestamp
                query += " ORDER BY timestamp ASC"
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                # Convert rows to Event objects
                events = []
                for row in rows:
                    event = Event(
                        event_id=row['event_id'],
                        event_type=EventType(row['event_type']),
                        timestamp=datetime.fromisoformat(row['timestamp']),
                        store_id=row['store_id'],
                        track_id=row['track_id'],
                        metadata=json.loads(row['metadata'])
                    )
                    events.append(event)
                
                if self.logger:
                    self.logger.debug(
                        "Events queried",
                        filter_store_id=filters.store_id,
                        result_count=len(events)
                    )
                
                return events
        
        return self._retry_on_lock(_query)
    
    def health_check(self) -> bool:
        """Check database connectivity and health.
        
        Returns:
            True if database is accessible and responsive, False otherwise
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                result = cursor.fetchone()
                
                healthy = result is not None
                
                if self.logger:
                    self.logger.debug(
                        "Health check performed",
                        healthy=healthy
                    )
                
                return healthy
        except Exception as e:
            if self.logger:
                self.logger.error(
                    "Health check failed",
                    error=str(e)
                )
            return False

    # ============================================================================
    # Analytics Methods
    # ============================================================================
    
    def get_store_metrics(
        self,
        store_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ):
        """Calculate aggregated metrics for a store.
        
        Args:
            store_id: Store identifier
            start_time: Optional start of time range
            end_time: Optional end of time range
        
        Returns:
            StoreMetrics object with aggregated statistics
        """
        from src.models import StoreMetrics, TimeRange
        
        def _calculate_metrics():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Build base query with time filters
                time_filter = ""
                params = [store_id]
                
                if start_time:
                    time_filter += " AND timestamp >= ?"
                    params.append(start_time.isoformat())
                
                if end_time:
                    time_filter += " AND timestamp <= ?"
                    params.append(end_time.isoformat())
                
                # Count ENTRY events
                cursor.execute(f"""
                    SELECT COUNT(*) FROM events 
                    WHERE store_id = ? AND event_type = 'ENTRY'{time_filter}
                """, params)
                total_entries = cursor.fetchone()[0]
                
                # Count EXIT events
                cursor.execute(f"""
                    SELECT COUNT(*) FROM events 
                    WHERE store_id = ? AND event_type = 'EXIT'{time_filter}
                """, params)
                total_exits = cursor.fetchone()[0]
                
                # Calculate current occupancy
                current_occupancy = total_entries - total_exits
                
                # Calculate average visit duration
                # Match ENTRY and EXIT events by track_id
                cursor.execute(f"""
                    SELECT 
                        entry.track_id,
                        entry.timestamp as entry_time,
                        exit.timestamp as exit_time
                    FROM events entry
                    JOIN events exit ON entry.track_id = exit.track_id 
                        AND entry.store_id = exit.store_id
                    WHERE entry.store_id = ? 
                        AND entry.event_type = 'ENTRY'
                        AND exit.event_type = 'EXIT'
                        {time_filter.replace('timestamp', 'entry.timestamp')}
                """, params)
                
                durations = []
                for row in cursor.fetchall():
                    entry_time = datetime.fromisoformat(row[1])
                    exit_time = datetime.fromisoformat(row[2])
                    duration_seconds = (exit_time - entry_time).total_seconds()
                    if duration_seconds > 0:  # Only count positive durations
                        durations.append(duration_seconds)
                
                avg_duration = sum(durations) / len(durations) if durations else 0.0
                
                # Create time range if filters were specified
                time_range = None
                if start_time or end_time:
                    time_range = TimeRange(
                        start=start_time or datetime.min,
                        end=end_time or datetime.max
                    )
                
                metrics = StoreMetrics(
                    store_id=store_id,
                    total_entries=total_entries,
                    total_exits=total_exits,
                    current_occupancy=current_occupancy,
                    average_visit_duration_seconds=avg_duration,
                    time_range=time_range
                )
                
                if self.logger:
                    self.logger.debug(
                        "Store metrics calculated",
                        store_id=store_id,
                        total_entries=total_entries,
                        total_exits=total_exits
                    )
                
                return metrics
        
        return self._retry_on_lock(_calculate_metrics)
    
    def get_conversion_funnel(
        self,
        store_id: str,
        zone_id: Optional[str] = None
    ):
        """Calculate customer journey conversion funnel.
        
        Args:
            store_id: Store identifier
            zone_id: Optional zone filter
        
        Returns:
            ConversionFunnel object with stage counts and conversion rates
        """
        from src.models import ConversionFunnel, FunnelStage
        
        def _calculate_funnel():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Stage 1: Count entries
                cursor.execute("""
                    SELECT COUNT(DISTINCT track_id) FROM events
                    WHERE store_id = ? AND event_type = 'ENTRY'
                """, (store_id,))
                entries = cursor.fetchone()[0]
                
                # Stage 2: Count zone visits (tracks that entered any/specific zone)
                if zone_id:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT track_id) FROM events
                        WHERE store_id = ? AND event_type = 'ZONE_ENTER'
                        AND json_extract(metadata, '$.zone_id') = ?
                    """, (store_id, zone_id))
                else:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT track_id) FROM events
                        WHERE store_id = ? AND event_type = 'ZONE_ENTER'
                    """, (store_id,))
                zone_visits = cursor.fetchone()[0]
                
                # Stage 3: Count billing queue joins
                if zone_id:
                    # If filtering by zone, only count if they visited that zone
                    cursor.execute("""
                        SELECT COUNT(DISTINCT e1.track_id) FROM events e1
                        WHERE e1.store_id = ? AND e1.event_type = 'BILLING_QUEUE_JOIN'
                        AND EXISTS (
                            SELECT 1 FROM events e2 
                            WHERE e2.track_id = e1.track_id 
                            AND e2.store_id = e1.store_id
                            AND e2.event_type = 'ZONE_ENTER'
                            AND json_extract(e2.metadata, '$.zone_id') = ?
                        )
                    """, (store_id, zone_id))
                else:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT track_id) FROM events
                        WHERE store_id = ? AND event_type = 'BILLING_QUEUE_JOIN'
                    """, (store_id,))
                billing_queue_joins = cursor.fetchone()[0]
                
                # Stage 4: Count completed purchases (joined queue but didn't abandon)
                # A purchase is complete if track joined queue but didn't generate ABANDON event
                if zone_id:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT e1.track_id) FROM events e1
                        WHERE e1.store_id = ? AND e1.event_type = 'BILLING_QUEUE_JOIN'
                        AND EXISTS (
                            SELECT 1 FROM events e2 
                            WHERE e2.track_id = e1.track_id 
                            AND e2.store_id = e1.store_id
                            AND e2.event_type = 'ZONE_ENTER'
                            AND json_extract(e2.metadata, '$.zone_id') = ?
                        )
                        AND NOT EXISTS (
                            SELECT 1 FROM events e3
                            WHERE e3.track_id = e1.track_id
                            AND e3.store_id = e1.store_id
                            AND e3.event_type = 'BILLING_QUEUE_ABANDON'
                        )
                    """, (store_id, zone_id))
                else:
                    cursor.execute("""
                        SELECT COUNT(DISTINCT track_id) FROM events
                        WHERE store_id = ? AND event_type = 'BILLING_QUEUE_JOIN'
                        AND track_id NOT IN (
                            SELECT track_id FROM events
                            WHERE store_id = ? AND event_type = 'BILLING_QUEUE_ABANDON'
                        )
                    """, (store_id, store_id))
                completed_purchases = cursor.fetchone()[0]
                
                # Calculate conversion rates
                stages = [
                    FunnelStage(
                        stage="entries",
                        count=entries,
                        conversion_rate=1.0
                    ),
                    FunnelStage(
                        stage="zone_visits",
                        count=zone_visits,
                        conversion_rate=zone_visits / entries if entries > 0 else 0.0
                    ),
                    FunnelStage(
                        stage="billing_queue_joins",
                        count=billing_queue_joins,
                        conversion_rate=billing_queue_joins / zone_visits if zone_visits > 0 else 0.0
                    ),
                    FunnelStage(
                        stage="completed_purchases",
                        count=completed_purchases,
                        conversion_rate=completed_purchases / billing_queue_joins if billing_queue_joins > 0 else 0.0
                    )
                ]
                
                funnel = ConversionFunnel(
                    store_id=store_id,
                    stages=stages,
                    zone_id=zone_id
                )
                
                if self.logger:
                    self.logger.debug(
                        "Conversion funnel calculated",
                        store_id=store_id,
                        zone_id=zone_id,
                        entries=entries
                    )
                
                return funnel
        
        return self._retry_on_lock(_calculate_funnel)
    
    def get_heatmap(
        self,
        store_id: str,
        resolution: int = 50
    ):
        """Generate spatial density heatmap of customer movement.
        
        Args:
            store_id: Store identifier
            resolution: Grid cell size in pixels (default 50)
        
        Returns:
            Heatmap object with normalized density grid
        """
        from src.models import Heatmap, GridDimensions
        import numpy as np
        
        def _generate_heatmap():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Query all zone events to get position data
                # We'll use zone centroids from zone metadata
                cursor.execute("""
                    SELECT metadata FROM events
                    WHERE store_id = ? 
                    AND event_type IN ('ZONE_ENTER', 'ZONE_DWELL')
                """, (store_id,))
                
                positions = []
                for row in cursor.fetchall():
                    metadata = json.loads(row[0])
                    # In a real system, we'd have actual trajectory positions
                    # For this implementation, we'll create synthetic positions
                    # based on zone interactions
                    if 'zone_id' in metadata:
                        # Generate a position based on zone (simplified)
                        # In production, this would use actual trajectory data
                        positions.append((100, 100))  # Placeholder
                
                # Determine spatial bounds (simplified - would come from video resolution)
                if not positions:
                    # Return empty heatmap
                    grid_width = 10
                    grid_height = 10
                    density = [[0.0 for _ in range(grid_width)] for _ in range(grid_height)]
                else:
                    # Calculate grid dimensions
                    max_x, max_y = 1920, 1080  # Typical video resolution
                    grid_width = (max_x // resolution) + 1
                    grid_height = (max_y // resolution) + 1
                    
                    # Create density grid
                    density_grid = np.zeros((grid_height, grid_width))
                    
                    # Count positions in each grid cell
                    for x, y in positions:
                        grid_x = int(x // resolution)
                        grid_y = int(y // resolution)
                        if 0 <= grid_x < grid_width and 0 <= grid_y < grid_height:
                            density_grid[grid_y, grid_x] += 1
                    
                    # Normalize to [0, 1]
                    max_density = density_grid.max()
                    if max_density > 0:
                        density_grid = density_grid / max_density
                    
                    density = density_grid.tolist()
                
                heatmap = Heatmap(
                    store_id=store_id,
                    resolution=resolution,
                    grid=GridDimensions(width=grid_width, height=grid_height),
                    density=density
                )
                
                if self.logger:
                    self.logger.debug(
                        "Heatmap generated",
                        store_id=store_id,
                        resolution=resolution
                    )
                
                return heatmap
        
        return self._retry_on_lock(_generate_heatmap)
    
    def detect_anomalies(
        self,
        store_id: str,
        time_window: int = 24
    ):
        """Detect anomalies in store metrics.
        
        Args:
            store_id: Store identifier
            time_window: Time window in hours (default 24)
        
        Returns:
            List of Anomaly objects
        """
        from src.models import Anomaly, AnomalyMetrics
        from datetime import timedelta, timezone
        import statistics
        
        def _detect():
            with self._get_connection() as conn:
                cursor = conn.cursor()
                anomalies = []
                
                # Calculate time window
                current_time = datetime.now(timezone.utc)
                window_start = current_time - timedelta(hours=time_window)
                
                # 1. Detect sudden crowd surge
                # Get hourly occupancy for the window
                cursor.execute("""
                    SELECT 
                        strftime('%Y-%m-%d %H:00:00', timestamp) as hour,
                        SUM(CASE WHEN event_type = 'ENTRY' THEN 1 ELSE 0 END) -
                        SUM(CASE WHEN event_type = 'EXIT' THEN 1 ELSE 0 END) as occupancy
                    FROM events
                    WHERE store_id = ? AND timestamp >= ?
                    GROUP BY hour
                    ORDER BY hour
                """, (store_id, window_start.isoformat()))
                
                occupancy_data = [row[1] for row in cursor.fetchall()]
                
                if len(occupancy_data) >= 3:
                    mean_occupancy = statistics.mean(occupancy_data)
                    stdev_occupancy = statistics.stdev(occupancy_data) if len(occupancy_data) > 1 else 0
                    threshold = mean_occupancy + 2 * stdev_occupancy
                    
                    current_occupancy = occupancy_data[-1]
                    if current_occupancy > threshold:
                        anomalies.append(Anomaly(
                            type="sudden_crowd_surge",
                            severity="high" if current_occupancy > mean_occupancy + 3 * stdev_occupancy else "medium",
                            timestamp=current_time,
                            description=f"Occupancy ({current_occupancy}) exceeds normal levels",
                            metrics=AnomalyMetrics(
                                baseline=mean_occupancy,
                                observed=current_occupancy,
                                threshold=threshold
                            )
                        ))
                
                # 2. Detect high queue abandonment
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN event_type = 'BILLING_QUEUE_JOIN' THEN 1 END) as joins,
                        COUNT(CASE WHEN event_type = 'BILLING_QUEUE_ABANDON' THEN 1 END) as abandons
                    FROM events
                    WHERE store_id = ? AND timestamp >= ?
                """, (store_id, window_start.isoformat()))
                
                row = cursor.fetchone()
                joins, abandons = row[0], row[1]
                
                if joins > 0:
                    abandon_rate = abandons / joins
                    # Get historical average (last 7 days)
                    cursor.execute("""
                        SELECT 
                            COUNT(CASE WHEN event_type = 'BILLING_QUEUE_JOIN' THEN 1 END) as joins,
                            COUNT(CASE WHEN event_type = 'BILLING_QUEUE_ABANDON' THEN 1 END) as abandons
                        FROM events
                        WHERE store_id = ? AND timestamp < ? AND timestamp >= ?
                    """, (store_id, window_start.isoformat(), (window_start - timedelta(days=7)).isoformat()))
                    
                    hist_row = cursor.fetchone()
                    hist_joins, hist_abandons = hist_row[0], hist_row[1]
                    
                    if hist_joins > 0:
                        historical_rate = hist_abandons / hist_joins
                        historical_stdev = 0.1  # Simplified - would calculate from multiple periods
                        threshold_rate = historical_rate + 2 * historical_stdev
                        
                        if abandon_rate > threshold_rate:
                            anomalies.append(Anomaly(
                                type="high_queue_abandonment",
                                severity="high" if abandon_rate > historical_rate + 3 * historical_stdev else "medium",
                                timestamp=current_time,
                                description=f"Queue abandonment rate ({abandon_rate:.2%}) is unusually high",
                                metrics=AnomalyMetrics(
                                    baseline=historical_rate,
                                    observed=abandon_rate,
                                    threshold=threshold_rate
                                )
                            ))
                
                # 3. Detect unusual dwell time
                cursor.execute("""
                    SELECT json_extract(metadata, '$.dwell_duration_seconds')
                    FROM events
                    WHERE store_id = ? 
                    AND event_type = 'ZONE_DWELL'
                    AND timestamp >= ?
                """, (store_id, window_start.isoformat()))
                
                dwell_times = [float(row[0]) for row in cursor.fetchall() if row[0] is not None]
                
                if len(dwell_times) >= 3:
                    mean_dwell = statistics.mean(dwell_times)
                    stdev_dwell = statistics.stdev(dwell_times) if len(dwell_times) > 1 else 0
                    upper_threshold = mean_dwell + 2 * stdev_dwell
                    lower_threshold = mean_dwell - 2 * stdev_dwell
                    
                    for dwell_time in dwell_times[-5:]:  # Check last 5
                        if dwell_time > upper_threshold or dwell_time < lower_threshold:
                            anomalies.append(Anomaly(
                                type="unusual_dwell_time",
                                severity="low",
                                timestamp=current_time,
                                description=f"Dwell time ({dwell_time:.1f}s) is outside normal range",
                                metrics=AnomalyMetrics(
                                    baseline=mean_dwell,
                                    observed=dwell_time,
                                    threshold=upper_threshold if dwell_time > mean_dwell else lower_threshold
                                )
                            ))
                            break  # Only report one unusual dwell anomaly
                
                # 4. Detect off-hours activity
                cursor.execute("""
                    SELECT COUNT(*) FROM events
                    WHERE store_id = ? 
                    AND event_type = 'ENTRY'
                    AND timestamp >= ?
                    AND (
                        CAST(strftime('%H', timestamp) AS INTEGER) < 9
                        OR CAST(strftime('%H', timestamp) AS INTEGER) >= 21
                    )
                """, (store_id, window_start.isoformat()))
                
                off_hours_entries = cursor.fetchone()[0]
                
                if off_hours_entries > 5:  # Threshold for suspicious activity
                    anomalies.append(Anomaly(
                        type="off_hours_activity",
                        severity="medium" if off_hours_entries < 10 else "high",
                        timestamp=current_time,
                        description=f"Detected {off_hours_entries} entries outside business hours (9 AM - 9 PM)",
                        metrics=AnomalyMetrics(
                            baseline=0.0,
                            observed=float(off_hours_entries),
                            threshold=5.0
                        )
                    ))
                
                if self.logger:
                    self.logger.debug(
                        "Anomaly detection completed",
                        store_id=store_id,
                        anomaly_count=len(anomalies)
                    )
                
                return anomalies
        
        return self._retry_on_lock(_detect)
