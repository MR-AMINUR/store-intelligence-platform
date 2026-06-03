#!/usr/bin/env python
"""Command-line interface for video processing pipeline.

This script provides a simple CLI to process video files through the
Store Intelligence Platform pipeline.

Usage:
    python process_video.py --video path/to/video.mp4
    python process_video.py --video path/to/video.mp4 --config path/to/.env
"""

import argparse
import sys
from pathlib import Path

from src.config import ConfigManager
from src.logger import Logger
from src.pipeline import VideoPipeline


def main():
    """Main entry point for video processing CLI."""
    parser = argparse.ArgumentParser(
        description="Process video through Store Intelligence Platform pipeline"
    )
    parser.add_argument(
        "--video",
        required=True,
        help="Path to video file to process"
    )
    parser.add_argument(
        "--config",
        help="Path to configuration file (uses environment variables if not specified)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Validate video file exists
    video_path = Path(args.video)
    if not video_path.exists():
        print(f"Error: Video file not found: {args.video}", file=sys.stderr)
        return 1
    
    # Load configuration
    if args.config:
        # TODO: Load from config file
        print(f"Warning: Config file support not yet implemented, using environment variables")
    
    try:
        config = ConfigManager()
        
        # Override log level if specified
        if args.log_level:
            import os
            os.environ["LOG_LEVEL"] = args.log_level
        
        # Create logger
        logger = Logger("CLI", args.log_level)
        
        logger.info(
            "Starting video processing",
            video_path=str(video_path)
        )
        
        # Create and run pipeline
        pipeline = VideoPipeline(str(video_path), config, logger)
        result = pipeline.process()
        
        # Print results
        print("\n" + "="*60)
        print("Pipeline Processing Complete")
        print("="*60)
        print(f"Status: {'SUCCESS' if result.success else 'FAILED'}")
        print(f"Total Frames: {result.total_frames}")
        print(f"Failed Frames: {result.frames_failed}")
        print(f"Events Generated: {result.events_generated}")
        print(f"Events Stored: {result.events_stored}")
        
        if result.errors:
            print(f"\nErrors encountered: {len(result.errors)}")
            for i, error in enumerate(result.errors[:5], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")
        
        print("="*60 + "\n")
        
        logger.info(
            "Video processing complete",
            success=result.success,
            total_frames=result.total_frames,
            events_generated=result.events_generated
        )
        
        return 0 if result.success else 1
    
    except Exception as e:
        print(f"Error: Pipeline failed with exception: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
