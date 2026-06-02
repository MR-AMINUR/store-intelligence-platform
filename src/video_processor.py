"""Video processing module for Store Intelligence Platform.

This module provides the VideoProcessor class for reading and decoding video
files, extracting frames with metadata for downstream processing.
"""

import os
from pathlib import Path
from typing import Iterator, Optional, Tuple

import cv2
import numpy as np

from src.logger import Logger
from src.models import Frame


class VideoMetadata:
    """Video metadata container.
    
    Attributes:
        duration: Video duration in seconds
        fps: Frames per second
        frame_count: Total number of frames
        resolution: Video resolution as (width, height)
        codec: Video codec fourcc code
    """
    
    def __init__(
        self,
        duration: float,
        fps: float,
        frame_count: int,
        resolution: Tuple[int, int],
        codec: str
    ):
        self.duration = duration
        self.fps = fps
        self.frame_count = frame_count
        self.resolution = resolution
        self.codec = codec


class VideoProcessor:
    """Processes video files and yields frames with metadata.
    
    The VideoProcessor reads video files using OpenCV, validates formats,
    handles decode errors gracefully, and yields Frame objects with complete
    metadata for each successfully decoded frame.
    
    Supported formats: MP4, AVI, MOV
    
    Example:
        >>> logger = Logger("VideoProcessor", "INFO")
        >>> processor = VideoProcessor("video.mp4", logger)
        >>> for frame in processor.read_frames():
        ...     print(f"Frame {frame.frame_number} at {frame.timestamp}s")
    """
    
    # Supported video file extensions
    SUPPORTED_FORMATS = {'.mp4', '.avi', '.mov'}
    
    def __init__(self, video_path: str, logger: Logger):
        """Initialize video processor with file path.
        
        Args:
            video_path: Path to video file
            logger: Logger instance for structured logging
        
        Raises:
            FileNotFoundError: If video file does not exist
            ValueError: If video format is not supported
        """
        self.video_path = video_path
        self.logger = logger
        
        # Validate video file exists
        if not os.path.exists(video_path):
            error_msg = f"Video file not found: {video_path}"
            self.logger.error(error_msg, video_path=video_path)
            raise FileNotFoundError(error_msg)
        
        # Validate video format
        file_ext = Path(video_path).suffix.lower()
        if file_ext not in self.SUPPORTED_FORMATS:
            error_msg = f"Unsupported video format: {file_ext}. Supported formats: {', '.join(self.SUPPORTED_FORMATS)}"
            self.logger.error(error_msg, file_extension=file_ext, video_path=video_path)
            raise ValueError(error_msg)
        
        self.logger.info(
            "VideoProcessor initialized",
            video_path=video_path,
            file_extension=file_ext
        )
    
    def get_metadata(self) -> VideoMetadata:
        """Get video metadata without reading frames.
        
        Returns:
            VideoMetadata object with video information
        
        Raises:
            RuntimeError: If video cannot be opened
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            error_msg = f"Failed to open video file: {self.video_path}"
            self.logger.error(error_msg, video_path=self.video_path)
            raise RuntimeError(error_msg)
        
        try:
            # Extract metadata from video capture
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fourcc = int(cap.get(cv2.CAP_PROP_FOURCC))
            
            # Calculate duration
            duration = frame_count / fps if fps > 0 else 0.0
            
            # Convert fourcc to string
            codec = "".join([chr((fourcc >> 8 * i) & 0xFF) for i in range(4)])
            
            metadata = VideoMetadata(
                duration=duration,
                fps=fps,
                frame_count=frame_count,
                resolution=(width, height),
                codec=codec
            )
            
            self.logger.info(
                "Video metadata extracted",
                duration=duration,
                fps=fps,
                frame_count=frame_count,
                resolution=f"{width}x{height}",
                codec=codec
            )
            
            return metadata
            
        finally:
            cap.release()
    
    def read_frames(self) -> Iterator[Frame]:
        """Read and yield video frames with metadata.
        
        This generator function reads the video frame by frame, handling
        decode errors gracefully by logging and continuing to the next frame.
        Each successfully decoded frame is yielded as a Frame object with
        complete metadata.
        
        Yields:
            Frame objects with frame_number, timestamp, image, and resolution
        
        Raises:
            RuntimeError: If video cannot be opened
        """
        cap = cv2.VideoCapture(self.video_path)
        
        if not cap.isOpened():
            error_msg = f"Failed to open video file: {self.video_path}"
            self.logger.error(error_msg, video_path=self.video_path)
            raise RuntimeError(error_msg)
        
        try:
            # Get video properties
            fps = cap.get(cv2.CAP_PROP_FPS)
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            resolution = (width, height)
            
            frame_number = 0
            frames_decoded = 0
            frames_failed = 0
            
            self.logger.info(
                "Starting video frame processing",
                video_path=self.video_path,
                fps=fps,
                resolution=f"{width}x{height}"
            )
            
            while True:
                ret, image = cap.read()
                
                # End of video
                if not ret:
                    break
                
                # Check if frame was successfully decoded
                if image is None or image.size == 0:
                    frames_failed += 1
                    self.logger.warning(
                        "Frame decode error - frame is None or empty",
                        frame_number=frame_number,
                        video_path=self.video_path
                    )
                    frame_number += 1
                    continue
                
                # Calculate timestamp from frame number and fps
                timestamp = frame_number / fps if fps > 0 else 0.0
                
                # Create Frame object
                frame = Frame(
                    frame_number=frame_number,
                    timestamp=timestamp,
                    image=image,
                    resolution=resolution
                )
                
                frames_decoded += 1
                frame_number += 1
                
                # Log progress periodically (every 100 frames)
                if frames_decoded % 100 == 0:
                    self.logger.debug(
                        "Frame processing progress",
                        frames_decoded=frames_decoded,
                        frames_failed=frames_failed,
                        current_frame=frame_number
                    )
                
                yield frame
            
            # Log final statistics
            self.logger.info(
                "Video frame processing completed",
                total_frames=frame_number,
                frames_decoded=frames_decoded,
                frames_failed=frames_failed,
                video_path=self.video_path
            )
            
        except Exception as e:
            self.logger.error(
                "Unexpected error during video processing",
                error=str(e),
                video_path=self.video_path
            )
            raise
            
        finally:
            cap.release()
