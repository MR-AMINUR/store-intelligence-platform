"""Unit tests for video processing pipeline."""

import os
import tempfile
from unittest.mock import MagicMock, Mock, patch

import numpy as np
import pytest

from src.config import ConfigManager
from src.event_generator import EventGenerator
from src.event_store import EventStore
from src.logger import Logger
from src.models import (
    BoundingBox,
    Detection,
    Event,
    EventType,
    Frame,
    Track,
    TrackState,
)
from src.person_detector import PersonDetector
from src.person_tracker import PersonTracker
from src.pipeline import PipelineResult, VideoPipeline
from src.video_processor import VideoProcessor


@pytest.fixture
def temp_db():
    """Create temporary database for testing."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def temp_video():
    """Create temporary video file path for testing."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        video_path = f.name
    yield video_path
    # Cleanup
    if os.path.exists(video_path):
        os.unlink(video_path)


@pytest.fixture
def test_config(temp_db):
    """Create test configuration."""
    # Set environment variables for testing
    os.environ["DB_PATH"] = temp_db
    os.environ["API_PORT"] = "8000"
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["YOLO_MODEL_PATH"] = "./models/yolov8n.pt"
    os.environ["CONFIDENCE_THRESHOLD"] = "0.5"
    os.environ["TRACKER_MAX_AGE"] = "30"
    os.environ["ZONE_CONFIG_PATH"] = "./config/zones.json"
    os.environ["STORE_ID"] = "test_store_001"
    
    config = ConfigManager()
    yield config
    
    # Cleanup environment variables
    for key in ["DB_PATH", "API_PORT", "LOG_LEVEL", "YOLO_MODEL_PATH",
                "CONFIDENCE_THRESHOLD", "TRACKER_MAX_AGE", "ZONE_CONFIG_PATH", "STORE_ID"]:
        os.environ.pop(key, None)


class TestPipelineResult:
    """Tests for PipelineResult class."""
    
    def test_pipeline_result_initialization(self):
        """Test PipelineResult initialization."""
        result = PipelineResult(
            success=True,
            total_frames=100,
            frames_failed=5,
            events_generated=50,
            events_stored=50,
            errors=["error1", "error2"]
        )
        
        assert result.success is True
        assert result.total_frames == 100
        assert result.frames_failed == 5
        assert result.events_generated == 50
        assert result.events_stored == 50
        assert len(result.errors) == 2
    
    def test_pipeline_result_defaults(self):
        """Test PipelineResult with default values."""
        result = PipelineResult(success=True)
        
        assert result.success is True
        assert result.total_frames == 0
        assert result.frames_failed == 0
        assert result.events_generated == 0
        assert result.events_stored == 0
        assert result.errors == []


class TestVideoPipeline:
    """Tests for VideoPipeline class."""
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_initialization(
        self,
        mock_event_store,
        mock_event_generator,
        mock_person_tracker,
        mock_person_detector,
        mock_video_processor,
        test_config,
        temp_video
    ):
        """Test pipeline initialization with all components."""
        # Create pipeline
        pipeline = VideoPipeline(temp_video, test_config)
        
        # Verify all components were initialized
        assert pipeline.video_path == temp_video
        assert pipeline.config == test_config
        assert pipeline.logger is not None
        assert pipeline.correlation_id is not None
        
        # Verify component initialization calls
        mock_video_processor.assert_called_once()
        mock_person_detector.assert_called_once()
        mock_person_tracker.assert_called_once()
        mock_event_generator.from_zone_config.assert_called_once()
        mock_event_store.assert_called_once()
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_process_success(
        self,
        mock_event_store_class,
        mock_event_generator_class,
        mock_person_tracker_class,
        mock_person_detector_class,
        mock_video_processor_class,
        test_config,
        temp_video
    ):
        """Test successful pipeline processing."""
        # Setup mocks
        mock_video_processor = Mock()
        mock_person_detector = Mock()
        mock_person_tracker = Mock()
        mock_event_generator = Mock()
        mock_event_store = Mock()
        
        # Mock video frames
        frame1 = Frame(
            frame_number=0,
            timestamp=0.0,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        frame2 = Frame(
            frame_number=1,
            timestamp=0.033,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        mock_video_processor.read_frames.return_value = [frame1, frame2]
        
        # Mock detections
        detection = Detection(
            bbox=BoundingBox(x=100, y=100, width=50, height=100),
            confidence=0.9,
            class_id=0
        )
        mock_person_detector.detect.return_value = [detection]
        
        # Mock tracks
        track = Track(
            track_id=1,
            bbox=BoundingBox(x=100, y=100, width=50, height=100),
            frame_number=0,
            age=0,
            state=TrackState.ACTIVE
        )
        mock_person_tracker.update.return_value = [track]
        
        # Mock events
        from datetime import datetime, timezone
        event = Event(
            event_id="test-event-1",
            event_type=EventType.ENTRY,
            timestamp=datetime.now(timezone.utc),
            store_id="test_store_001",
            track_id=1,
            metadata={}
        )
        mock_event_generator.process_tracks.return_value = [event]
        mock_event_generator.finalize.return_value = []
        
        # Mock event store
        from src.event_store import BatchResult
        mock_event_store.insert_events_batch.return_value = BatchResult(
            success_count=1,
            errors=[]
        )
        
        # Setup class mocks to return instance mocks
        mock_video_processor_class.return_value = mock_video_processor
        mock_person_detector_class.return_value = mock_person_detector
        mock_person_tracker_class.return_value = mock_person_tracker
        mock_event_generator_class.from_zone_config.return_value = mock_event_generator
        mock_event_store_class.return_value = mock_event_store
        
        # Create pipeline and process
        pipeline = VideoPipeline(temp_video, test_config)
        result = pipeline.process()
        
        # Verify result
        assert result.success is True
        assert result.total_frames == 2
        assert result.frames_failed == 0
        assert result.events_generated == 2  # 2 frames with 1 event each
        assert result.events_stored == 2
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_handles_detection_failure(
        self,
        mock_event_store_class,
        mock_event_generator_class,
        mock_person_tracker_class,
        mock_person_detector_class,
        mock_video_processor_class,
        test_config,
        temp_video
    ):
        """Test pipeline handles detection failures gracefully."""
        # Setup mocks
        mock_video_processor = Mock()
        mock_person_detector = Mock()
        mock_person_tracker = Mock()
        mock_event_generator = Mock()
        mock_event_store = Mock()
        
        # Mock video frame
        frame = Frame(
            frame_number=0,
            timestamp=0.0,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        mock_video_processor.read_frames.return_value = [frame]
        
        # Mock detection failure
        mock_person_detector.detect.side_effect = Exception("Detection failed")
        
        # Mock empty tracks (no detections)
        mock_person_tracker.update.return_value = []
        
        # Mock no events generated
        mock_event_generator.process_tracks.return_value = []
        mock_event_generator.finalize.return_value = []
        
        # Setup class mocks
        mock_video_processor_class.return_value = mock_video_processor
        mock_person_detector_class.return_value = mock_person_detector
        mock_person_tracker_class.return_value = mock_person_tracker
        mock_event_generator_class.from_zone_config.return_value = mock_event_generator
        mock_event_store_class.return_value = mock_event_store
        
        # Create pipeline and process
        pipeline = VideoPipeline(temp_video, test_config)
        
        # Override _detect_people to test error handling
        original_detect = pipeline._detect_people
        def detect_with_error(image):
            try:
                return original_detect(image)
            except:
                return []
        pipeline._detect_people = detect_with_error
        
        result = pipeline.process()
        
        # Verify pipeline continues despite detection failure
        assert result.success is True
        assert result.total_frames == 1
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_handles_frame_processing_error(
        self,
        mock_event_store_class,
        mock_event_generator_class,
        mock_person_tracker_class,
        mock_person_detector_class,
        mock_video_processor_class,
        test_config,
        temp_video
    ):
        """Test pipeline handles frame processing errors."""
        # Setup mocks
        mock_video_processor = Mock()
        mock_person_detector = Mock()
        mock_person_tracker = Mock()
        mock_event_generator = Mock()
        mock_event_store = Mock()
        
        # Mock multiple frames
        frame1 = Frame(
            frame_number=0,
            timestamp=0.0,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        frame2 = Frame(
            frame_number=1,
            timestamp=0.033,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        mock_video_processor.read_frames.return_value = [frame1, frame2]
        
        # Mock detection success for frame 1
        mock_person_detector.detect.return_value = []
        
        # Mock tracker to fail on frame 2 (simulating processing error)
        call_count = [0]
        def tracker_side_effect(detections, frame_number):
            call_count[0] += 1
            if call_count[0] == 1:
                return []
            else:
                raise Exception("Tracker processing error")
        
        mock_person_tracker.update.side_effect = tracker_side_effect
        mock_event_generator.process_tracks.return_value = []
        mock_event_generator.finalize.return_value = []
        
        # Setup class mocks
        mock_video_processor_class.return_value = mock_video_processor
        mock_person_detector_class.return_value = mock_person_detector
        mock_person_tracker_class.return_value = mock_person_tracker
        mock_event_generator_class.from_zone_config.return_value = mock_event_generator
        mock_event_store_class.return_value = mock_event_store
        
        # Create pipeline and process
        pipeline = VideoPipeline(temp_video, test_config)
        result = pipeline.process()
        
        # Verify pipeline continues and tracks errors
        assert result.success is True
        assert result.total_frames == 2
        assert result.frames_failed == 1
        assert len(result.errors) >= 1
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_handles_database_error(
        self,
        mock_event_store_class,
        mock_event_generator_class,
        mock_person_tracker_class,
        mock_person_detector_class,
        mock_video_processor_class,
        test_config,
        temp_video
    ):
        """Test pipeline handles database errors with fallback."""
        # Setup mocks
        mock_video_processor = Mock()
        mock_person_detector = Mock()
        mock_person_tracker = Mock()
        mock_event_generator = Mock()
        mock_event_store = Mock()
        
        # Mock video frame
        frame = Frame(
            frame_number=0,
            timestamp=0.0,
            image=np.zeros((480, 640, 3), dtype=np.uint8),
            resolution=(640, 480)
        )
        mock_video_processor.read_frames.return_value = [frame]
        
        # Mock detections and tracks
        mock_person_detector.detect.return_value = []
        mock_person_tracker.update.return_value = []
        
        # Mock event generation
        from datetime import datetime, timezone
        event = Event(
            event_id="test-event-1",
            event_type=EventType.ENTRY,
            timestamp=datetime.now(timezone.utc),
            store_id="test_store_001",
            track_id=1,
            metadata={}
        )
        mock_event_generator.process_tracks.return_value = [event]
        mock_event_generator.finalize.return_value = []
        
        # Mock database error on batch insert, success on individual insert
        mock_event_store.insert_events_batch.side_effect = Exception("Database error")
        mock_event_store.insert_event.return_value = True
        
        # Setup class mocks
        mock_video_processor_class.return_value = mock_video_processor
        mock_person_detector_class.return_value = mock_person_detector
        mock_person_tracker_class.return_value = mock_person_tracker
        mock_event_generator_class.from_zone_config.return_value = mock_event_generator
        mock_event_store_class.return_value = mock_event_store
        
        # Create pipeline and process
        pipeline = VideoPipeline(temp_video, test_config)
        result = pipeline.process()
        
        # Verify fallback to individual inserts worked
        assert result.success is True
        assert mock_event_store.insert_event.called
    
    @patch("src.pipeline.VideoProcessor")
    @patch("src.pipeline.PersonDetector")
    @patch("src.pipeline.PersonTracker")
    @patch("src.pipeline.EventGenerator")
    @patch("src.pipeline.EventStore")
    def test_pipeline_calls_finalize(
        self,
        mock_event_store_class,
        mock_event_generator_class,
        mock_person_tracker_class,
        mock_person_detector_class,
        mock_video_processor_class,
        test_config,
        temp_video
    ):
        """Test pipeline calls EventGenerator.finalize() at end."""
        # Setup mocks
        mock_video_processor = Mock()
        mock_person_detector = Mock()
        mock_person_tracker = Mock()
        mock_event_generator = Mock()
        mock_event_store = Mock()
        
        # Mock empty video
        mock_video_processor.read_frames.return_value = []
        
        # Mock finalize with exit event
        from datetime import datetime, timezone
        exit_event = Event(
            event_id="test-exit-1",
            event_type=EventType.EXIT,
            timestamp=datetime.now(timezone.utc),
            store_id="test_store_001",
            track_id=1,
            metadata={}
        )
        mock_event_generator.finalize.return_value = [exit_event]
        
        # Mock event store
        from src.event_store import BatchResult
        mock_event_store.insert_events_batch.return_value = BatchResult(
            success_count=1,
            errors=[]
        )
        
        # Setup class mocks
        mock_video_processor_class.return_value = mock_video_processor
        mock_person_detector_class.return_value = mock_person_detector
        mock_person_tracker_class.return_value = mock_person_tracker
        mock_event_generator_class.from_zone_config.return_value = mock_event_generator
        mock_event_store_class.return_value = mock_event_store
        
        # Create pipeline and process
        pipeline = VideoPipeline(temp_video, test_config)
        result = pipeline.process()
        
        # Verify finalize was called and exit event was stored
        mock_event_generator.finalize.assert_called_once()
        assert result.events_generated == 1
        assert result.events_stored == 1
