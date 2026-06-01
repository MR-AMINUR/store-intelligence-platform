"""Unit tests for core data models."""

from datetime import datetime

import numpy as np
import pytest

from src.models import (
    BoundingBox,
    Detection,
    Event,
    EventType,
    Frame,
    Point,
    Track,
    TrackState,
    Zone,
    ZoneType,
)


class TestFrame:
    """Tests for Frame dataclass."""
    
    def test_frame_initialization(self):
        """Test Frame can be initialized with all required fields."""
        image = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = Frame(
            frame_number=42,
            timestamp=1.4,
            image=image,
            resolution=(640, 480)
        )
        
        assert frame.frame_number == 42
        assert frame.timestamp == 1.4
        assert frame.image.shape == (480, 640, 3)
        assert frame.resolution == (640, 480)


class TestBoundingBox:
    """Tests for BoundingBox dataclass."""
    
    def test_bounding_box_initialization(self):
        """Test BoundingBox can be initialized with coordinates."""
        bbox = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        
        assert bbox.x == 100.0
        assert bbox.y == 200.0
        assert bbox.width == 50.0
        assert bbox.height == 80.0


class TestDetection:
    """Tests for Detection dataclass."""
    
    def test_detection_initialization(self):
        """Test Detection can be initialized with bbox and confidence."""
        bbox = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        detection = Detection(bbox=bbox, confidence=0.85, class_id=0)
        
        assert detection.bbox == bbox
        assert detection.confidence == 0.85
        assert detection.class_id == 0


class TestTrack:
    """Tests for Track dataclass."""
    
    def test_track_initialization(self):
        """Test Track can be initialized with all required fields."""
        bbox = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        track = Track(
            track_id=1,
            bbox=bbox,
            frame_number=42,
            age=0,
            state=TrackState.ACTIVE
        )
        
        assert track.track_id == 1
        assert track.bbox == bbox
        assert track.frame_number == 42
        assert track.age == 0
        assert track.state == TrackState.ACTIVE
    
    def test_track_state_enum(self):
        """Test TrackState enum values."""
        assert TrackState.ACTIVE.value == "active"
        assert TrackState.LOST.value == "lost"
        assert TrackState.REMOVED.value == "removed"


class TestZone:
    """Tests for Zone dataclass."""
    
    def test_zone_initialization(self):
        """Test Zone can be initialized with polygon and type."""
        polygon = [
            Point(x=0.0, y=0.0),
            Point(x=100.0, y=0.0),
            Point(x=100.0, y=100.0),
            Point(x=0.0, y=100.0),
        ]
        zone = Zone(
            zone_id="zone_001",
            zone_name="Cosmetics",
            polygon=polygon,
            zone_type=ZoneType.GENERAL
        )
        
        assert zone.zone_id == "zone_001"
        assert zone.zone_name == "Cosmetics"
        assert len(zone.polygon) == 4
        assert zone.zone_type == ZoneType.GENERAL
    
    def test_zone_type_enum(self):
        """Test ZoneType enum values."""
        assert ZoneType.GENERAL.value == "general"
        assert ZoneType.BILLING_QUEUE.value == "billing_queue"


class TestEvent:
    """Tests for Event dataclass."""
    
    def test_event_initialization(self):
        """Test Event can be initialized with all required fields."""
        event = Event(
            event_id="evt_123",
            event_type=EventType.ENTRY,
            timestamp=datetime(2024, 1, 15, 10, 30, 0),
            store_id="store_001",
            track_id=42,
            metadata={}
        )
        
        assert event.event_id == "evt_123"
        assert event.event_type == EventType.ENTRY
        assert event.timestamp == datetime(2024, 1, 15, 10, 30, 0)
        assert event.store_id == "store_001"
        assert event.track_id == 42
        assert event.metadata == {}
    
    def test_event_with_metadata(self):
        """Test Event can store event-specific metadata."""
        metadata = {
            "zone_id": "zone_001",
            "zone_name": "Cosmetics",
            "dwell_duration_seconds": 15.5
        }
        event = Event(
            event_id="evt_456",
            event_type=EventType.ZONE_DWELL,
            timestamp=datetime(2024, 1, 15, 10, 30, 15),
            store_id="store_001",
            track_id=42,
            metadata=metadata
        )
        
        assert event.metadata["zone_id"] == "zone_001"
        assert event.metadata["zone_name"] == "Cosmetics"
        assert event.metadata["dwell_duration_seconds"] == 15.5
    
    def test_event_type_enum(self):
        """Test EventType enum values."""
        assert EventType.ENTRY.value == "ENTRY"
        assert EventType.EXIT.value == "EXIT"
        assert EventType.ZONE_ENTER.value == "ZONE_ENTER"
        assert EventType.ZONE_EXIT.value == "ZONE_EXIT"
        assert EventType.ZONE_DWELL.value == "ZONE_DWELL"
        assert EventType.BILLING_QUEUE_JOIN.value == "BILLING_QUEUE_JOIN"
        assert EventType.BILLING_QUEUE_ABANDON.value == "BILLING_QUEUE_ABANDON"
        assert EventType.REENTRY.value == "REENTRY"


class TestPoint:
    """Tests for Point dataclass."""
    
    def test_point_initialization(self):
        """Test Point can be initialized with coordinates."""
        point = Point(x=100.5, y=200.7)
        
        assert point.x == 100.5
        assert point.y == 200.7



# ============================================================================
# Tests for Pydantic API Models
# ============================================================================

from src.models import (
    IngestResponse,
    StoreMetrics,
    TimeRange,
    FunnelStage,
    ConversionFunnel,
    GridDimensions,
    Heatmap,
    AnomalyMetrics,
    Anomaly,
    HealthCheck,
    HealthStatus,
)


class TestIngestResponse:
    """Tests for IngestResponse Pydantic model."""
    
    def test_ingest_response_initialization(self):
        """Test IngestResponse can be initialized with required fields."""
        response = IngestResponse(
            success=True,
            events_processed=10,
            errors=[]
        )
        
        assert response.success is True
        assert response.events_processed == 10
        assert response.errors == []
    
    def test_ingest_response_with_errors(self):
        """Test IngestResponse can store error messages."""
        response = IngestResponse(
            success=False,
            events_processed=5,
            errors=["Invalid event_id", "Missing timestamp"]
        )
        
        assert response.success is False
        assert response.events_processed == 5
        assert len(response.errors) == 2
    
    def test_ingest_response_json_serialization(self):
        """Test IngestResponse can be serialized to JSON."""
        response = IngestResponse(
            success=True,
            events_processed=10,
            errors=[]
        )
        
        json_data = response.model_dump()
        assert json_data["success"] is True
        assert json_data["events_processed"] == 10
        assert json_data["errors"] == []
    
    def test_ingest_response_validation_negative_events(self):
        """Test IngestResponse validates events_processed >= 0."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            IngestResponse(
                success=True,
                events_processed=-1,
                errors=[]
            )


class TestStoreMetrics:
    """Tests for StoreMetrics Pydantic model."""
    
    def test_store_metrics_initialization(self):
        """Test StoreMetrics can be initialized with required fields."""
        metrics = StoreMetrics(
            store_id="store_001",
            total_entries=100,
            total_exits=95,
            current_occupancy=5,
            average_visit_duration_seconds=1800.5
        )
        
        assert metrics.store_id == "store_001"
        assert metrics.total_entries == 100
        assert metrics.total_exits == 95
        assert metrics.current_occupancy == 5
        assert metrics.average_visit_duration_seconds == 1800.5
    
    def test_store_metrics_with_time_range(self):
        """Test StoreMetrics can include time range."""
        time_range = TimeRange(
            start=datetime(2024, 1, 15, 0, 0, 0),
            end=datetime(2024, 1, 15, 23, 59, 59)
        )
        metrics = StoreMetrics(
            store_id="store_001",
            total_entries=100,
            total_exits=95,
            current_occupancy=5,
            average_visit_duration_seconds=1800.5,
            time_range=time_range
        )
        
        assert metrics.time_range is not None
        assert metrics.time_range.start == datetime(2024, 1, 15, 0, 0, 0)
    
    def test_store_metrics_json_serialization(self):
        """Test StoreMetrics can be serialized to JSON."""
        metrics = StoreMetrics(
            store_id="store_001",
            total_entries=100,
            total_exits=95,
            current_occupancy=5,
            average_visit_duration_seconds=1800.5
        )
        
        json_data = metrics.model_dump()
        assert json_data["store_id"] == "store_001"
        assert json_data["total_entries"] == 100


class TestConversionFunnel:
    """Tests for ConversionFunnel Pydantic model."""
    
    def test_conversion_funnel_initialization(self):
        """Test ConversionFunnel can be initialized with stages."""
        stages = [
            FunnelStage(stage="entries", count=1000, conversion_rate=1.0),
            FunnelStage(stage="zone_visits", count=800, conversion_rate=0.8),
            FunnelStage(stage="billing_queue_joins", count=600, conversion_rate=0.75),
            FunnelStage(stage="completed_purchases", count=550, conversion_rate=0.917),
        ]
        funnel = ConversionFunnel(
            store_id="store_001",
            stages=stages
        )
        
        assert funnel.store_id == "store_001"
        assert len(funnel.stages) == 4
        assert funnel.stages[0].stage == "entries"
        assert funnel.stages[0].count == 1000
    
    def test_conversion_funnel_with_zone_filter(self):
        """Test ConversionFunnel can include zone filter."""
        stages = [
            FunnelStage(stage="entries", count=500, conversion_rate=1.0),
        ]
        funnel = ConversionFunnel(
            store_id="store_001",
            stages=stages,
            zone_id="zone_cosmetics"
        )
        
        assert funnel.zone_id == "zone_cosmetics"
    
    def test_funnel_stage_validation(self):
        """Test FunnelStage validates conversion_rate in [0, 1]."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            FunnelStage(stage="entries", count=100, conversion_rate=1.5)


class TestHeatmap:
    """Tests for Heatmap Pydantic model."""
    
    def test_heatmap_initialization(self):
        """Test Heatmap can be initialized with grid and density."""
        grid = GridDimensions(width=20, height=15)
        density = [[0.1, 0.3, 0.5], [0.2, 0.4, 0.6]]
        
        heatmap = Heatmap(
            store_id="store_001",
            resolution=50,
            grid=grid,
            density=density
        )
        
        assert heatmap.store_id == "store_001"
        assert heatmap.resolution == 50
        assert heatmap.grid.width == 20
        assert heatmap.grid.height == 15
        assert len(heatmap.density) == 2
    
    def test_heatmap_json_serialization(self):
        """Test Heatmap can be serialized to JSON."""
        grid = GridDimensions(width=20, height=15)
        density = [[0.1, 0.3], [0.2, 0.4]]
        
        heatmap = Heatmap(
            store_id="store_001",
            resolution=50,
            grid=grid,
            density=density
        )
        
        json_data = heatmap.model_dump()
        assert json_data["store_id"] == "store_001"
        assert json_data["grid"]["width"] == 20


class TestAnomaly:
    """Tests for Anomaly Pydantic model."""
    
    def test_anomaly_initialization(self):
        """Test Anomaly can be initialized with metrics."""
        metrics = AnomalyMetrics(
            baseline=50.0,
            observed=125.0,
            threshold=100.0
        )
        anomaly = Anomaly(
            type="sudden_crowd_surge",
            severity="high",
            timestamp=datetime(2024, 1, 15, 14, 30, 0),
            description="Occupancy increased by 150% in 10 minutes",
            metrics=metrics
        )
        
        assert anomaly.type == "sudden_crowd_surge"
        assert anomaly.severity == "high"
        assert anomaly.metrics.baseline == 50.0
        assert anomaly.metrics.observed == 125.0
    
    def test_anomaly_severity_validation(self):
        """Test Anomaly validates severity is low/medium/high."""
        metrics = AnomalyMetrics(baseline=50.0, observed=125.0, threshold=100.0)
        
        with pytest.raises(Exception):  # Pydantic ValidationError
            Anomaly(
                type="test",
                severity="invalid",
                timestamp=datetime(2024, 1, 15, 14, 30, 0),
                description="Test",
                metrics=metrics
            )


class TestHealthStatus:
    """Tests for HealthStatus Pydantic model."""
    
    def test_health_status_initialization(self):
        """Test HealthStatus can be initialized with checks."""
        health = HealthStatus(
            status="healthy",
            checks={"database": "ok", "api": "ok"},
            response_time_ms=45.2,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        assert health.status == "healthy"
        assert health.checks["database"] == "ok"
        assert health.response_time_ms == 45.2
    
    def test_health_status_validation(self):
        """Test HealthStatus validates status is healthy/degraded/unhealthy."""
        with pytest.raises(Exception):  # Pydantic ValidationError
            HealthStatus(
                status="invalid",
                checks={},
                response_time_ms=45.2,
                timestamp=datetime(2024, 1, 15, 10, 30, 0)
            )
    
    def test_health_status_json_serialization(self):
        """Test HealthStatus can be serialized to JSON."""
        health = HealthStatus(
            status="healthy",
            checks={"database": "ok"},
            response_time_ms=45.2,
            timestamp=datetime(2024, 1, 15, 10, 30, 0)
        )
        
        json_data = health.model_dump()
        assert json_data["status"] == "healthy"
        assert json_data["checks"]["database"] == "ok"
