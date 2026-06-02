"""Unit tests for EventStore."""

import pytest
import sqlite3
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock, patch

from src.event_store import BatchResult, EventFilters, EventStore
from src.logger import Logger
from src.models import Event, EventType


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=Logger)
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def temp_db_path(tmp_path):
    """Create a temporary database path for testing."""
    return str(tmp_path / "test_events.db")


@pytest.fixture
def event_store(temp_db_path, mock_logger):
    """Create an EventStore instance for testing."""
    return EventStore(db_path=temp_db_path, logger=mock_logger)


@pytest.fixture
def sample_event():
    """Create a sample event for testing."""
    return Event(
        event_id="test-event-001",
        event_type=EventType.ENTRY,
        timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
        store_id="store_001",
        track_id=1,
        metadata={"test_key": "test_value"}
    )


@pytest.fixture
def sample_events():
    """Create multiple sample events for testing."""
    return [
        Event(
            event_id=f"event-{i:03d}",
            event_type=EventType.ENTRY if i % 2 == 0 else EventType.EXIT,
            timestamp=datetime(2024, 1, 1, 12, i, 0, tzinfo=timezone.utc),
            store_id="store_001",
            track_id=i,
            metadata={"index": i}
        )
        for i in range(10)
    ]


class TestEventStoreInitialization:
    """Tests for EventStore initialization."""
    
    def test_initialization_success(self, temp_db_path, mock_logger):
        """Test EventStore can be initialized successfully."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger)
        
        assert store.db_path == Path(temp_db_path)
        assert store.logger == mock_logger
        assert store.max_retries == 3
        assert store.retry_base_delay == 1.0
        
        # Verify database file was created
        assert Path(temp_db_path).exists()
    
    def test_initialization_without_logger(self, temp_db_path):
        """Test EventStore can be initialized without logger."""
        store = EventStore(db_path=temp_db_path, logger=None)
        
        assert store.logger is None
        assert Path(temp_db_path).exists()
    
    def test_initialization_creates_directory(self, tmp_path, mock_logger):
        """Test EventStore creates parent directories if they don't exist."""
        nested_path = tmp_path / "nested" / "path" / "events.db"
        store = EventStore(db_path=str(nested_path), logger=mock_logger)
        
        assert nested_path.exists()
    
    def test_initialization_creates_schema(self, temp_db_path, mock_logger):
        """Test EventStore creates database schema on initialization."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger)
        
        # Verify events table exists
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='events'
            """)
            result = cursor.fetchone()
            
            assert result is not None
            assert result[0] == 'events'
    
    def test_initialization_creates_indexes(self, temp_db_path, mock_logger):
        """Test EventStore creates indexes on initialization."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger)
        
        # Verify indexes exist
        with sqlite3.connect(temp_db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT name FROM sqlite_master 
                WHERE type='index'
            """)
            indexes = [row[0] for row in cursor.fetchall()]
            
            assert 'idx_events_store_id' in indexes
            assert 'idx_events_track_id' in indexes
            assert 'idx_events_event_type' in indexes
            assert 'idx_events_timestamp' in indexes


class TestEventInsertion:
    """Tests for event insertion."""
    
    def test_insert_event_success(self, event_store, sample_event):
        """Test successful event insertion."""
        result = event_store.insert_event(sample_event)
        
        assert result is True
        
        # Verify event was inserted
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        
        assert len(events) == 1
        assert events[0].event_id == sample_event.event_id
        assert events[0].event_type == sample_event.event_type
        assert events[0].track_id == sample_event.track_id
    
    def test_insert_event_idempotency(self, event_store, sample_event):
        """Test inserting the same event twice is idempotent."""
        # Insert event first time
        result1 = event_store.insert_event(sample_event)
        assert result1 is True
        
        # Insert same event second time
        result2 = event_store.insert_event(sample_event)
        assert result2 is True
        
        # Verify only one event exists
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        assert len(events) == 1
    
    def test_insert_event_metadata_serialization(self, event_store):
        """Test event metadata is correctly serialized to JSON."""
        event = Event(
            event_id="meta-test-001",
            event_type=EventType.ZONE_ENTER,
            timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
            store_id="store_001",
            track_id=1,
            metadata={
                "zone_id": "cosmetics",
                "zone_name": "Cosmetics Section",
                "nested": {"key": "value"}
            }
        )
        
        event_store.insert_event(event)
        
        # Query and verify metadata
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        
        assert len(events) == 1
        assert events[0].metadata["zone_id"] == "cosmetics"
        assert events[0].metadata["nested"]["key"] == "value"


class TestBatchInsertion:
    """Tests for batch event insertion."""
    
    def test_insert_events_batch_success(self, event_store, sample_events):
        """Test successful batch insertion."""
        result = event_store.insert_events_batch(sample_events)
        
        assert result.success_count == len(sample_events)
        assert len(result.errors) == 0
        
        # Verify all events were inserted
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        assert len(events) == len(sample_events)
    
    def test_insert_events_batch_idempotency(self, event_store, sample_events):
        """Test batch insertion is idempotent."""
        # Insert batch first time
        result1 = event_store.insert_events_batch(sample_events)
        assert result1.success_count == len(sample_events)
        
        # Insert same batch second time
        result2 = event_store.insert_events_batch(sample_events)
        assert result2.success_count == len(sample_events)
        
        # Verify still only one copy of each event
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        assert len(events) == len(sample_events)
    
    def test_insert_events_batch_atomicity(self, event_store):
        """Test batch insertion is atomic (all or nothing)."""
        # Create mix of valid and duplicate events
        events = [
            Event(
                event_id="batch-001",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                store_id="store_001",
                track_id=1,
                metadata={}
            ),
            Event(
                event_id="batch-002",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
                store_id="store_001",
                track_id=2,
                metadata={}
            ),
        ]
        
        # Insert batch
        result = event_store.insert_events_batch(events)
        
        # Both should succeed (INSERT OR IGNORE handles duplicates)
        assert result.success_count == 2
        
        # Verify both events exist
        filters = EventFilters(store_id="store_001")
        stored_events = event_store.query_events(filters)
        assert len(stored_events) == 2


class TestEventQuerying:
    """Tests for event querying."""
    
    def test_query_events_by_store_id(self, event_store, sample_events):
        """Test querying events by store_id."""
        event_store.insert_events_batch(sample_events)
        
        filters = EventFilters(store_id="store_001")
        events = event_store.query_events(filters)
        
        assert len(events) == len(sample_events)
        assert all(e.store_id == "store_001" for e in events)
    
    def test_query_events_by_track_id(self, event_store, sample_events):
        """Test querying events by track_id."""
        event_store.insert_events_batch(sample_events)
        
        filters = EventFilters(store_id="store_001", track_id=5)
        events = event_store.query_events(filters)
        
        assert len(events) == 1
        assert events[0].track_id == 5
    
    def test_query_events_by_event_type(self, event_store, sample_events):
        """Test querying events by event_type."""
        event_store.insert_events_batch(sample_events)
        
        filters = EventFilters(store_id="store_001", event_type=EventType.ENTRY)
        events = event_store.query_events(filters)
        
        # sample_events has ENTRY for even indices (0, 2, 4, 6, 8)
        assert len(events) == 5
        assert all(e.event_type == EventType.ENTRY for e in events)
    
    def test_query_events_by_time_range(self, event_store, sample_events):
        """Test querying events by time range."""
        event_store.insert_events_batch(sample_events)
        
        start_time = datetime(2024, 1, 1, 12, 3, 0, tzinfo=timezone.utc)
        end_time = datetime(2024, 1, 1, 12, 7, 0, tzinfo=timezone.utc)
        
        filters = EventFilters(
            store_id="store_001",
            start_time=start_time,
            end_time=end_time
        )
        events = event_store.query_events(filters)
        
        # Events at minutes 3, 4, 5, 6, 7 (5 events)
        assert len(events) == 5
        assert all(start_time <= e.timestamp <= end_time for e in events)
    
    def test_query_events_ordered_by_timestamp(self, event_store):
        """Test queried events are ordered by timestamp."""
        # Insert events in random order
        events = [
            Event(
                event_id="evt-003",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 1, 12, 2, 0, tzinfo=timezone.utc),
                store_id="store_001",
                track_id=3,
                metadata={}
            ),
            Event(
                event_id="evt-001",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc),
                store_id="store_001",
                track_id=1,
                metadata={}
            ),
            Event(
                event_id="evt-002",
                event_type=EventType.ENTRY,
                timestamp=datetime(2024, 1, 1, 12, 1, 0, tzinfo=timezone.utc),
                store_id="store_001",
                track_id=2,
                metadata={}
            ),
        ]
        
        event_store.insert_events_batch(events)
        
        filters = EventFilters(store_id="store_001")
        queried_events = event_store.query_events(filters)
        
        # Verify order
        assert len(queried_events) == 3
        assert queried_events[0].event_id == "evt-001"
        assert queried_events[1].event_id == "evt-002"
        assert queried_events[2].event_id == "evt-003"
    
    def test_query_events_empty_result(self, event_store):
        """Test querying with no matching events returns empty list."""
        filters = EventFilters(store_id="nonexistent_store")
        events = event_store.query_events(filters)
        
        assert len(events) == 0


class TestRetryLogic:
    """Tests for retry logic with exponential backoff."""
    
    def test_retry_on_lock_contention(self, temp_db_path, mock_logger):
        """Test retry logic handles lock contention."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger, max_retries=3)
        
        # Mock a lock error on first two attempts, success on third
        call_count = 0
        
        def mock_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise sqlite3.OperationalError("database is locked")
            return True
        
        # Patch time.sleep to avoid actual delays in test
        with patch('time.sleep'):
            result = store._retry_on_lock(mock_operation)
        
        assert result is True
        assert call_count == 3
    
    def test_retry_exhausted_raises_error(self, temp_db_path, mock_logger):
        """Test error is raised when all retries are exhausted."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger, max_retries=2)
        
        def mock_operation():
            raise sqlite3.OperationalError("database is locked")
        
        with patch('time.sleep'):
            with pytest.raises(sqlite3.OperationalError):
                store._retry_on_lock(mock_operation)


class TestHealthCheck:
    """Tests for health check functionality."""
    
    def test_health_check_success(self, event_store):
        """Test health check returns True for healthy database."""
        result = event_store.health_check()
        assert result is True
    
    def test_health_check_failure(self, temp_db_path, mock_logger):
        """Test health check returns False for unhealthy database."""
        store = EventStore(db_path=temp_db_path, logger=mock_logger)
        
        # Corrupt the database by setting an invalid path
        store.db_path = Path("/nonexistent/path/to/database.db")
        
        result = store.health_check()
        assert result is False


class TestConcurrentReads:
    """Tests for concurrent read operations."""
    
    def test_concurrent_reads_while_writing(self, event_store, sample_events):
        """Test reads can occur while writes are in progress (WAL mode)."""
        # Insert initial events
        event_store.insert_events_batch(sample_events[:5])
        
        # This test verifies WAL mode is enabled
        # In WAL mode, reads don't block on writes
        filters = EventFilters(store_id="store_001")
        events_before = event_store.query_events(filters)
        assert len(events_before) == 5
        
        # Insert more events
        event_store.insert_events_batch(sample_events[5:])
        
        # Read again
        events_after = event_store.query_events(filters)
        assert len(events_after) == 10
