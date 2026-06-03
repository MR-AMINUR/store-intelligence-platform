"""Property-based tests for VideoProcessor using Hypothesis.

This module contains property tests that validate universal correctness
properties of video processing, particularly frame ordering and metadata.
"""

import tempfile
from pathlib import Path

import cv2
import numpy as np
from hypothesis import given, strategies as st, settings

from src.logger import Logger
from src.video_processor import VideoProcessor


def create_test_video_for_property(path: str, num_frames: int, fps: float, resolution: tuple):
    """Helper to create test video for property tests."""
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, resolution)
    
    for i in range(num_frames):
        frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
        color_value = int((i / max(num_frames, 1)) * 255)
        frame[:, :] = (color_value, color_value, color_value)
        out.write(frame)
    
    out.release()


# Property 4: Frame Ordering Preservation
# Validates: Requirements 1.5
@settings(max_examples=15, deadline=5000)  # Reduced examples due to video creation overhead
@given(
    num_frames=st.integers(min_value=5, max_value=30),
    fps=st.sampled_from([15.0, 24.0, 25.0, 30.0, 60.0])
)
def test_property_frame_ordering_preservation(num_frames, fps):
    """
    Property 4: Frame Ordering Preservation
    
    For ANY processed video, the frame_number values SHALL increase
    monotonically, preserving the original frame sequence.
    
    This property validates Requirement 1.5:
    - FOR ALL processed videos, THE Video_Processor SHALL maintain frame ordering
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = str(Path(tmp_dir) / "test_video.mp4")
        resolution = (640, 480)
        
        # Create test video
        create_test_video_for_property(video_path, num_frames, fps, resolution)
        
        # Process video
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        # Property 1: Number of frames should match input
        assert len(frames) == num_frames, \
            f"Expected {num_frames} frames, got {len(frames)}"
        
        # Property 2: Frame numbers must be sequential starting from 0
        for i, frame in enumerate(frames):
            assert frame.frame_number == i, \
                f"Frame {i} has incorrect frame_number: {frame.frame_number}"
        
        # Property 3: Frame numbers must be monotonically increasing
        frame_numbers = [frame.frame_number for frame in frames]
        assert frame_numbers == sorted(frame_numbers), \
            "Frame numbers are not monotonically increasing"
        
        # Property 4: No gaps in frame sequence
        expected_sequence = list(range(num_frames))
        assert frame_numbers == expected_sequence, \
            f"Frame sequence has gaps: expected {expected_sequence}, got {frame_numbers}"
        
        # Property 5: Timestamps must be monotonically increasing
        timestamps = [frame.timestamp for frame in frames]
        assert timestamps == sorted(timestamps), \
            "Timestamps are not monotonically increasing"
        
        # Property 6: Timestamp differences should be consistent (1/fps)
        if len(timestamps) > 1:
            expected_delta = 1.0 / fps
            for i in range(1, len(timestamps)):
                actual_delta = timestamps[i] - timestamps[i-1]
                # Allow 10% tolerance for floating point arithmetic
                assert abs(actual_delta - expected_delta) / expected_delta < 0.1, \
                    f"Timestamp delta at frame {i} is {actual_delta}, expected ~{expected_delta}"


# Property 5: Frame Metadata Completeness
# Validates: Requirements 1.4
@settings(max_examples=15, deadline=5000)
@given(
    num_frames=st.integers(min_value=3, max_value=20),
    fps=st.sampled_from([24.0, 30.0]),
    width=st.sampled_from([320, 640, 1280]),
    height=st.sampled_from([240, 480, 720])
)
def test_property_frame_metadata_completeness(num_frames, fps, width, height):
    """
    Property 5: Frame Metadata Completeness
    
    For ANY successfully decoded video frame, the frame SHALL include all
    metadata fields (frame_number, timestamp, resolution) with valid values.
    
    This property validates Requirement 1.4:
    - THE Video_Processor SHALL extract frame metadata (timestamp, frame number, resolution)
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = str(Path(tmp_dir) / "test_video.mp4")
        resolution = (width, height)
        
        # Create test video
        create_test_video_for_property(video_path, num_frames, fps, resolution)
        
        # Process video
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        for i, frame in enumerate(frames):
            # Property 1: frame_number must be present and valid
            assert hasattr(frame, 'frame_number'), "Frame must have frame_number attribute"
            assert isinstance(frame.frame_number, int), "frame_number must be an integer"
            assert frame.frame_number >= 0, "frame_number must be non-negative"
            assert frame.frame_number == i, f"frame_number must match sequence position"
            
            # Property 2: timestamp must be present and valid
            assert hasattr(frame, 'timestamp'), "Frame must have timestamp attribute"
            assert isinstance(frame.timestamp, (int, float)), "timestamp must be numeric"
            assert frame.timestamp >= 0, "timestamp must be non-negative"
            
            # Property 3: timestamp must be calculated correctly
            expected_timestamp = i / fps
            # Allow small tolerance for floating point arithmetic
            assert abs(frame.timestamp - expected_timestamp) < 0.1, \
                f"timestamp {frame.timestamp} doesn't match expected {expected_timestamp}"
            
            # Property 4: image must be present and valid
            assert hasattr(frame, 'image'), "Frame must have image attribute"
            assert isinstance(frame.image, np.ndarray), "image must be numpy array"
            assert frame.image.size > 0, "image must not be empty"
            assert len(frame.image.shape) == 3, "image must be 3D array (HxWxC)"
            assert frame.image.shape[2] == 3, "image must have 3 channels (BGR)"
            
            # Property 5: resolution must be present and valid
            assert hasattr(frame, 'resolution'), "Frame must have resolution attribute"
            assert isinstance(frame.resolution, tuple), "resolution must be a tuple"
            assert len(frame.resolution) == 2, "resolution must have 2 elements (width, height)"
            assert frame.resolution == resolution, \
                f"resolution {frame.resolution} doesn't match expected {resolution}"
            
            # Property 6: image dimensions must match resolution
            img_height, img_width = frame.image.shape[:2]
            assert (img_width, img_height) == resolution, \
                f"image dimensions ({img_width}, {img_height}) don't match resolution {resolution}"


# Property: Consistent Metadata Across Frames
@settings(max_examples=10, deadline=5000)
@given(
    num_frames=st.integers(min_value=5, max_value=15),
    fps=st.sampled_from([24.0, 30.0]),
    resolution=st.sampled_from([(640, 480), (1280, 720)])
)
def test_property_consistent_metadata_across_frames(num_frames, fps, resolution):
    """
    Property: Consistent Metadata Across Frames
    
    For ANY video, ALL frames SHALL have consistent resolution metadata
    that matches the video's resolution.
    
    This validates that metadata is correctly extracted and consistent.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = str(Path(tmp_dir) / "test_video.mp4")
        
        # Create test video
        create_test_video_for_property(video_path, num_frames, fps, resolution)
        
        # Process video
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        # Property 1: All frames must have the same resolution
        resolutions = [frame.resolution for frame in frames]
        assert all(r == resolution for r in resolutions), \
            f"Not all frames have consistent resolution: {set(resolutions)}"
        
        # Property 2: All frames must have images with matching dimensions
        for frame in frames:
            img_height, img_width = frame.image.shape[:2]
            assert (img_width, img_height) == resolution, \
                f"Frame {frame.frame_number} image dimensions don't match resolution"


# Property: Frame Timestamp Calculation
@settings(max_examples=10, deadline=5000)
@given(
    num_frames=st.integers(min_value=3, max_value=15),
    fps=st.sampled_from([15.0, 24.0, 25.0, 30.0, 60.0])
)
def test_property_frame_timestamp_calculation(num_frames, fps):
    """
    Property: Frame Timestamp Calculation
    
    For ANY video with known FPS, frame timestamps SHALL be calculated
    as frame_number / fps with reasonable precision.
    
    This validates correct timestamp calculation from frame numbers.
    """
    with tempfile.TemporaryDirectory() as tmp_dir:
        video_path = str(Path(tmp_dir) / "test_video.mp4")
        resolution = (640, 480)
        
        # Create test video
        create_test_video_for_property(video_path, num_frames, fps, resolution)
        
        # Process video
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        for frame in frames:
            # Property: timestamp = frame_number / fps (with tolerance)
            expected_timestamp = frame.frame_number / fps
            actual_timestamp = frame.timestamp
            
            # Allow 10% tolerance for floating point arithmetic and codec variations
            tolerance = expected_timestamp * 0.1 if expected_timestamp > 0 else 0.01
            assert abs(actual_timestamp - expected_timestamp) <= tolerance, \
                f"Frame {frame.frame_number}: timestamp {actual_timestamp} " \
                f"doesn't match expected {expected_timestamp} (tolerance: {tolerance})"
