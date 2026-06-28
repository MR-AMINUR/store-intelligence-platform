"""Configuration module for CV Pipeline.

This module provides centralized configuration management for the
computer vision pipeline, loading settings from JSON config files
and environment variables.
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DetectorConfig:
    """Configuration for person detector.
    
    Attributes:
        model_path: Path to YOLOv8 model weights
        confidence_threshold: Minimum confidence score for detections [0, 1]
        device: Device to use ('cuda' or 'cpu', 'auto' for automatic)
        batch_size: Batch size for inference (1 for real-time)
    """
    model_path: str = "./models/yolov8n.pt"
    confidence_threshold: float = 0.5
    device: str = "auto"
    batch_size: int = 1


@dataclass
class TrackerConfig:
    """Configuration for person tracker.
    
    Attributes:
        max_age: Maximum frames to keep track alive without detection
        min_hits: Minimum hits before track is confirmed
        iou_threshold: IoU threshold for matching detections to tracks
    """
    max_age: int = 30
    min_hits: int = 3
    iou_threshold: float = 0.3


@dataclass
class ZoneConfig:
    """Configuration for zone management.
    
    Attributes:
        config_path: Path to zone configuration JSON file
        dwell_threshold_seconds: Time threshold for ZONE_DWELL events
    """
    config_path: str = "./config/zones.json"
    dwell_threshold_seconds: float = 5.0


@dataclass
class VideoConfig:
    """Configuration for video processing.
    
    Attributes:
        supported_formats: List of supported video file extensions
        frame_skip: Number of frames to skip (0 = process every frame)
        target_fps: Target FPS for processing (None = use video's native FPS)
        resize_width: Resize frame width (None = keep original)
        resize_height: Resize frame height (None = keep original)
    """
    supported_formats: List[str] = field(default_factory=lambda: [".mp4", ".avi", ".mov"])
    frame_skip: int = 0
    target_fps: Optional[int] = None
    resize_width: Optional[int] = None
    resize_height: Optional[int] = None


@dataclass
class APIConfig:
    """Configuration for API integration.
    
    Attributes:
        base_url: Base URL of the Store Intelligence Platform API
        ingest_endpoint: Endpoint path for event ingestion
        timeout_seconds: Request timeout in seconds
        max_retries: Maximum number of retry attempts
        retry_delay_seconds: Delay between retries in seconds
        batch_size: Number of events to batch per request
    """
    base_url: str = "http://localhost:8000"
    ingest_endpoint: str = "/events/ingest"
    timeout_seconds: int = 30
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    batch_size: int = 50


@dataclass
class PipelineConfig:
    """Main pipeline configuration container.
    
    Attributes:
        store_id: Store identifier for event generation
        camera_name: Camera name for logging
        mode: Processing mode ('file' or 'stream')
        replay_timing: Preserve original timing in replay mode
        detector: Detector configuration
        tracker: Tracker configuration
        zone: Zone configuration
        video: Video configuration
        api: API configuration
    """
    store_id: str = "store_001"
    camera_name: str = "camera_001"
    mode: str = "file"  # 'file' or 'stream'
    replay_timing: bool = True
    detector: DetectorConfig = field(default_factory=DetectorConfig)
    tracker: TrackerConfig = field(default_factory=TrackerConfig)
    zone: ZoneConfig = field(default_factory=ZoneConfig)
    video: VideoConfig = field(default_factory=VideoConfig)
    api: APIConfig = field(default_factory=APIConfig)
    
    @classmethod
    def from_json(cls, config_path: str) -> "PipelineConfig":
        """Load pipeline configuration from JSON file.
        
        Args:
            config_path: Path to configuration JSON file
            
        Returns:
            PipelineConfig instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config JSON is invalid
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            data = json.load(f)
        
        return cls.from_dict(data)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PipelineConfig":
        """Create PipelineConfig from dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            PipelineConfig instance
        """
        # Extract nested configurations
        detector_data = data.get("detector", {})
        tracker_data = data.get("tracker", {})
        zone_data = data.get("zone", {})
        video_data = data.get("video", {})
        api_data = data.get("api", {})
        
        return cls(
            store_id=data.get("store_id", "store_001"),
            camera_name=data.get("camera_name", "camera_001"),
            mode=data.get("mode", "file"),
            replay_timing=data.get("replay_timing", True),
            detector=DetectorConfig(**detector_data),
            tracker=TrackerConfig(**tracker_data),
            zone=ZoneConfig(**zone_data),
            video=VideoConfig(**video_data),
            api=APIConfig(**api_data),
        )
    
    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Create PipelineConfig from environment variables.
        
        Environment variables:
            STORE_ID: Store identifier
            CAMERA_NAME: Camera name
            PIPELINE_MODE: Processing mode ('file' or 'stream')
            REPLAY_TIMING: Preserve timing ('true' or 'false')
            API_BASE_URL: Backend API URL
            YOLO_MODEL_PATH: Path to YOLO model
            CONFIDENCE_THRESHOLD: Detection confidence threshold
            ZONE_CONFIG_PATH: Path to zone configuration
            
        Returns:
            PipelineConfig instance
        """
        return cls(
            store_id=os.getenv("STORE_ID", "store_001"),
            camera_name=os.getenv("CAMERA_NAME", "camera_001"),
            mode=os.getenv("PIPELINE_MODE", "file"),
            replay_timing=os.getenv("REPLAY_TIMING", "true").lower() == "true",
            detector=DetectorConfig(
                model_path=os.getenv("YOLO_MODEL_PATH", "./models/yolov8n.pt"),
                confidence_threshold=float(os.getenv("CONFIDENCE_THRESHOLD", "0.5")),
                device=os.getenv("DEVICE", "auto"),
                batch_size=int(os.getenv("BATCH_SIZE", "1")),
            ),
            tracker=TrackerConfig(
                max_age=int(os.getenv("TRACKER_MAX_AGE", "30")),
                min_hits=int(os.getenv("TRACKER_MIN_HITS", "3")),
                iou_threshold=float(os.getenv("TRACKER_IOU_THRESHOLD", "0.3")),
            ),
            zone=ZoneConfig(
                config_path=os.getenv("ZONE_CONFIG_PATH", "./config/zones.json"),
                dwell_threshold_seconds=float(os.getenv("DWELL_THRESHOLD", "5.0")),
            ),
            video=VideoConfig(
                frame_skip=int(os.getenv("FRAME_SKIP", "0")),
                target_fps=int(os.getenv("TARGET_FPS")) if os.getenv("TARGET_FPS") else None,
            ),
            api=APIConfig(
                base_url=os.getenv("API_BASE_URL", "http://localhost:8000"),
                timeout_seconds=int(os.getenv("API_TIMEOUT", "30")),
                max_retries=int(os.getenv("API_MAX_RETRIES", "3")),
                batch_size=int(os.getenv("API_BATCH_SIZE", "50")),
            ),
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.
        
        Returns:
            Configuration as nested dictionary
        """
        return {
            "store_id": self.store_id,
            "camera_name": self.camera_name,
            "mode": self.mode,
            "replay_timing": self.replay_timing,
            "detector": {
                "model_path": self.detector.model_path,
                "confidence_threshold": self.detector.confidence_threshold,
                "device": self.detector.device,
                "batch_size": self.detector.batch_size,
            },
            "tracker": {
                "max_age": self.tracker.max_age,
                "min_hits": self.tracker.min_hits,
                "iou_threshold": self.tracker.iou_threshold,
            },
            "zone": {
                "config_path": self.zone.config_path,
                "dwell_threshold_seconds": self.zone.dwell_threshold_seconds,
            },
            "video": {
                "supported_formats": self.video.supported_formats,
                "frame_skip": self.video.frame_skip,
                "target_fps": self.video.target_fps,
                "resize_width": self.video.resize_width,
                "resize_height": self.video.resize_height,
            },
            "api": {
                "base_url": self.api.base_url,
                "ingest_endpoint": self.api.ingest_endpoint,
                "timeout_seconds": self.api.timeout_seconds,
                "max_retries": self.api.max_retries,
                "retry_delay_seconds": self.api.retry_delay_seconds,
                "batch_size": self.api.batch_size,
            },
        }
    
    def save(self, config_path: str) -> None:
        """Save configuration to JSON file.
        
        Args:
            config_path: Path to save configuration file
        """
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
    
    def validate(self) -> None:
        """Validate configuration parameters.
        
        Raises:
            ValueError: If any configuration parameter is invalid
        """
        errors = []
        
        # Validate detector
        if not Path(self.detector.model_path).exists():
            errors.append(f"YOLO model not found: {self.detector.model_path}")
        
        if not (0 <= self.detector.confidence_threshold <= 1):
            errors.append(f"Confidence threshold must be in [0, 1]: {self.detector.confidence_threshold}")
        
        if self.detector.device not in ["auto", "cuda", "cpu"]:
            errors.append(f"Invalid device: {self.detector.device}. Must be 'auto', 'cuda', or 'cpu'")
        
        # Validate tracker
        if self.tracker.max_age <= 0:
            errors.append(f"Tracker max_age must be positive: {self.tracker.max_age}")
        
        if not (0 <= self.tracker.iou_threshold <= 1):
            errors.append(f"IoU threshold must be in [0, 1]: {self.tracker.iou_threshold}")
        
        # Validate zone
        if not Path(self.zone.config_path).exists():
            errors.append(f"Zone configuration not found: {self.zone.config_path}")
        
        # Validate API
        if not self.api.base_url:
            errors.append("API base_url cannot be empty")
        
        if self.api.timeout_seconds <= 0:
            errors.append(f"API timeout must be positive: {self.api.timeout_seconds}")
        
        if errors:
            raise ValueError("Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors))
