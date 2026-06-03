#!/usr/bin/env python
"""Command-line interface entry points for Store Intelligence Platform.

This module provides CLI commands for video processing and API server operations.

Commands:
    - process_video: Process video files through the detection/tracking/event pipeline
    - start_api_server: Start the FastAPI REST API server

Usage:
    store-intelligence-process --video path/to/video.mp4 [--config path/to/.env]
    store-intelligence-api [--config path/to/.env] [--host 0.0.0.0] [--port 8000]
"""

import argparse
import sys
from pathlib import Path
from typing import Optional

import uvicorn
from dotenv import load_dotenv

from src.config import ConfigManager
from src.logger import Logger
from src.pipeline import VideoPipeline


def process_video() -> None:
    """CLI entry point for video processing pipeline.
    
    Accepts video_path and optional config_path as arguments, initializes
    the logger and configuration, runs the video processing pipeline, and
    prints summary statistics.
    
    **Validates: Requirements 1.1**
    
    Exit codes:
        0: Success
        1: Error (file not found, pipeline failure, etc.)
    """
    parser = argparse.ArgumentParser(
        prog="store-intelligence-process",
        description="Process video through Store Intelligence Platform pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process a video file with default configuration
  store-intelligence-process --video store_footage.mp4
  
  # Process with custom configuration file
  store-intelligence-process --video store_footage.mp4 --config .env.production
  
  # Enable debug logging
  store-intelligence-process --video store_footage.mp4 --log-level DEBUG
        """
    )
    
    parser.add_argument(
        "--video",
        required=True,
        metavar="PATH",
        help="Path to video file to process (MP4, AVI, MOV)"
    )
    
    parser.add_argument(
        "--config",
        metavar="PATH",
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
        sys.exit(1)
    
    # Validate video format
    supported_formats = [".mp4", ".avi", ".mov"]
    if video_path.suffix.lower() not in supported_formats:
        print(
            f"Error: Unsupported video format '{video_path.suffix}'. "
            f"Supported formats: {', '.join(supported_formats)}",
            file=sys.stderr
        )
        sys.exit(1)
    
    # Load configuration
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        # Load configuration from file by setting environment variables
        load_dotenv(config_path)
    
    try:
        # Initialize configuration manager
        config = ConfigManager()
        
        # Override log level if specified
        import os
        if args.log_level:
            os.environ["LOG_LEVEL"] = args.log_level
        
        # Initialize logger
        logger = Logger(component="CLI", log_level=args.log_level)
        
        logger.info(
            "Starting video processing",
            video_path=str(video_path),
            log_level=args.log_level
        )
        
        # Initialize and run pipeline
        pipeline = VideoPipeline(
            video_path=str(video_path),
            config=config,
            logger=logger
        )
        
        result = pipeline.process()
        
        # Print summary statistics
        print("\n" + "=" * 70)
        print("VIDEO PROCESSING SUMMARY")
        print("=" * 70)
        print(f"Video File:       {video_path.name}")
        print(f"Status:           {'✓ SUCCESS' if result.success else '✗ FAILED'}")
        print(f"Total Frames:     {result.total_frames}")
        print(f"Failed Frames:    {result.frames_failed}")
        print(f"Events Generated: {result.events_generated}")
        print(f"Events Stored:    {result.events_stored}")
        
        if result.errors:
            print(f"\nErrors Encountered: {len(result.errors)}")
            for i, error in enumerate(result.errors[:5], 1):
                print(f"  {i}. {error}")
            if len(result.errors) > 5:
                print(f"  ... and {len(result.errors) - 5} more errors")
        
        print("=" * 70 + "\n")
        
        logger.info(
            "Video processing complete",
            success=result.success,
            total_frames=result.total_frames,
            events_generated=result.events_generated,
            events_stored=result.events_stored
        )
        
        sys.exit(0 if result.success else 1)
    
    except KeyboardInterrupt:
        print("\n\nInterrupted by user", file=sys.stderr)
        sys.exit(130)
    
    except Exception as e:
        print(f"Error: Pipeline failed with exception: {e}", file=sys.stderr)
        sys.exit(1)


def start_api_server() -> None:
    """CLI entry point for starting the FastAPI API server.
    
    Accepts optional config_path, host, and port arguments, initializes
    the logger and configuration, and starts the FastAPI server using uvicorn.
    
    **Validates: Requirements 10.1**
    
    Exit codes:
        0: Success (server shut down gracefully)
        1: Error (configuration error, server startup failure, etc.)
    """
    parser = argparse.ArgumentParser(
        prog="store-intelligence-api",
        description="Start Store Intelligence Platform REST API server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start API server with default settings (0.0.0.0:8000)
  store-intelligence-api
  
  # Start with custom host and port
  store-intelligence-api --host 127.0.0.1 --port 5000
  
  # Start with custom configuration file
  store-intelligence-api --config .env.production
  
  # Enable auto-reload for development
  store-intelligence-api --reload
        """
    )
    
    parser.add_argument(
        "--config",
        metavar="PATH",
        help="Path to configuration file (uses environment variables if not specified)"
    )
    
    parser.add_argument(
        "--host",
        default=None,
        metavar="HOST",
        help="Server host address (default: from config or 0.0.0.0)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        metavar="PORT",
        help="Server port (default: from config or 8000)"
    )
    
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (not for production)"
    )
    
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        metavar="N",
        help="Number of worker processes (default: 1)"
    )
    
    args = parser.parse_args()
    
    # Load configuration from file if specified
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            print(f"Error: Configuration file not found: {args.config}", file=sys.stderr)
            sys.exit(1)
        # Load configuration from file by setting environment variables
        load_dotenv(config_path)
    
    try:
        # Initialize configuration manager
        config = ConfigManager()
        
        # Override configuration with CLI arguments
        import os
        if args.log_level:
            os.environ["LOG_LEVEL"] = args.log_level
        
        # Initialize logger
        logger = Logger(component="API_CLI", log_level=args.log_level)
        
        # Get host and port from CLI args or config
        host = args.host if args.host is not None else config.get("API_HOST", "0.0.0.0")
        port = args.port if args.port is not None else config.get("API_PORT", 8000)
        
        # Validate port range
        if not (1 <= port <= 65535):
            print(f"Error: Invalid port number {port}. Must be between 1 and 65535.", file=sys.stderr)
            sys.exit(1)
        
        logger.info(
            "Starting API server",
            host=host,
            port=port,
            log_level=args.log_level,
            reload=args.reload,
            workers=args.workers
        )
        
        print("\n" + "=" * 70)
        print("STORE INTELLIGENCE PLATFORM API SERVER")
        print("=" * 70)
        print(f"Host:        {host}")
        print(f"Port:        {port}")
        print(f"Log Level:   {args.log_level}")
        print(f"Reload:      {'Enabled' if args.reload else 'Disabled'}")
        print(f"Workers:     {args.workers}")
        print(f"Database:    {config.get('DB_PATH', 'data/events.db')}")
        print("=" * 70)
        print(f"\nAPI Documentation: http://{host if host != '0.0.0.0' else 'localhost'}:{port}/docs")
        print(f"Health Check:      http://{host if host != '0.0.0.0' else 'localhost'}:{port}/health")
        print("\nPress CTRL+C to stop the server\n")
        
        # Start FastAPI server with uvicorn
        uvicorn.run(
            "src.api_server:app",
            host=host,
            port=port,
            log_level=args.log_level.lower(),
            reload=args.reload,
            workers=args.workers if not args.reload else 1,  # Reload mode requires workers=1
            access_log=True
        )
        
        logger.info("API server shut down")
        sys.exit(0)
    
    except KeyboardInterrupt:
        print("\n\nServer stopped by user", file=sys.stderr)
        sys.exit(0)
    
    except Exception as e:
        print(f"Error: Failed to start API server: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # When run directly, show usage information
    print("Store Intelligence Platform CLI")
    print("\nAvailable commands:")
    print("  store-intelligence-process  - Process video files")
    print("  store-intelligence-api      - Start API server")
    print("\nRun with --help for more information:")
    print("  store-intelligence-process --help")
    print("  store-intelligence-api --help")
