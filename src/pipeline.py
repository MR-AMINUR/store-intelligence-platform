"""Video processing pipeline integration module.

This module provides the VideoPipeline class that orchestrates the complete
end-to-end video processing workflow, integrating all system components:
VideoProcessor, PersonDetector, PersonTracker, EventGenerator, and EventStore.
"""

from typing import List, Optional

from src.config import ConfigManager
from src.event_generator import EventGenerator
from src.event_store import EventStore
from src.logger import CorrelationContext, Logger
from src.models import Event
from src.person_detector import PersonDetector
from src.person_tracker import PersonTracker
from src.video_processor import VideoProcessor


class PipelineResult:
    """Result of pipeline execution.
    
    Attributes:
        success: Whether the pipeline completed successfully
        total_frames: Total number of frames processed
        frames_failed: Number of frames that failed to process
        events_generated: Number of events generated
        events_stored: Number of events successfully stored
        errors: List of error messages encountered during processing
    """
    
    def __init__(
        self,
        success: bool,
        total_frames: int = 0,
        frames_failed: int = 0,
        events_generated: int = 0,
        events_stored: int = 0,
        errors: Optional[List[str]] = None
    ):
        self.success = success
        self.total_frames = total_frames
        self.frames_failed = frames_failed
        self.events_generated = events_generated
        self.events_stored = events_stored
        self.errors = errors or []


class VideoPipeline:
    """End-to-end video processing pipeline.
    
    The VideoPipeline orchestrates the complete workflow for processing video
    files and generating structured events:
    
    1. Read and decode video frames (VideoProcessor)
    2. Detect people in each frame (PersonDetector)
    3. Track people across frames (PersonTracker)
    4. Generate events from tracking data (EventGenerator)
    5. Store events in database (EventStore)
    
    The pipeline includes comprehensive error handling at each stage:
    - Frame decode errors: logged and skipped
    - Detection failures: logged and treated as empty detections
    - Database errors: retried with exponential backoff
    
    Attributes:
        video_path: Path to video file to process
        config: Configuration manager
        logger: Logger instance for structured logging
        video_processor: VideoProcessor instance
        person_detector: PersonDetector instance
        person_tracker: PersonTracker instance
        event_generator: EventGenerator instance
        event_store: EventStore instance
    
    Example:
        >>> config = ConfigManager()
        >>> logger = Logger("VideoPipeline", "INFO")
        >>> pipeline = VideoPipeline("video.mp4", config, logger)
        >>> result = pipeline.process()
        >>> print(f"Processed {result.total_frames} frames, generated {result.events_generated} events")
    """
    
    def __init__(
        self,
        video_path: str,
        config: ConfigManager,
        logger: Optional[Logger] = None
    ):
        """Initialize pipeline with video path and configuration.
        
        Args:
            video_path: Path to video file to process
            config: ConfigManager instance with system configuration
            logger: Optional Logger instance for structured logging
        
        Raises:
            FileNotFoundError: If video file or required configuration files don't exist
            ValueError: If configuration is invalid
        """
        self.video_path = video_path
        self.config = config
        self.logger = logger or Logger("VideoPipeline", config.get("LOG_LEVEL", "INFO"))
        
        # Generate correlation ID for this pipeline run
        self.correlation_id = CorrelationContext.generate()
        self.logger.set_correlation_id(self.correlation_id)
        
        self.logger.info(
            "Initializing video processing pipeline",
            video_path=video_path,
            correlation_id=self.correlation_id
        )
        
        # Initialize VideoProcessor
        self.video_processor = VideoProcessor(
            video_path=video_path,
            logger=Logger("VideoProcessor", config.get("LOG_LEVEL", "INFO"))
        )
        self.video_processor.logger.set_correlation_id(self.correlation_id)
        
        # Initialize PersonDetector
        model_path = config.get("YOLO_MODEL_PATH", "./models/yolov8n.pt")
        confidence_threshold = float(config.get("CONFIDENCE_THRESHOLD", "0.5"))
        self.person_detector = PersonDetector(
            model_path=model_path,
            confidence_threshold=confidence_threshold,
            logger=Logger("PersonDetector", config.get("LOG_LEVEL", "INFO"))
        )
        self.person_detector.logger.set_correlation_id(self.correlation_id)
        
        # Initialize PersonTracker
        max_age = int(config.get("TRACKER_MAX_AGE", "30"))
        self.person_tracker = PersonTracker(
            max_age=max_age,
            logger=Logger("PersonTracker", config.get("LOG_LEVEL", "INFO"))
        )
        self.person_tracker.logger.set_correlation_id(self.correlation_id)
        
        # Initialize EventGenerator
        store_id = config.get("STORE_ID", "store_001")
        zone_config_path = config.get("ZONE_CONFIG_PATH", "./config/zones.json")
        self.event_generator = EventGenerator.from_zone_config(
            store_id=store_id,
            zone_config_path=zone_config_path,
            logger=Logger("EventGenerator", config.get("LOG_LEVEL", "INFO"))
        )
        self.event_generator.logger.set_correlation_id(self.correlation_id)
        
        # Initialize EventStore
        db_path = config.get("DB_PATH", "./data/events.db")
        self.event_store = EventStore(
            db_path=db_path,
            logger=Logger("EventStore", config.get("LOG_LEVEL", "INFO"))
        )
        self.event_store.logger.set_correlation_id(self.correlation_id)
        
        self.logger.info("Pipeline initialization complete")
    
    def process(self) -> PipelineResult:
        """Process video through complete pipeline.
        
        Executes the complete pipeline workflow:
        1. Read frames from video
        2. Detect people in each frame
        3. Update person tracking
        4. Generate events from tracking data
        5. Store events in database
        6. Finalize event generation (EXIT events for remaining tracks)
        
        Error handling:
        - Frame decode errors: logged and skipped, processing continues
        - Detection failures: logged and treated as empty detections
        - Database errors: retried automatically by EventStore
        
        Returns:
            PipelineResult with execution statistics and any errors encountered
        
        Example:
            >>> pipeline = VideoPipeline("video.mp4", config, logger)
            >>> result = pipeline.process()
            >>> if result.success:
            ...     print(f"Success! Generated {result.events_generated} events")
            ... else:
            ...     print(f"Failed with errors: {result.errors}")
        """
        total_frames = 0
        frames_failed = 0
        events_generated = 0
        events_stored = 0
        errors = []
        
        self.logger.info("Starting video processing pipeline")
        
        try:
            # Process video frame by frame
            for frame in self.video_processor.read_frames():
                total_frames += 1
                
                try:
                    # Step 1: Detect people in frame
                    detections = self._detect_people(frame.image)
                    
                    # Step 2: Update tracking with detections
                    tracks = self.person_tracker.update(detections, frame.frame_number)
                    
                    # Step 3: Generate events from tracks
                    frame_events = self.event_generator.process_tracks(tracks, frame.frame_number)
                    events_generated += len(frame_events)
                    
                    # Step 4: Store events in database
                    stored_count = self._store_events(frame_events)
                    events_stored += stored_count
                    
                    # Log progress periodically (every 100 frames)
                    if total_frames % 100 == 0:
                        self.logger.info(
                            "Pipeline progress",
                            frames_processed=total_frames,
                            frames_failed=frames_failed,
                            events_generated=events_generated,
                            events_stored=events_stored
                        )
                
                except Exception as e:
                    frames_failed += 1
                    error_msg = f"Frame {frame.frame_number} processing failed: {str(e)}"
                    errors.append(error_msg)
                    self.logger.error(
                        "Frame processing error",
                        frame_number=frame.frame_number,
                        error=str(e)
                    )
                    # Continue processing next frame
                    continue
            
            # Step 5: Finalize event generation (generate EXIT events for remaining tracks)
            self.logger.info("Finalizing event generation")
            final_events = self.event_generator.finalize()
            events_generated += len(final_events)
            
            # Store final events
            stored_count = self._store_events(final_events)
            events_stored += stored_count
            
            # Log final statistics
            self.logger.info(
                "Pipeline processing complete",
                total_frames=total_frames,
                frames_failed=frames_failed,
                events_generated=events_generated,
                events_stored=events_stored,
                success=True
            )
            
            return PipelineResult(
                success=True,
                total_frames=total_frames,
                frames_failed=frames_failed,
                events_generated=events_generated,
                events_stored=events_stored,
                errors=errors
            )
        
        except Exception as e:
            error_msg = f"Pipeline failed: {str(e)}"
            errors.append(error_msg)
            self.logger.error(
                "Pipeline execution failed",
                error=str(e),
                total_frames=total_frames,
                frames_failed=frames_failed
            )
            
            return PipelineResult(
                success=False,
                total_frames=total_frames,
                frames_failed=frames_failed,
                events_generated=events_generated,
                events_stored=events_stored,
                errors=errors
            )
    
    def _detect_people(self, frame_image):
        """Detect people in frame with error handling.
        
        Args:
            frame_image: Frame image as numpy array
        
        Returns:
            List of Detection objects, or empty list if detection fails
        """
        try:
            detections = self.person_detector.detect(frame_image)
            return detections
        except Exception as e:
            self.logger.warning(
                "Detection failed, continuing with empty detections",
                error=str(e)
            )
            return []
    
    def _store_events(self, events: List[Event]) -> int:
        """Store events in database with error handling and retry.
        
        Args:
            events: List of Event objects to store
        
        Returns:
            Number of events successfully stored
        """
        if not events:
            return 0
        
        try:
            # Use batch insert for efficiency
            result = self.event_store.insert_events_batch(events)
            
            if result.errors:
                self.logger.warning(
                    "Some events failed to store",
                    success_count=result.success_count,
                    error_count=len(result.errors),
                    errors=result.errors[:5]  # Log first 5 errors
                )
            
            return result.success_count
        
        except Exception as e:
            self.logger.error(
                "Failed to store events batch",
                event_count=len(events),
                error=str(e)
            )
            
            # Fallback: try inserting events one by one
            success_count = 0
            for event in events:
                try:
                    if self.event_store.insert_event(event):
                        success_count += 1
                except Exception as insert_error:
                    self.logger.error(
                        "Failed to store individual event",
                        event_id=event.event_id,
                        error=str(insert_error)
                    )
            
            return success_count
