"""Unit tests for PersonTracker."""

import pytest
from unittest.mock import Mock

from src.person_tracker import PersonTracker, Position
from src.logger import Logger
from src.models import BoundingBox, Detection, TrackState


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
def tracker(mock_logger):
    """Create a PersonTracker instance for testing."""
    return PersonTracker(max_age=30, logger=mock_logger)


@pytest.fixture
def sample_detection():
    """Create a sample detection for testing."""
    return Detection(
        bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0),
        confidence=0.85,
        class_id=0
    )


class TestPersonTrackerInitialization:
    """Tests for PersonTracker initialization."""
    
    def test_initialization_success(self, mock_logger):
        """Test PersonTracker can be initialized successfully."""
        tracker = PersonTracker(max_age=30, logger=mock_logger)
        
        assert tracker.max_age == 30
        assert tracker.logger == mock_logger
        assert tracker.next_id == 1
        assert len(tracker.tracks) == 0
        assert len(tracker.trajectories) == 0
    
    def test_initialization_with_invalid_max_age(self, mock_logger):
        """Test PersonTracker raises ValueError for invalid max_age."""
        with pytest.raises(ValueError, match="max_age must be positive"):
            PersonTracker(max_age=0, logger=mock_logger)
        
        with pytest.raises(ValueError, match="max_age must be positive"):
            PersonTracker(max_age=-5, logger=mock_logger)
    
    def test_initialization_logs_creation(self, mock_logger):
        """Test PersonTracker logs initialization."""
        tracker = PersonTracker(max_age=30, logger=mock_logger)
        
        mock_logger.info.assert_called_with(
            "PersonTracker initialized",
            max_age=30
        )
    
    def test_initialization_without_logger(self):
        """Test PersonTracker can be initialized without logger."""
        tracker = PersonTracker(max_age=30, logger=None)
        
        assert tracker.max_age == 30
        assert tracker.logger is None
        assert tracker.next_id == 1


class TestPersonTrackerTrackAssignment:
    """Tests for track assignment in PersonTracker."""
    
    def test_first_detection_creates_new_track(self, tracker, sample_detection):
        """Test that the first detection creates a new track with ID 1."""
        tracks = tracker.update([sample_detection], frame_number=0)
        
        assert len(tracks) == 1
        assert tracks[0].track_id == 1
        assert tracks[0].bbox == sample_detection.bbox
        assert tracks[0].frame_number == 0
        assert tracks[0].age == 0
        assert tracks[0].state == TrackState.ACTIVE
    
    def test_multiple_detections_create_multiple_tracks(self, tracker):
        """Test that multiple detections create multiple tracks."""
        detections = [
            Detection(bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0), confidence=0.85, class_id=0),
            Detection(bbox=BoundingBox(x=300.0, y=400.0, width=60.0, height=90.0), confidence=0.90, class_id=0),
            Detection(bbox=BoundingBox(x=500.0, y=100.0, width=55.0, height=85.0), confidence=0.75, class_id=0),
        ]
        
        tracks = tracker.update(detections, frame_number=0)
        
        assert len(tracks) == 3
        assert tracks[0].track_id == 1
        assert tracks[1].track_id == 2
        assert tracks[2].track_id == 3
    
    def test_similar_detection_maintains_track_id(self, tracker, sample_detection):
        """Test that similar detections in consecutive frames maintain track ID."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id_0 = tracks_0[0].track_id
        
        # Frame 1: Similar detection (small movement)
        detection_1 = Detection(
            bbox=BoundingBox(x=105.0, y=205.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        tracks_1 = tracker.update([detection_1], frame_number=1)
        
        assert len(tracks_1) == 1
        assert tracks_1[0].track_id == track_id_0
        assert tracks_1[0].frame_number == 1
    
    def test_distant_detection_creates_new_track(self, tracker, sample_detection):
        """Test that distant detections create new tracks."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id_0 = tracks_0[0].track_id
        
        # Frame 1: Distant detection (no overlap)
        detection_1 = Detection(
            bbox=BoundingBox(x=500.0, y=500.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        tracks_1 = tracker.update([detection_1], frame_number=1)
        
        # Should have 2 tracks (1 lost, 1 active)
        assert len(tracks_1) == 2
        track_ids = {track.track_id for track in tracks_1}
        assert track_id_0 in track_ids
        assert track_id_0 + 1 in track_ids


class TestPersonTrackerOcclusionHandling:
    """Tests for occlusion handling in PersonTracker."""
    
    def test_track_maintained_during_short_occlusion(self, tracker, sample_detection):
        """Test that tracks are maintained during short occlusions (< max_age frames)."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frames 1-29: No detections (occlusion)
        for frame in range(1, 30):
            tracks = tracker.update([], frame_number=frame)
            # Track should still exist but in LOST state
            assert len(tracks) == 1
            assert tracks[0].track_id == track_id
            assert tracks[0].state == TrackState.LOST
            assert tracks[0].age == frame
        
        # Track should still exist after 29 frames
        assert len(tracker.tracks) == 1
    
    def test_track_removed_after_max_age(self, tracker, sample_detection):
        """Test that tracks are removed after exceeding max_age frames."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frames 1-30: No detections (occlusion)
        for frame in range(1, 31):
            tracks = tracker.update([], frame_number=frame)
        
        # Track should be removed after 31 frames (age > 30)
        tracks_31 = tracker.update([], frame_number=31)
        assert len(tracks_31) == 0
        assert len(tracker.tracks) == 0
    
    def test_track_reactivated_after_occlusion(self, tracker, sample_detection):
        """Test that tracks are reactivated when detection reappears."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frames 1-10: No detections (occlusion)
        for frame in range(1, 11):
            tracker.update([], frame_number=frame)
        
        # Frame 11: Detection reappears
        detection_11 = Detection(
            bbox=BoundingBox(x=105.0, y=205.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        tracks_11 = tracker.update([detection_11], frame_number=11)
        
        assert len(tracks_11) == 1
        assert tracks_11[0].track_id == track_id
        assert tracks_11[0].state == TrackState.ACTIVE
        assert tracks_11[0].age == 0
    
    def test_new_track_assigned_after_extended_absence(self, tracker, sample_detection):
        """Test that new track ID is assigned after extended absence (> max_age frames)."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        original_track_id = tracks_0[0].track_id
        
        # Frames 1-31: No detections (extended occlusion)
        for frame in range(1, 32):
            tracker.update([], frame_number=frame)
        
        # Frame 32: Detection reappears (should get new track ID)
        tracks_32 = tracker.update([sample_detection], frame_number=32)
        
        assert len(tracks_32) == 1
        assert tracks_32[0].track_id != original_track_id
        assert tracks_32[0].track_id == original_track_id + 1
        assert tracks_32[0].state == TrackState.ACTIVE


class TestPersonTrackerTrajectoryStorage:
    """Tests for trajectory storage in PersonTracker."""
    
    def test_trajectory_stored_for_single_detection(self, tracker, sample_detection):
        """Test that trajectory is stored for a single detection."""
        tracks = tracker.update([sample_detection], frame_number=0)
        track_id = tracks[0].track_id
        
        trajectory = tracker.get_trajectory(track_id)
        
        assert len(trajectory) == 1
        assert trajectory[0].x == 125.0  # center_x = 100 + 50/2
        assert trajectory[0].y == 240.0  # center_y = 200 + 80/2
        assert trajectory[0].frame_number == 0
    
    def test_trajectory_accumulated_over_frames(self, tracker):
        """Test that trajectory accumulates positions over multiple frames."""
        detections = [
            Detection(bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0), confidence=0.85, class_id=0),
            Detection(bbox=BoundingBox(x=110.0, y=210.0, width=50.0, height=80.0), confidence=0.85, class_id=0),
            Detection(bbox=BoundingBox(x=120.0, y=220.0, width=50.0, height=80.0), confidence=0.85, class_id=0),
        ]
        
        # Frame 0
        tracks_0 = tracker.update([detections[0]], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frame 1
        tracker.update([detections[1]], frame_number=1)
        
        # Frame 2
        tracker.update([detections[2]], frame_number=2)
        
        trajectory = tracker.get_trajectory(track_id)
        
        assert len(trajectory) == 3
        assert trajectory[0].x == 125.0
        assert trajectory[0].y == 240.0
        assert trajectory[1].x == 135.0
        assert trajectory[1].y == 250.0
        assert trajectory[2].x == 145.0
        assert trajectory[2].y == 260.0
    
    def test_trajectory_preserved_during_occlusion(self, tracker, sample_detection):
        """Test that trajectory is preserved during occlusion."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frames 1-10: No detections (occlusion)
        for frame in range(1, 11):
            tracker.update([], frame_number=frame)
        
        # Trajectory should still be available
        trajectory = tracker.get_trajectory(track_id)
        assert len(trajectory) == 1
        assert trajectory[0].frame_number == 0
    
    def test_get_trajectory_empty_for_nonexistent_track(self, tracker):
        """Test that get_trajectory returns empty list for nonexistent track."""
        trajectory = tracker.get_trajectory(999)
        assert len(trajectory) == 0
    
    def test_trajectory_cleared_after_track_removal(self, tracker, sample_detection):
        """Test that trajectory persists even after track is removed."""
        # Frame 0: Initial detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frames 1-31: No detections (track will be removed)
        for frame in range(1, 32):
            tracker.update([], frame_number=frame)
        
        # Track should be removed but trajectory should persist
        trajectory = tracker.get_trajectory(track_id)
        assert len(trajectory) == 1


class TestPersonTrackerIoUCalculation:
    """Tests for IoU calculation in PersonTracker."""
    
    def test_iou_identical_boxes(self, tracker):
        """Test IoU calculation for identical bounding boxes."""
        bbox1 = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        bbox2 = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        
        iou = tracker._compute_iou(bbox1, bbox2)
        
        assert iou == 1.0
    
    def test_iou_no_overlap(self, tracker):
        """Test IoU calculation for non-overlapping boxes."""
        bbox1 = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        bbox2 = BoundingBox(x=300.0, y=400.0, width=50.0, height=80.0)
        
        iou = tracker._compute_iou(bbox1, bbox2)
        
        assert iou == 0.0
    
    def test_iou_partial_overlap(self, tracker):
        """Test IoU calculation for partially overlapping boxes."""
        bbox1 = BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0)
        bbox2 = BoundingBox(x=125.0, y=220.0, width=50.0, height=80.0)
        
        iou = tracker._compute_iou(bbox1, bbox2)
        
        # Calculate expected IoU
        # Intersection: width = 25, height = 60, area = 1500
        # Union: (50*80) + (50*80) - 1500 = 8000 - 1500 = 6500
        # IoU = 1500 / 6500 ≈ 0.2307
        assert 0.23 < iou < 0.24
    
    def test_iou_one_box_inside_another(self, tracker):
        """Test IoU calculation when one box is inside another."""
        bbox1 = BoundingBox(x=100.0, y=200.0, width=100.0, height=100.0)
        bbox2 = BoundingBox(x=120.0, y=220.0, width=40.0, height=40.0)
        
        iou = tracker._compute_iou(bbox1, bbox2)
        
        # Intersection: 40*40 = 1600
        # Union: (100*100) + (40*40) - 1600 = 10000 + 1600 - 1600 = 10000
        # IoU = 1600 / 10000 = 0.16
        assert iou == 0.16


class TestPersonTrackerEdgeCases:
    """Tests for edge cases in PersonTracker."""
    
    def test_empty_detections_list(self, tracker):
        """Test handling of empty detections list."""
        tracks = tracker.update([], frame_number=0)
        
        assert len(tracks) == 0
        assert len(tracker.tracks) == 0
    
    def test_multiple_frames_with_no_detections(self, tracker):
        """Test multiple consecutive frames with no detections."""
        for frame in range(10):
            tracks = tracker.update([], frame_number=frame)
            assert len(tracks) == 0
    
    def test_alternating_detections_and_no_detections(self, tracker, sample_detection):
        """Test alternating frames with and without detections."""
        # Frame 0: Detection
        tracks_0 = tracker.update([sample_detection], frame_number=0)
        track_id = tracks_0[0].track_id
        
        # Frame 1: No detection
        tracks_1 = tracker.update([], frame_number=1)
        assert len(tracks_1) == 1
        assert tracks_1[0].state == TrackState.LOST
        
        # Frame 2: Detection reappears
        tracks_2 = tracker.update([sample_detection], frame_number=2)
        assert len(tracks_2) == 1
        assert tracks_2[0].track_id == track_id
        assert tracks_2[0].state == TrackState.ACTIVE
    
    def test_many_detections_in_single_frame(self, tracker):
        """Test handling of many detections in a single frame."""
        detections = [
            Detection(
                bbox=BoundingBox(x=float(i*100), y=float(i*100), width=50.0, height=80.0),
                confidence=0.85,
                class_id=0
            )
            for i in range(20)
        ]
        
        tracks = tracker.update(detections, frame_number=0)
        
        assert len(tracks) == 20
        assert len(set(track.track_id for track in tracks)) == 20  # All unique IDs
    
    def test_track_id_incrementing(self, tracker):
        """Test that track IDs increment correctly."""
        # Create 5 tracks in frame 0
        detections = [
            Detection(
                bbox=BoundingBox(x=float(i*100), y=float(i*100), width=50.0, height=80.0),
                confidence=0.85,
                class_id=0
            )
            for i in range(5)
        ]
        
        tracks = tracker.update(detections, frame_number=0)
        
        track_ids = sorted([track.track_id for track in tracks])
        assert track_ids == [1, 2, 3, 4, 5]
        
        # Remove all tracks
        for frame in range(1, 32):
            tracker.update([], frame_number=frame)
        
        # Create new track - should get ID 6
        new_detection = Detection(
            bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        new_tracks = tracker.update([new_detection], frame_number=32)
        
        assert new_tracks[0].track_id == 6


class TestPersonTrackerLogging:
    """Tests for logging in PersonTracker."""
    
    def test_update_logs_debug_info(self, mock_logger):
        """Test that update() logs debug information."""
        tracker = PersonTracker(max_age=30, logger=mock_logger)
        
        detection = Detection(
            bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        
        tracker.update([detection], frame_number=0)
        
        # Check debug logging was called
        mock_logger.debug.assert_called()
    
    def test_new_track_creation_logged(self, mock_logger):
        """Test that new track creation is logged."""
        tracker = PersonTracker(max_age=30, logger=mock_logger)
        
        detection = Detection(
            bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        
        tracker.update([detection], frame_number=0)
        
        # Verify track creation was logged
        calls = [call for call in mock_logger.debug.call_args_list]
        assert any("New track created" in str(call) for call in calls)
    
    def test_track_removal_logged(self, mock_logger):
        """Test that track removal is logged."""
        tracker = PersonTracker(max_age=30, logger=mock_logger)
        
        detection = Detection(
            bbox=BoundingBox(x=100.0, y=200.0, width=50.0, height=80.0),
            confidence=0.85,
            class_id=0
        )
        
        # Create track
        tracker.update([detection], frame_number=0)
        
        # Age track beyond max_age
        for frame in range(1, 32):
            tracker.update([], frame_number=frame)
        
        # Verify track removal was logged
        calls = [call for call in mock_logger.debug.call_args_list]
        assert any("Track removed" in str(call) for call in calls)
