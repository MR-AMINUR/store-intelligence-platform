"""Video Processor for CV Pipeline.

This module handles video file reading, frame extraction, and
preprocessing for the computer vision pipeline.
"""

import logging
import time
from pathlib import Path
from typing import Iterator, Optional, Tuple

import cv2
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class VideoMetadata:
    """Video metadata container.
    
    Attributes:
        duration: Video duration in seconds
        fps: Frames per second
        frame_count: Total frames
        resolution: (width, height)
        codec: Video codec
    """
    
    def __init__(
        self,
        duration: float,
        fps: float,
        frame_count: int,
        resolution: Tuple[int, int],
        codec: str,
    ):
        self.duration = duration
        self.fps = fps
        self.frame_count = frame_count
        self.resolution = resolution
        self.codec = codec
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "duration": self.duration,
            "fps": self.fps,
            "frame_count": self.frame_count,
            "resolution": self.resolution,
            "codec": self.codec,
        }


class Frame:
    """Video frame with metadata.
    
    Attributes:
        frame_number: Sequential frame number
        timestamp: Time in seconds from video start
        image: Frame image (HxWx3 BGR format)
        resolution: (width, height)
    """
    
    def __init__(
        self,
        frame_number: int,
        timestamp: float,
        image: np.ndarray,
        resolution: Tuple[int, int],
    ):
        self.frame_number = frame_number
        self.timestamp = timestamp
        self.image = image
        self.resolution = resolution


class VideoProcessor:
    """Processes video files and yields frames.
    
    Supports MP4, AVI, MOV formats. Handles frame skipping,
    resizing, and error recovery.
    
    Attributes:
        video_path: Path to video file
        frame_skip: Number of frames to skip
        target_fps: Target FPS (None = use native)
        resize_width: Resize width (None = keep original)
        resize_height: Resize height (None = keep original)
    """
    
    SUPPORTED_FORMATS = {'.mp4', '.avi', '.mov'}
    
    def __init__(
        self,
        video_path: str,
        frame_skip: int = 0,
        target_fps: Optional[int] = None,
        resize_width: Optional[int] = None,
        resize_height: Optional[int] = None,
    ):
        """Initialize video processor.
        
        Args:
            video_path: Path to video file
            frame_skip: Frames to skip (0 = process all)
            target_fps: Target FPS (None = use native)
            resize_width: Resize width (None = keep original)
            resize_height: Resize height (None = keep original)
            
        Raises:
            FileNotFoundError: If video file doesn't exist
            ValueError: If video format not supported
        """
        self.video_path = video_path
        self.frame_skip = frame_skip
        self.target_fps = target_fps
        self.resize_width = resize_width
        self.resize_height = resize_height
        
        # Validate video file
        if not Path(video_path).exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        
        file_ext = Path(video_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            raise ValueError(
                f"Unsupported video format: {file_ext}. "
                f"Supported: {', '.join(self.SUPPORTED_FORMATS)}"
            )
        
        logger.info(f"VideoProcessor initialized (path={video_path}, frame_skip={frame_skip})")
    
    def get_metadata(self) -> VideoMetadata:
        """Get video metadata.
        
        Returns:
            VideoMetadata object
            
        Raises:
            RuntimeError: If video cannot be opened
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            duration = frame_count / fps if fps > 0 else 0.0
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            metadata = VideoMetadata(
                duration=duration,
                fps=fps,
                frame_count=frame_count,
                resolution=(width, height),
                codec=codec,
            )
            
            logger.info(f"Video metadata: {metadata.to_dict()}")
            return metadata
            
        finally:
            cap.release()
    
    def read_frames(self) -> Iterator[Frame]:
        """Read and yield video frames.
        
        Yields:
            Frame objects with metadata
            
        Raises:
            RuntimeError: If video cannot be opened
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            raise RuntimeError(f"Failed to open video: {self.video_path}")
        
        try:
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            resolution = (width, height)
            
            # Calculate frame skip for target FPS
            actual_frame_skip = self.frame_skip
            if self.target_fps and self.target_fps < fps:
                actual_frame_skip = max(int(fps / self.target_fps) - 1, 0)
            
            frame_number = 0
            frames_decoded = 0
            frames_failed = 0
            frames_skipped = 0
            
            logger.info(f"Starting frame processing (fps={fps}, resolution={width}x{height})")
            
            while True:
                ret, image = cap.read()
                
                if not ret:
                    break
                
                # Check frame validity
                if image is None or image.size == 0:
                    frames_failed += 1
                    frame_number += 1
                    continue
                
                # Skip frames if needed
                if frames_decoded > 0 and actual_frame_skip > 0:
                    if frames_decoded % (actual_frame_skip + 1) != 0:
                        frames_skipped += 1
                        frame_number += 1
                        continue
                
                # Resize if requested
                if self.resize_width and self.resize_height:
                    image = cv2.resize(image, (self.resize_width, self.resize_height))
                    resolution = (self.resize_width, self.resize_height)
                
                # Calculate timestamp
                timestamp = frame_number / fps if fps > 0 else 0.0
                
                frame = Frame(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    image=image,
                    resolution=resolution,
                )
                
                frames_decoded += 1
                frame_number += 1
                
                # Log progress
                if frames_decoded % 100 == 0:
                    logger.debug(
                        f"Progress: {frames_decoded} frames decoded, "
                        f"{frames_skipped} skipped, {frames_failed} failed"
                    )
                
                yield frame
            
            logger.info(
                f"Frame processing complete: "
                f"{frames_decoded} decoded, {frames_skipped} skipped, {frames_failed} failed"
            )
            
        except Exception as e:
            logger.error(f"Error during video processing: {e}")
            raise
            
        finally:
            cap.release()
    
    def read_frames_with_timing(self, replay_timing: bool = True) -> Iterator[Frame]:
        """Read frames with optional timing preservation.
        
        Args:
            replay_timing: If True, sleep to preserve original timing
            
        Yields:
            Frame objects
        """
        last_timestamp = 0.0
        
        for frame in self.read_frames():
            if replay_timing and frame.timestamp > last_timestamp:
                sleep_duration = frame.timestamp - last_timestamp
                if sleep_duration > 0:
                    time.sleep(sleep_duration)
            
            last_timestamp = frame.timestamp
            yield frame
