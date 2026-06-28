"""Computer Vision Pipeline for Store Intelligence Platform.

This package provides a complete video processing pipeline that transforms
raw CCTV footage into structured events that feed into the existing Store
Intelligence Platform backend.

Pipeline Flow:
    Raw CCTV Video
    ↓
    Video Upload
    ↓
    YOLOv8 Person Detection (detector.py)
    ↓
    Multi-Object Tracking - ByteTrack (tracker.py)
    ↓
    Zone Mapping (zone_manager.py)
    ↓
    Event Generation (event_generator.py)
    ↓
    POST /events/ingest (event_sender.py)
    ↓
    Existing FastAPI Backend
    ↓
    SQLite Database
    ↓
    Analytics Engine
    ↓
    Dashboard

Modules:
    - config: Pipeline configuration management
    - detector: YOLOv8 person detection
    - tracker: ByteTrack multi-object tracking
    - zone_manager: Store zone definition and point-in-polygon checks
    - event_generator: Transform tracking data into events
    - event_sender: HTTP client for sending events to backend API
    - video_processor: Video file reading and frame extraction
    - run_pipeline: Main pipeline orchestrator and CLI
"""

__version__ = "1.0.0"
__all__ = [
    "PipelineConfig",
    "PersonDetector",
    "PersonTracker",
    "ZoneManager",
    "EventGenerator",
    "EventSender",
    "VideoProcessor",
    "run_pipeline",
]

from pipeline.config import PipelineConfig
from pipeline.detector import PersonDetector
from pipeline.event_generator import EventGenerator
from pipeline.event_sender import EventSender
from pipeline.tracker import PersonTracker
from pipeline.video_processor import VideoProcessor
from pipeline.zone_manager import ZoneManager
