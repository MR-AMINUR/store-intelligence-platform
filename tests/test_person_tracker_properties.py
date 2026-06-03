"""Property-based tests for PersonTracker.

This module uses Hypothesis to test universal properties that should hold
for the PersonTracker across all valid inputs.
"""

import pytest
from hypothesis import given, strategies as st, settings, assume, HealthCheck
from unittest.mock import Mock

from src.person_tracker import PersonTracker, Position
from src.logger import Logger
from src.models import BoundingBox, Detection, TrackState


def create_mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=Logger)
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


# Hypothesis strategies for generating test data

@st.composite
def bounding_box_strategy(draw):
    """Strategy for generating valid bounding boxes."""
    x = draw(st.floats(min_value=0.0, max_value=1920.0))
    y = draw(st.floats(min_value=0.0, max_value=1080.0))
    width = draw(st.floats(min_value=10.0, max_value=200.0))
    height = draw(st.floats(min_value=10.0, max_value=200.0))
    return BoundingBox(x=x, y=y, width=width, height=height)


@st.composite
def detection_strategy(draw):
    """Strategy for generating valid detections."""
    bbox = draw(bounding_box_strategy())
    confidence = draw(st.floats(min_value=0.5, max_value=1.0))
    class_id = 0  # person class
    return Detection(bbox=bbox, confidence=confidence, class_id=class_id)


@st.composite
def detection_list_strategy(draw):
    """Strategy for generating lists of detections."""
    return draw(st.lists(detection_strategy(), min_size=0, max_size=20))


class TestTrajectoryMaintenanceProperty:
    """Property 8: Trajectory History Maintenance
    
    **Validates: Requirements 3.5**
    
    For any active track, the Person_Tracker SHALL maintain a retrievable
    trajectory history containing all positions over time.
    """
    
    @settings(max_examples=15, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        detections_per_frame=st.lists(
            detection_list_strategy(),
            min_size=1,
            max_size=10
        )
    )
    def test_trajectory_maintained_for_all_active_tracks(self, detections_per_frame):
        """Test that trajectory history is maintained for all active tracks.
        
        Property: For any sequence of frames with detections, every track that
        receives updates must have a trajectory history that can be retrieved
        and contains all its positions over time.
        """
        tracker = PersonTracker(max_age=30, logger=create_mock_logger())
        
        # Track which tracks have been created and their expected trajectory lengths
        track_positions = {}  # track_id -> list of (frame_number, bbox)
        
        # Process each frame
        for frame_number, detections in enumerate(detections_per_frame):
            tracks = tracker.update(detections, frame_number=frame_number)
            
            # For each active track, record its position
            for track in tracks:
                if track.state == TrackState.ACTIVE:
                    if track.track_id not in track_positions:
                        track_positions[track.track_id] = []
                    track_positions[track.track_id].append((frame_number, track.bbox))
        
        # Verify trajectory history for each track that received updates
        for track_id, positions in track_positions.items():
            trajectory = tracker.get_trajectory(track_id)
            
            # Property: Trajectory must exist and have at least as many positions as updates
            assert len(trajectory) >= len(positions), \
                f"Track {track_id} received {len(positions)} updates but trajectory has {len(trajectory)} positions"
            
            # Property: All frame numbers in trajectory must be in ascending order
            frame_numbers = [pos.frame_number for pos in trajectory]
            assert frame_numbers == sorted(frame_numbers), \
                f"Trajectory frame numbers not in ascending order: {frame_numbers}"
            
            # Property: Trajectory positions must correspond to actual detections
            for i, (expected_frame, expected_bbox) in enumerate(positions):
                # Find corresponding trajectory position
                trajectory_at_frame = [pos for pos in trajectory if pos.frame_number == expected_frame]
                assert len(trajectory_at_frame) > 0, \
                    f"No trajectory position found for track {track_id} at frame {expected_frame}"
    
    @settings(max_examples=10, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        initial_detections=detection_list_strategy(),
        occlusion_frames=st.integers(min_value=1, max_value=29),
        reappearance_detection=detection_strategy()
    )
    def test_trajectory_preserved_during_occlusion(self, initial_detections, 
                                                   occlusion_frames, reappearance_detection):
        """Test that trajectory is preserved during temporary occlusions.
        
        Property: When a track experiences temporary occlusion (< max_age frames),
        its trajectory history must be preserved and still be retrievable.
        """
        assume(len(initial_detections) > 0)
        
        tracker = PersonTracker(max_age=30, logger=create_mock_logger())
        
        # Frame 0: Initial detections
        initial_tracks = tracker.update(initial_detections, frame_number=0)
        assume(len(initial_tracks) > 0)
        
        # Record initial trajectories
        initial_trajectory_lengths = {}
        for track in initial_tracks:
            trajectory = tracker.get_trajectory(track.track_id)
            initial_trajectory_lengths[track.track_id] = len(trajectory)
        
        # Simulate occlusion (no detections)
        for frame in range(1, occlusion_frames + 1):
            tracker.update([], frame_number=frame)
        
        # Property: Trajectories must still be retrievable
        for track_id, initial_length in initial_trajectory_lengths.items():
            trajectory = tracker.get_trajectory(track_id)
            assert len(trajectory) == initial_length, \
                f"Trajectory for track {track_id} changed during occlusion"
    
    @settings(max_examples=10, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        num_frames=st.integers(min_value=2, max_value=20),
        detection=detection_strategy()
    )
    def test_trajectory_grows_with_active_track(self, num_frames, detection):
        """Test that trajectory grows as track receives updates.
        
        Property: For any track that is actively updated across multiple frames,
        the trajectory length must increase with each update.
        """
        tracker = PersonTracker(max_age=30, logger=create_mock_logger())
        
        # Track the same detection across multiple frames
        previous_trajectory_length = 0
        track_id = None
        
        for frame_number in range(num_frames):
            tracks = tracker.update([detection], frame_number=frame_number)
            
            if len(tracks) > 0:
                if track_id is None:
                    track_id = tracks[0].track_id
                
                trajectory = tracker.get_trajectory(track_id)
                
                # Property: Trajectory must grow with each update
                assert len(trajectory) > previous_trajectory_length, \
                    f"Trajectory did not grow at frame {frame_number}"
                
                previous_trajectory_length = len(trajectory)
    
    @settings(max_examples=10, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        detections=detection_list_strategy(),
        nonexistent_track_id=st.integers(min_value=1000, max_value=9999)
    )
    def test_trajectory_empty_for_nonexistent_tracks(self, detections, nonexistent_track_id):
        """Test that get_trajectory returns empty list for nonexistent tracks.
        
        Property: For any track ID that has never been assigned by the tracker,
        get_trajectory must return an empty list.
        """
        tracker = PersonTracker(max_age=30, logger=create_mock_logger())
        
        # Process some detections
        tracker.update(detections, frame_number=0)
        
        # Property: Nonexistent track must return empty trajectory
        trajectory = tracker.get_trajectory(nonexistent_track_id)
        assert len(trajectory) == 0, \
            f"Trajectory for nonexistent track {nonexistent_track_id} is not empty"
    
    @settings(max_examples=10, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        detection=detection_strategy(),
        frame_number=st.integers(min_value=0, max_value=100)
    )
    def test_trajectory_positions_are_bbox_centers(self, detection, frame_number):
        """Test that trajectory positions represent bounding box centers.
        
        Property: For any detection that creates or updates a track, the
        corresponding trajectory position must be at the center of the
        detection's bounding box.
        """
        tracker = PersonTracker(max_age=30, logger=create_mock_logger())
        
        # Update with detection
        tracks = tracker.update([detection], frame_number=frame_number)
        
        if len(tracks) > 0:
            track = tracks[0]
            trajectory = tracker.get_trajectory(track.track_id)
            
            # Get the trajectory position for this frame
            positions_at_frame = [pos for pos in trajectory if pos.frame_number == frame_number]
            
            if len(positions_at_frame) > 0:
                position = positions_at_frame[0]
                
                # Calculate expected center
                expected_center_x = detection.bbox.x + detection.bbox.width / 2
                expected_center_y = detection.bbox.y + detection.bbox.height / 2
                
                # Property: Trajectory position must be at bbox center
                assert abs(position.x - expected_center_x) < 0.01, \
                    f"Trajectory x-position {position.x} does not match bbox center {expected_center_x}"
                assert abs(position.y - expected_center_y) < 0.01, \
                    f"Trajectory y-position {position.y} does not match bbox center {expected_center_y}"
    
    @settings(max_examples=10, deadline=2000, suppress_health_check=[HealthCheck.function_scoped_fixture])
    @given(
        detection=detection_strategy(),
        max_age=st.integers(min_value=1, max_value=100)
    )
    def test_trajectory_persists_after_track_removal(self, detection, max_age):
        """Test that trajectory persists even after track is removed.
        
        Property: When a track is removed due to exceeding max_age, its
        trajectory history must still be retrievable.
        """
        tracker = PersonTracker(max_age=max_age, logger=create_mock_logger())
        
        # Frame 0: Create track
        tracks_0 = tracker.update([detection], frame_number=0)
        assume(len(tracks_0) > 0)
        track_id = tracks_0[0].track_id
        
        # Get initial trajectory
        initial_trajectory = tracker.get_trajectory(track_id)
        initial_length = len(initial_trajectory)
        assert initial_length > 0
        
        # Age track beyond max_age
        for frame in range(1, max_age + 2):
            tracker.update([], frame_number=frame)
        
        # Property: Trajectory must still be retrievable after removal
        trajectory_after_removal = tracker.get_trajectory(track_id)
        assert len(trajectory_after_removal) == initial_length, \
            f"Trajectory changed after track removal: was {initial_length}, now {len(trajectory_after_removal)}"
