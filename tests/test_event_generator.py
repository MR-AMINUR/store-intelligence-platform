"""Unit tests for EventGenerator."""

import json
import pytest
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

from src.event_generator import EventGenerator
from src.logger import Logger
from src.models import BoundingBox, Event, EventType, Point, Track, TrackState, Zone, ZoneType


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
def sample_zones():
    """Create sample zones for testing."""
    return [
        Zone(
            zone_id="cosmetics",
            zone_name="Cosmetics Section",
            polygon=[
                Point(x=100, y=100),
                Point(x=300, y=100),
                Point(x=300, y=300),
                Point(x=100, y=300)
            ],
            zone_type=ZoneType.GENERAL
        ),
        Zone(
            zone_id="billing_queue",
            zone_name="Billing Queue",
            polygon=[
                Point(x=400, y=400),
                Point(x=600, y=400),
                Point(x=600, y=600),
                Point(x=400, y=600)
            ],
            zone_type=ZoneType.BILLING_QUEUE
        )
    ]


@pytest.fixture
def event_generator(sample_zones, mock_logger):
    """Create an EventGenerator instance for testing."""
    return EventGenerator(
        store_id="store_001",
        zones=sample_zones,
        logger=mock_logger,
        fps=30
    )


@pytest.fixture
def sample_track():
    """Create a sample track for testing."""
    return Track(
        track_id=1,
        bbox=BoundingBox(x=150.0, y=150.0, width=50.0, height=80.0),
        frame_number=10,
        age=0,
        state=TrackState.ACTIVE
    )


class TestEventGeneratorInitialization:
    """Tests for EventGenerator initialization."""
    
    def test_initialization_success(self, sample_zones, mock_logger):
        """Test EventGenerator can be initialized successfully."""
        generator = EventGenerator(
            store_id="store_001",
            zones=sample_zones,
            logger=mock_logger,
            fps=30
        )
        
        assert generator.store_id == "store_001"
        assert len(generator.zones) == 2
        assert generator.fps == 30
        assert len(generator.track_state) == 0
        assert len(generator.zone_state) == 0
        assert len(generator.exit_history) == 0
    
    def test_initialization_with_invalid_fps(self, sample_zones, mock_logger):
        """Test EventGenerator raises error with invalid fps."""
        with pytest.raises(ValueError, match="fps must be positive"):
            EventGenerator(
                store_id="store_001",
                zones=sample_zones,
                logger=mock_logger,
                fps=0
            )

    
    def test_initialization_without_logger(self, sample_zones):
        """Test EventGenerator can be initialized without logger."""
        generator = EventGenerator(
            store_id="store_001",
            zones=sample_zones,
            logger=None,
            fps=30
        )
        
        assert generator.logger is None
    
    def test_from_zone_config(self, mock_logger, tmp_path):
        """Test creating EventGenerator from zone config file."""
        # Create temporary zone config
        config_data = {
            "zones": [
                {
                    "zone_id": "test_zone",
                    "zone_name": "Test Zone",
                    "zone_type": "GENERAL",
                    "polygon": [
                        {"x": 0, "y": 0},
                        {"x": 100, "y": 0},
                        {"x": 100, "y": 100},
                        {"x": 0, "y": 100}
                    ]
                }
            ]
        }
        config_path = tmp_path / "zones.json"
        with open(config_path, 'w') as f:
            json.dump(config_data, f)
        
        generator = EventGenerator.from_zone_config(
            store_id="store_001",
            zone_config_path=str(config_path),
            logger=mock_logger,
            fps=30
        )
        
        assert generator.store_id == "store_001"
        assert len(generator.zones) == 1
        assert generator.zones[0].zone_id == "test_zone"

    
    def test_from_zone_config_file_not_found(self, mock_logger):
        """Test error when zone config file doesn't exist."""
        with pytest.raises(FileNotFoundError):
            EventGenerator.from_zone_config(
                store_id="store_001",
                zone_config_path="/nonexistent/path.json",
                logger=mock_logger
            )
    
    def test_from_zone_config_invalid_json(self, mock_logger, tmp_path):
        """Test error with invalid zone config."""
        config_path = tmp_path / "invalid_zones.json"
        with open(config_path, 'w') as f:
            json.dump({"invalid": "data"}, f)
        
        with pytest.raises(ValueError, match="must contain 'zones' key"):
            EventGenerator.from_zone_config(
                store_id="store_001",
                zone_config_path=str(config_path),
                logger=mock_logger
            )


class TestEntryExitDetection:
    """Tests for entry and exit event detection."""
    
    def test_entry_event_generated_for_new_track(self, event_generator, sample_track):
        """Test ENTRY event is generated when track first appears."""
        events = event_generator.process_tracks([sample_track], frame_number=10)
        
        entry_events = [e for e in events if e.event_type == EventType.ENTRY]
        assert len(entry_events) == 1
        assert entry_events[0].track_id == sample_track.track_id
        assert entry_events[0].store_id == "store_001"
        assert entry_events[0].event_id is not None

    
    def test_exit_event_generated_after_max_age(self, event_generator, sample_track):
        """Test EXIT event is generated when track is absent > max_age frames."""
        # First, track appears
        event_generator.process_tracks([sample_track], frame_number=10)
        
        # Track disappears for more than 30 frames
        events = event_generator.process_tracks([], frame_number=50)
        
        exit_events = [e for e in events if e.event_type == EventType.EXIT]
        assert len(exit_events) == 1
        assert exit_events[0].track_id == sample_track.track_id
    
    def test_no_exit_event_within_max_age(self, event_generator, sample_track):
        """Test no EXIT event when track is absent < max_age frames."""
        # Track appears
        event_generator.process_tracks([sample_track], frame_number=10)
        
        # Track disappears for less than 30 frames
        events = event_generator.process_tracks([], frame_number=35)
        
        exit_events = [e for e in events if e.event_type == EventType.EXIT]
        assert len(exit_events) == 0
    
    def test_exit_event_exactly_at_max_age(self, event_generator, sample_track):
        """Test EXIT event at exactly max_age + 1 frames."""
        # Track appears
        event_generator.process_tracks([sample_track], frame_number=10)
        
        # Track disappears for exactly 31 frames (max_age + 1)
        events = event_generator.process_tracks([], frame_number=41)
        
        exit_events = [e for e in events if e.event_type == EventType.EXIT]
        assert len(exit_events) == 1

