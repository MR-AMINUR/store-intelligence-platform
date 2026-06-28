"""Main Pipeline Orchestrator for CV Pipeline.

This module provides the main pipeline execution logic and CLI interface.
"""

import argparse
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from pipeline.config import PipelineConfig
from pipeline.detector import PersonDetector
from pipeline.event_generator import Event, EventGenerator
from pipeline.event_sender import EventSender
from pipeline.tracker import PersonTracker
from pipeline.video_processor import VideoProcessor
from pipeline.zone_manager import ZoneManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log'),
    ]
)

logger = logging.getLogger(__name__)


class PipelineStats:
    """Pipeline execution statistics."""
    
    def __init__(self):
        self.start_time = time.time()
        self.frames_processed = 0
        self.frames_failed = 0
        self.detections_total = 0
        self.tracks_total = 0
        self.events_generated = 0
        self.events_sent = 0
        self.events_failed = 0
    
    def get_summary(self) -> dict:
        """Get statistics summary."""
        elapsed = time.time() - self.start_time
        fps = self.frames_processed / elapsed if elapsed > 0 else 0
        
        return {
            "elapsed_seconds": elapsed,
            "frames_processed": self.frames_processed,
            "frames_failed": self.frames_failed,
            "processing_fps": fps,
            "detections_total": self.detections_total,
            "tracks_total": self.tracks_total,
            "events_generated": self.events_generated,
            "events_sent": self.events_sent,
            "events_failed": self.events_failed,
        }


class VideoPipeline:
    """Complete video processing pipeline.
    
    Orchestrates the end-to-end pipeline from video input to event ingestion.
    """
    
    def __init__(self, config: PipelineConfig):
        """Initialize pipeline.
        
        Args:
            config: Pipeline configuration
        """
        self.config = config
        self.stats = PipelineStats()
        
        logger.info("=" * 70)
        logger.info("Initializing Video Processing Pipeline")
        logger.info("=" * 70)
        
        # Initialize components
        logger.info("Loading components...")
        
        self.detector = PersonDetector(
            model_path=config.detector.model_path,
            confidence_threshold=config.detector.confidence_threshold,
            device=config.detector.device,
            batch_size=config.detector.batch_size,
        )
        
        self.tracker = PersonTracker(
            max_age=config.tracker.max_age,
            min_hits=config.tracker.min_hits,
            iou_threshold=config.tracker.iou_threshold,
        )
        
        self.zone_manager = ZoneManager.from_config(config.zone.config_path)
        
        self.event_generator = EventGenerator(
            store_id=config.store_id,
            zone_manager=self.zone_manager,
            dwell_threshold_seconds=config.zone.dwell_threshold_seconds,
            base_timestamp=datetime.now(timezone.utc),
        )
        
        self.event_sender = EventSender(
            base_url=config.api.base_url,
            ingest_endpoint=config.api.ingest_endpoint,
            timeout=config.api.timeout_seconds,
            max_retries=config.api.max_retries,
            retry_delay=config.api.retry_delay_seconds,
            batch_size=config.api.batch_size,
        )
        
        logger.info("Pipeline initialization complete")
    
    def process_video(self, video_path: str) -> bool:
        """Process video file through complete pipeline.
        
        Args:
            video_path: Path to video file
            
        Returns:
            True if processing completed successfully
        """
        logger.info("=" * 70)
        logger.info(f"Processing video: {video_path}")
        logger.info("=" * 70)
        
        try:
            # Check API health
            logger.info("Checking backend API health...")
            if not self.event_sender.health_check():
                logger.error("Backend API health check failed. Exiting.")
                return False
            
            # Initialize video processor
            video_processor = VideoProcessor(
                video_path=video_path,
                frame_skip=self.config.video.frame_skip,
                target_fps=self.config.video.target_fps,
                resize_width=self.config.video.resize_width,
                resize_height=self.config.video.resize_height,
            )
            
            # Get video metadata
            metadata = video_processor.get_metadata()
            logger.info(f"Video metadata: {metadata.to_dict()}")
            
            # Update event generator FPS
            self.event_generator.fps = metadata.fps
            
            # Process frames
            logger.info("Starting frame processing...")
            event_buffer: List[Event] = []
            
            if self.config.replay_timing:
                frame_iterator = video_processor.read_frames_with_timing(replay_timing=True)
            else:
                frame_iterator = video_processor.read_frames()
            
            for frame in frame_iterator:
                try:
                    # 1. Detect people
                    detections = self.detector.detect(frame.image)
                    self.stats.detections_total += len(detections)
                    
                    # 2. Update tracking
                    tracks = self.tracker.update(detections, frame.frame_number)
                    if tracks:
                        self.stats.tracks_total = max(self.stats.tracks_total, len(tracks))
                    
                    # 3. Generate events
                    events = self.event_generator.process_tracks(tracks, frame.frame_number)
                    event_buffer.extend(events)
                    self.stats.events_generated += len(events)
                    
                    # 4. Send events in batches
                    if len(event_buffer) >= self.config.api.batch_size:
                        success = self.event_sender.send_events(event_buffer)
                        if success:
                            self.stats.events_sent += len(event_buffer)
                        else:
                            self.stats.events_failed += len(event_buffer)
                        event_buffer.clear()
                    
                    self.stats.frames_processed += 1
                    
                    # Log progress
                    if self.stats.frames_processed % 100 == 0:
                        self._log_progress()
                    
                except Exception as e:
                    self.stats.frames_failed += 1
                    logger.error(f"Frame {frame.frame_number} processing failed: {e}")
                    continue
            
            # Finalize event generation
            logger.info("Finalizing event generation...")
            final_events = self.event_generator.finalize()
            event_buffer.extend(final_events)
            self.stats.events_generated += len(final_events)
            
            # Send remaining events
            if event_buffer:
                logger.info(f"Sending remaining {len(event_buffer)} events...")
                success = self.event_sender.send_events(event_buffer)
                if success:
                    self.stats.events_sent += len(event_buffer)
                else:
                    self.stats.events_failed += len(event_buffer)
            
            # Log final statistics
            self._log_final_stats()
            
            logger.info("=" * 70)
            logger.info("Pipeline processing complete")
            logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            logger.error(f"Pipeline processing failed: {e}", exc_info=True)
            return False
    
    def _log_progress(self) -> None:
        """Log processing progress."""
        summary = self.stats.get_summary()
        logger.info(
            f"Progress: {summary['frames_processed']} frames | "
            f"{summary['processing_fps']:.1f} FPS | "
            f"{summary['detections_total']} detections | "
            f"{summary['tracks_total']} tracks | "
            f"{summary['events_generated']} events"
        )
    
    def _log_final_stats(self) -> None:
        """Log final statistics."""
        summary = self.stats.get_summary()
        sender_stats = self.event_sender.get_stats()
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("PIPELINE STATISTICS")
        logger.info("=" * 70)
        logger.info(f"Total Time:          {summary['elapsed_seconds']:.2f} seconds")
        logger.info(f"Frames Processed:    {summary['frames_processed']}")
        logger.info(f"Frames Failed:       {summary['frames_failed']}")
        logger.info(f"Processing FPS:      {summary['processing_fps']:.2f}")
        logger.info(f"Total Detections:    {summary['detections_total']}")
        logger.info(f"Max Tracks:          {summary['tracks_total']}")
        logger.info(f"Events Generated:    {summary['events_generated']}")
        logger.info(f"Events Sent:         {sender_stats['events_sent']}")
        logger.info(f"Events Failed:       {sender_stats['events_failed']}")
        logger.info(f"Success Rate:        {sender_stats['success_rate']:.1%}")
        logger.info("=" * 70)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Store Intelligence Platform - Computer Vision Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process video with default config
  python -m pipeline.run_pipeline --video sample.mp4
  
  # Process with custom config file
  python -m pipeline.run_pipeline --video sample.mp4 --config my_config.json
  
  # Process with environment variables
  export API_BASE_URL=http://localhost:8000
  export STORE_ID=store_001
  python -m pipeline.run_pipeline --video sample.mp4
  
  # Process with custom parameters
  python -m pipeline.run_pipeline --video sample.mp4 \\
      --store-id store_002 \\
      --api-url http://localhost:8000 \\
      --confidence 0.6
        """
    )
    
    parser.add_argument(
        '--video',
        type=str,
        required=True,
        help='Path to video file (MP4, AVI, MOV)',
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration JSON file',
    )
    
    parser.add_argument(
        '--store-id',
        type=str,
        help='Store identifier (overrides config)',
    )
    
    parser.add_argument(
        '--api-url',
        type=str,
        help='Backend API URL (overrides config)',
    )
    
    parser.add_argument(
        '--confidence',
        type=float,
        help='Detection confidence threshold [0-1] (overrides config)',
    )
    
    parser.add_argument(
        '--no-replay-timing',
        action='store_true',
        help='Disable timing preservation (process as fast as possible)',
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging',
    )
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger('pipeline').setLevel(logging.DEBUG)
    
    # Load configuration
    if args.config:
        logger.info(f"Loading configuration from {args.config}")
        config = PipelineConfig.from_json(args.config)
    else:
        logger.info("Loading configuration from environment variables")
        config = PipelineConfig.from_env()
    
    # Apply CLI overrides
    if args.store_id:
        config.store_id = args.store_id
    
    if args.api_url:
        config.api.base_url = args.api_url
    
    if args.confidence:
        config.detector.confidence_threshold = args.confidence
    
    if args.no_replay_timing:
        config.replay_timing = False
    
    # Validate configuration
    try:
        config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)
    
    # Verify video file exists
    if not Path(args.video).exists():
        logger.error(f"Video file not found: {args.video}")
        sys.exit(1)
    
    # Initialize and run pipeline
    pipeline = VideoPipeline(config)
    success = pipeline.process_video(args.video)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
