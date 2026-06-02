"""Unit tests for EventStore analytics methods."""

import pytest
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

from src.event_store import EventStore
from src.models import Event, EventType


@pytest.fixture
def temp_db_path():
    """Create a temporary database path for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield str(Path(tmp_dir) / "test_analytics.db")


@pytest.fixture
def store_with_data(temp_db_path):
    """Create an EventStore with sample data for analytics."""
    store = EventStore(db_path=temp_db_path, logger=None)
    
    # Create events for 5 customers with complete journeys
    base_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
    
    events = []
    
    # Customer 1: Complete journey (entry -> zone -> queue -> purchase)
    events.extend([
        Event("evt-001", EventType.ENTRY, base_time, "store_001", 1, {}),
        Event("evt-002", EventType.ZONE_ENTER, base_time + timedelta(minutes=5), "store_001", 1, {"zone_id": "cosmetics", "zone_name": "Cosmetics"}),
        Event("evt-003", EventType.ZONE_DWELL, base_time + timedelta(minutes=10), "store_001", 1, {"zone_id": "cosmetics", "zone_name": "Cosmetics", "dwell_duration_seconds": 300.0}),
        Event("evt-004", EventType.ZONE_EXIT, base_time + timedelta(minutes=15), "store_001", 1, {"zone_id": "cosmetics", "zone_name": "Cosmetics", "zone_duration_seconds": 600.0}),
        Event("evt-005", EventType.BILLING_QUEUE_JOIN, base_time + timedelta(minutes=20), "store_001", 1, {"queue_position": 1}),
        Event("evt-006", EventType.EXIT, base_time + timedelta(minutes=30), "store_001", 1, {}),
    ])
    
    # Customer 2: Abandoned queue
    events.extend([
        Event("evt-007", EventType.ENTRY, base_time + timedelta(minutes=2), "store_001", 2, {}),
        Event("evt-008", EventType.ZONE_ENTER, base_time + timedelta(minutes=7), "store_001", 2, {"zone_id": "skincare", "zone_name": "Skincare"}),
        Event("evt-009", EventType.BILLING_QUEUE_JOIN, base_time + timedelta(minutes=15), "store_001", 2, {"queue_position": 2}),
        Event("evt-010", EventType.BILLING_QUEUE_ABANDON, base_time + timedelta(minutes=25), "store_001", 2, {"queue_wait_time_seconds": 600.0, "high_wait_time": True}),
        Event("evt-011", EventType.EXIT, base_time + timedelta(minutes=27), "store_001", 2, {}),
    ])
    
    # Customer 3: Just browsed, no queue
    events.extend([
        Event("evt-012", EventType.ENTRY, base_time + timedelta(minutes=5), "store_001", 3, {}),
        Event("evt-013", EventType.ZONE_ENTER, base_time + timedelta(minutes=8), "store_001", 3, {"zone_id": "cosmetics", "zone_name": "Cosmetics"}),
        Event("evt-014", EventType.ZONE_EXIT, base_time + timedelta(minutes=12), "store_001", 3, {"zone_id": "cosmetics", "zone_name": "Cosmetics", "zone_duration_seconds": 240.0}),
        Event("evt-015", EventType.EXIT, base_time + timedelta(minutes=15), "store_001", 3, {}),
    ])
    
    # Customer 4: Complete journey (entry -> zone -> queue -> purchase)
    events.extend([
        Event("evt-016", EventType.ENTRY, base_time + timedelta(minutes=10), "store_001", 4, {}),
        Event("evt-017", EventType.ZONE_ENTER, base_time + timedelta(minutes=15), "store_001", 4, {"zone_id": "cosmetics", "zone_name": "Cosmetics"}),
        Event("evt-018", EventType.BILLING_QUEUE_JOIN, base_time + timedelta(minutes=25), "store_001", 4, {"queue_position": 1}),
        Event("evt-019", EventType.EXIT, base_time + timedelta(minutes=35), "store_001", 4, {}),
    ])
    
    # Customer 5: Still in store (no exit)
    events.extend([
        Event("evt-020", EventType.ENTRY, base_time + timedelta(minutes=40), "store_001", 5, {}),
        Event("evt-021", EventType.ZONE_ENTER, base_time + timedelta(minutes=45), "store_001", 5, {"zone_id": "cosmetics", "zone_name": "Cosmetics"}),
    ])
    
    store.insert_events_batch(events)
    return store


class TestStoreMetrics:
    """Tests for get_store_metrics()."""
    
    def test_basic_metrics_calculation(self, store_with_data):
        """Test basic metrics calculation."""
        metrics = store_with_data.get_store_metrics("store_001")
        
        assert metrics.store_id == "store_001"
        assert metrics.total_entries == 5
        assert metrics.total_exits == 4
        assert metrics.current_occupancy == 1  # 5 entries - 4 exits
    
    def test_average_visit_duration(self, store_with_data):
        """Test average visit duration calculation."""
        metrics = store_with_data.get_store_metrics("store_001")
        
        # Should have calculated average for 4 complete visits
        assert metrics.average_visit_duration_seconds > 0
        # Durations: 30min, 25min, 10min, 25min = 1800, 1500, 600, 1500 seconds
        # Average: (1800 + 1500 + 600 + 1500) / 4 = 1350 seconds
        assert abs(metrics.average_visit_duration_seconds - 1350.0) < 10
    
    def test_metrics_with_time_range(self, store_with_data):
        """Test metrics calculation with time range filter."""
        base_time = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
        start_time = base_time + timedelta(minutes=5)
        end_time = base_time + timedelta(minutes=20)
        
        metrics = store_with_data.get_store_metrics(
            "store_001",
            start_time=start_time,
            end_time=end_time
        )
        
        # Should only count events in the time range
        assert metrics.total_entries < 5  # Not all entries in range
        assert metrics.time_range is not None
        assert metrics.time_range.start == start_time
        assert metrics.time_range.end == end_time
    
    def test_metrics_empty_store(self, temp_db_path):
        """Test metrics for store with no data."""
        store = EventStore(db_path=temp_db_path, logger=None)
        metrics = store.get_store_metrics("nonexistent_store")
        
        assert metrics.total_entries == 0
        assert metrics.total_exits == 0
        assert metrics.current_occupancy == 0
        assert metrics.average_visit_duration_seconds == 0.0


class TestConversionFunnel:
    """Tests for get_conversion_funnel()."""
    
    def test_basic_funnel_calculation(self, store_with_data):
        """Test basic conversion funnel calculation."""
        funnel = store_with_data.get_conversion_funnel("store_001")
        
        assert funnel.store_id == "store_001"
        assert len(funnel.stages) == 4
        
        # Check stage names and counts
        stage_dict = {stage.stage: stage for stage in funnel.stages}
        
        assert "entries" in stage_dict
        assert stage_dict["entries"].count == 5
        assert stage_dict["entries"].conversion_rate == 1.0
        
        assert "zone_visits" in stage_dict
        assert stage_dict["zone_visits"].count == 5  # All visited zones
        
        assert "billing_queue_joins" in stage_dict
        assert stage_dict["billing_queue_joins"].count == 3  # 3 joined queue
        
        assert "completed_purchases" in stage_dict
        assert stage_dict["completed_purchases"].count == 2  # 2 completed (didn't abandon)
    
    def test_funnel_conversion_rates(self, store_with_data):
        """Test conversion rate calculations."""
        funnel = store_with_data.get_conversion_funnel("store_001")
        
        stage_dict = {stage.stage: stage for stage in funnel.stages}
        
        # zone_visits / entries = 5 / 5 = 1.0
        assert abs(stage_dict["zone_visits"].conversion_rate - 1.0) < 0.01
        
        # billing_queue_joins / zone_visits = 3 / 5 = 0.6
        assert abs(stage_dict["billing_queue_joins"].conversion_rate - 0.6) < 0.01
        
        # completed_purchases / billing_queue_joins = 2 / 3 ≈ 0.667
        assert abs(stage_dict["completed_purchases"].conversion_rate - 0.667) < 0.01
    
    def test_funnel_with_zone_filter(self, store_with_data):
        """Test funnel with zone_id filter."""
        funnel = store_with_data.get_conversion_funnel("store_001", zone_id="cosmetics")
        
        assert funnel.zone_id == "cosmetics"
        
        stage_dict = {stage.stage: stage for stage in funnel.stages}
        
        # Should filter to only customers who visited cosmetics zone
        assert stage_dict["zone_visits"].count == 4  # 4 visited cosmetics
    
    def test_funnel_empty_store(self, temp_db_path):
        """Test funnel for store with no data."""
        store = EventStore(db_path=temp_db_path, logger=None)
        funnel = store.get_conversion_funnel("nonexistent_store")
        
        assert all(stage.count == 0 for stage in funnel.stages)
        assert all(stage.conversion_rate >= 0 for stage in funnel.stages)


class TestHeatmap:
    """Tests for get_heatmap()."""
    
    def test_basic_heatmap_generation(self, store_with_data):
        """Test basic heatmap generation."""
        heatmap = store_with_data.get_heatmap("store_001", resolution=50)
        
        assert heatmap.store_id == "store_001"
        assert heatmap.resolution == 50
        assert heatmap.grid.width > 0
        assert heatmap.grid.height > 0
        assert len(heatmap.density) == heatmap.grid.height
        assert all(len(row) == heatmap.grid.width for row in heatmap.density)
    
    def test_heatmap_density_normalization(self, store_with_data):
        """Test heatmap density values are normalized to [0, 1]."""
        heatmap = store_with_data.get_heatmap("store_001")
        
        # All values should be in range [0, 1]
        for row in heatmap.density:
            for value in row:
                assert 0.0 <= value <= 1.0
    
    def test_heatmap_empty_store(self, temp_db_path):
        """Test heatmap for store with no data."""
        store = EventStore(db_path=temp_db_path, logger=None)
        heatmap = store.get_heatmap("nonexistent_store")
        
        assert heatmap.grid.width > 0
        assert heatmap.grid.height > 0
        # Should return empty/zero density grid
        assert all(all(v == 0.0 for v in row) for row in heatmap.density)
    
    def test_heatmap_custom_resolution(self, store_with_data):
        """Test heatmap with custom resolution."""
        heatmap_50 = store_with_data.get_heatmap("store_001", resolution=50)
        heatmap_100 = store_with_data.get_heatmap("store_001", resolution=100)
        
        # Larger resolution should result in smaller grid
        assert heatmap_100.grid.width <= heatmap_50.grid.width
        assert heatmap_100.grid.height <= heatmap_50.grid.height


class TestAnomalyDetection:
    """Tests for detect_anomalies()."""
    
    def test_anomaly_detection_basic(self, store_with_data):
        """Test basic anomaly detection."""
        anomalies = store_with_data.detect_anomalies("store_001", time_window=24)
        
        # Should return a list (may be empty if no anomalies)
        assert isinstance(anomalies, list)
    
    def test_detect_high_queue_abandonment(self, temp_db_path):
        """Test detection of high queue abandonment."""
        store = EventStore(db_path=temp_db_path, logger=None)
        
        base_time = datetime.now(timezone.utc) - timedelta(hours=1)
        
        # Create historical data (low abandonment)
        historical_time = base_time - timedelta(days=3)
        historical_events = []
        for i in range(10):
            historical_events.extend([
                Event(f"hist-join-{i}", EventType.BILLING_QUEUE_JOIN, historical_time + timedelta(minutes=i*5), "store_001", 100+i, {"queue_position": i+1}),
                # Only 1 abandonment out of 10
            ])
        if historical_events:
            historical_events.append(
                Event("hist-abandon-1", EventType.BILLING_QUEUE_ABANDON, historical_time + timedelta(minutes=25), "store_001", 100, {"queue_wait_time_seconds": 300.0, "high_wait_time": False})
            )
        
        store.insert_events_batch(historical_events)
        
        # Create recent data (high abandonment)
        recent_events = []
        for i in range(10):
            recent_events.extend([
                Event(f"recent-join-{i}", EventType.BILLING_QUEUE_JOIN, base_time + timedelta(minutes=i*5), "store_001", 200+i, {"queue_position": i+1}),
                Event(f"recent-abandon-{i}", EventType.BILLING_QUEUE_ABANDON, base_time + timedelta(minutes=i*5+3), "store_001", 200+i, {"queue_wait_time_seconds": 180.0, "high_wait_time": False}),
            ])
        
        store.insert_events_batch(recent_events)
        
        anomalies = store.detect_anomalies("store_001", time_window=24)
        
        # Should detect high abandonment
        abandonment_anomalies = [a for a in anomalies if a.type == "high_queue_abandonment"]
        assert len(abandonment_anomalies) > 0
        assert abandonment_anomalies[0].severity in ["medium", "high"]
    
    def test_detect_off_hours_activity(self, temp_db_path):
        """Test detection of off-hours activity."""
        store = EventStore(db_path=temp_db_path, logger=None)
        
        # Create events at 2 AM (off-hours)
        off_hours_time = datetime.now(timezone.utc).replace(hour=2, minute=0, second=0)
        
        off_hours_events = [
            Event(f"off-{i}", EventType.ENTRY, off_hours_time + timedelta(minutes=i), "store_001", 300+i, {})
            for i in range(10)
        ]
        
        store.insert_events_batch(off_hours_events)
        
        anomalies = store.detect_anomalies("store_001", time_window=24)
        
        # Should detect off-hours activity
        off_hours_anomalies = [a for a in anomalies if a.type == "off_hours_activity"]
        assert len(off_hours_anomalies) > 0
        assert off_hours_anomalies[0].metrics.observed >= 10
    
    def test_anomaly_object_structure(self, store_with_data):
        """Test anomaly objects have correct structure."""
        anomalies = store_with_data.detect_anomalies("store_001", time_window=24)
        
        for anomaly in anomalies:
            assert hasattr(anomaly, 'type')
            assert hasattr(anomaly, 'severity')
            assert anomaly.severity in ["low", "medium", "high"]
            assert hasattr(anomaly, 'timestamp')
            assert hasattr(anomaly, 'description')
            assert hasattr(anomaly, 'metrics')
            assert hasattr(anomaly.metrics, 'baseline')
            assert hasattr(anomaly.metrics, 'observed')
            assert hasattr(anomaly.metrics, 'threshold')
    
    def test_anomaly_detection_empty_store(self, temp_db_path):
        """Test anomaly detection for store with no data."""
        store = EventStore(db_path=temp_db_path, logger=None)
        anomalies = store.detect_anomalies("nonexistent_store", time_window=24)
        
        # Should return empty list for empty store
        assert isinstance(anomalies, list)
        assert len(anomalies) == 0
