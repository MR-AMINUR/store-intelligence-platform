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
