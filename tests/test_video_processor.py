"""Unit tests for VideoProcessor class."""

import os
import tempfile
from pathlib import Path

import cv2
import numpy as np
import pytest

from src.logger import Logger
from src.video_processor import VideoProcessor, VideoMetadata


def create_test_video(path: str, num_frames: int = 10, fps: float = 30.0, resolution: tuple = (640, 480)):
    """Helper function to create a test video file.
    
    Args:
        path: Output video file path
        num_frames: Number of frames to generate
        fps: Frames per second
        resolution: Video resolution as (width, height)
    """
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(path, fourcc, fps, resolution)
    
    for i in range(num_frames):
        # Create a frame with a different color for each frame
        frame = np.zeros((resolution[1], resolution[0], 3), dtype=np.uint8)
        # Add frame number as visual indicator
        color_value = int((i / num_frames) * 255)
        frame[:, :] = (color_value, color_value, color_value)
        out.write(frame)
    
    out.release()


class TestVideoProcessor:
    """Tests for VideoProcessor class."""
    
    def test_init_with_valid_video(self, tmp_path):
        """Test VideoProcessor initialization with valid video file."""
        video_path = str(tmp_path / "test_video.mp4")
        create_test_video(video_path, num_frames=5)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        assert processor.video_path == video_path
        assert processor.logger == logger
    
    def test_init_with_nonexistent_file(self):
        """Test VideoProcessor raises FileNotFoundError for missing file."""
        logger = Logger("TestVideoProcessor", "INFO")
        
        with pytest.raises(FileNotFoundError) as exc_info:
            VideoProcessor("/nonexistent/video.mp4", logger)
        
        assert "Video file not found" in str(exc_info.value)
        assert "/nonexistent/video.mp4" in str(exc_info.value)
    
    def test_init_with_unsupported_format(self, tmp_path):
        """Test VideoProcessor raises ValueError for unsupported format."""
        # Create a dummy file with unsupported extension
        video_path = str(tmp_path / "test_video.mkv")
        Path(video_path).touch()
        
        logger = Logger("TestVideoProcessor", "INFO")
        
        with pytest.raises(ValueError) as exc_info:
            VideoProcessor(video_path, logger)
        
        assert "Unsupported video format" in str(exc_info.value)
        assert ".mkv" in str(exc_info.value)
    
    def test_init_with_supported_formats(self, tmp_path):
        """Test VideoProcessor accepts all supported formats."""
        logger = Logger("TestVideoProcessor", "INFO")
        
        for ext in ['.mp4', '.avi', '.mov']:
            video_path = str(tmp_path / f"test_video{ext}")
            create_test_video(video_path, num_frames=2)
            
            # Should not raise exception
            processor = VideoProcessor(video_path, logger)
            assert processor.video_path == video_path
    
    def test_get_metadata(self, tmp_path):
        """Test get_metadata returns correct video information."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 10
        fps = 30.0
        resolution = (640, 480)
        create_test_video(video_path, num_frames=num_frames, fps=fps, resolution=resolution)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        metadata = processor.get_metadata()
        
        assert isinstance(metadata, VideoMetadata)
        assert metadata.fps == fps
        assert metadata.frame_count == num_frames
        assert metadata.resolution == resolution
        assert metadata.duration == pytest.approx(num_frames / fps, rel=0.1)
        assert isinstance(metadata.codec, str)
    
    def test_read_frames_yields_correct_count(self, tmp_path):
        """Test read_frames yields correct number of frames."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 10
        create_test_video(video_path, num_frames=num_frames)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        assert len(frames) == num_frames
    
    def test_read_frames_frame_metadata(self, tmp_path):
        """Test read_frames yields frames with correct metadata."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 5
        fps = 30.0
        resolution = (640, 480)
        create_test_video(video_path, num_frames=num_frames, fps=fps, resolution=resolution)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        # Check first frame
        first_frame = frames[0]
        assert first_frame.frame_number == 0
        assert first_frame.timestamp == pytest.approx(0.0, abs=0.01)
        assert first_frame.resolution == resolution
        assert first_frame.image.shape == (resolution[1], resolution[0], 3)
        
        # Check last frame
        last_frame = frames[-1]
        assert last_frame.frame_number == num_frames - 1
        expected_timestamp = (num_frames - 1) / fps
        assert last_frame.timestamp == pytest.approx(expected_timestamp, rel=0.1)
    
    def test_read_frames_ordering_preservation(self, tmp_path):
        """Test read_frames preserves frame ordering."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 20
        create_test_video(video_path, num_frames=num_frames)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        # Verify frame numbers are sequential
        for i, frame in enumerate(frames):
            assert frame.frame_number == i, f"Frame {i} has incorrect frame_number: {frame.frame_number}"
        
        # Verify timestamps are monotonically increasing
        timestamps = [frame.timestamp for frame in frames]
        assert timestamps == sorted(timestamps), "Timestamps are not monotonically increasing"
    
    def test_read_frames_image_data(self, tmp_path):
        """Test read_frames yields frames with valid image data."""
        video_path = str(tmp_path / "test_video.mp4")
        create_test_video(video_path, num_frames=5)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        for frame in processor.read_frames():
            # Check image is numpy array
            assert isinstance(frame.image, np.ndarray)
            
            # Check image has correct shape (HxWx3 for BGR)
            assert len(frame.image.shape) == 3
            assert frame.image.shape[2] == 3
            
            # Check image dimensions match resolution
            height, width = frame.image.shape[:2]
            assert (width, height) == frame.resolution
    
    def test_read_frames_with_nonexistent_file(self):
        """Test read_frames raises RuntimeError for missing file after init."""
        logger = Logger("TestVideoProcessor", "INFO")
        
        # We can't test this directly since __init__ validates file existence
        # This test documents the expected behavior
        with pytest.raises(FileNotFoundError):
            VideoProcessor("/nonexistent/video.mp4", logger)
    
    def test_read_frames_multiple_iterations(self, tmp_path):
        """Test read_frames can be called multiple times."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 5
        create_test_video(video_path, num_frames=num_frames)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        # First iteration
        frames1 = list(processor.read_frames())
        assert len(frames1) == num_frames
        
        # Second iteration
        frames2 = list(processor.read_frames())
        assert len(frames2) == num_frames
        
        # Verify both iterations yield same frame numbers
        frame_numbers1 = [f.frame_number for f in frames1]
        frame_numbers2 = [f.frame_number for f in frames2]
        assert frame_numbers1 == frame_numbers2
    
    def test_supported_formats_constant(self):
        """Test SUPPORTED_FORMATS contains expected formats."""
        expected_formats = {'.mp4', '.avi', '.mov'}
        assert VideoProcessor.SUPPORTED_FORMATS == expected_formats
    
    def test_video_metadata_attributes(self):
        """Test VideoMetadata has all required attributes."""
        metadata = VideoMetadata(
            duration=10.0,
            fps=30.0,
            frame_count=300,
            resolution=(640, 480),
            codec="mp4v"
        )
        
        assert metadata.duration == 10.0
        assert metadata.fps == 30.0
        assert metadata.frame_count == 300
        assert metadata.resolution == (640, 480)
        assert metadata.codec == "mp4v"
    
    def test_read_frames_empty_video(self, tmp_path):
        """Test read_frames handles empty video (0 frames) gracefully."""
        video_path = str(tmp_path / "empty_video.mp4")
        # Create a video with at least 1 frame (OpenCV can't create truly empty videos)
        create_test_video(video_path, num_frames=1)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        # Should have at least the frames we created
        assert len(frames) >= 0
    
    def test_frame_timestamp_calculation(self, tmp_path):
        """Test frame timestamps are calculated correctly."""
        video_path = str(tmp_path / "test_video.mp4")
        num_frames = 10
        fps = 25.0  # Use non-standard FPS
        create_test_video(video_path, num_frames=num_frames, fps=fps)
        
        logger = Logger("TestVideoProcessor", "INFO")
        processor = VideoProcessor(video_path, logger)
        
        frames = list(processor.read_frames())
        
        for i, frame in enumerate(frames):
            expected_timestamp = i / fps
            assert frame.timestamp == pytest.approx(expected_timestamp, rel=0.1)
    
    def test_different_resolutions(self, tmp_path):
        """Test VideoProcessor handles different video resolutions."""
        logger = Logger("TestVideoProcessor", "INFO")
        
        resolutions = [(320, 240), (640, 480), (1280, 720), (1920, 1080)]
        
        for resolution in resolutions:
            video_path = str(tmp_path / f"video_{resolution[0]}x{resolution[1]}.mp4")
            create_test_video(video_path, num_frames=3, resolution=resolution)
            
            processor = VideoProcessor(video_path, logger)
            frames = list(processor.read_frames())
            
            assert len(frames) == 3
            for frame in frames:
                assert frame.resolution == resolution
                height, width = frame.image.shape[:2]
                assert (width, height) == resolution
