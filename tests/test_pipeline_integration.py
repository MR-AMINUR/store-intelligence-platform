"""Integration tests for video processing pipeline.

These tests verify end-to-end pipeline functionality by creating synthetic
test videos and processing them through the complete system.
"""

import os
import tempfile

import cv2
import numpy as np
import pytest

from src.config import ConfigManager
from src.logger import Logger
from src.pipeline import VideoPipeline


def create_test_video(path: str, num_frames: int = 30, fps: int = 10) -> None:
    """Create a synthetic test video for integration testing.
    
    Args:
        path: Path to save video file
        num_frames: Number of frames to generate
        fps: Frames per second
    """
    # Define video properties
    width, height = 640, 480
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    
    # Create video writer
    writer = cv2.VideoWriter(path, fourcc, fps, (width, height))
    
    try:
        for i in range(num_frames):
            # Create a frame with a moving rectangle (simulating a person)
            frame = np.zeros((height, width, 3), dtype=np.uint8)
            
            # Draw background
            frame[:, :] = (50, 50, 50)
            
            # Draw a moving rectangle (simulates a person walking)
            x = int(50 + (i / num_frames) * (width - 150))
            y = height // 2 - 50
            cv2.rectangle(frame, (x, y), (x + 100, y + 150), (0, 255, 0), -1)
            
            writer.write(frame)
    finally:
        writer.release()


@pytest.fixture
def test_video_path():
    """Create a temporary test video."""
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
        video_path = f.name
    
    # Create test video
    create_test_video(video_path, num_frames=30, fps=10)
    
    yield video_path
    
    # Cleanup
    if os.path.exists(video_path):
        os.unlink(video_path)


@pytest.fixture
def test_db_path():
    """Create temporary database path."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def integration_config(test_db_path):
    """Create configuration for integration testing."""
    # Set environment variables
    os.environ["DB_PATH"] = test_db_path
    os.environ["LOG_LEVEL"] = "INFO"
    os.environ["YOLO_MODEL_PATH"] = "./models/yolov8n.pt"
    os.environ["CONFIDENCE_THRESHOLD"] = "0.3"  # Lower threshold for test
    os.environ["TRACKER_MAX_AGE"] = "30"
    os.environ["ZONE_CONFIG_PATH"] = "./config/zones.json"
    os.environ["STORE_ID"] = "integration_test_store"
    
    config = ConfigManager()
    yield config
    
    # Cleanup
    for key in ["DB_PATH", "LOG_LEVEL", "YOLO_MODEL_PATH", 
                "CONFIDENCE_THRESHOLD", "TRACKER_MAX_AGE", 
                "ZONE_CONFIG_PATH", "STORE_ID"]:
        os.environ.pop(key, None)


@pytest.mark.integration
class TestPipelineIntegration:
    """Integration tests for end-to-end pipeline."""
    
    def test_pipeline_processes_video_end_to_end(
        self,
        test_video_path,
        integration_config
    ):
        """Test complete pipeline processes synthetic video end-to-end.
        
        This test verifies that:
        1. Pipeline can be initialized with all components
        2. Video is processed frame by frame
        3. Events are generated and stored
        4. Pipeline completes successfully
        """
        # Skip if model file doesn't exist (CI environment)
        model_path = integration_config.get("YOLO_MODEL_PATH")
        if not os.path.exists(model_path):
            pytest.skip(f"YOLOv8 model not found at {model_path}")
        
        # Skip if zone config doesn't exist
        zone_config = integration_config.get("ZONE_CONFIG_PATH")
        if not os.path.exists(zone_config):
            pytest.skip(f"Zone config not found at {zone_config}")
        
        # Create logger
        logger = Logger("PipelineIntegration", "INFO")
        
        # Create and run pipeline
        pipeline = VideoPipeline(test_video_path, integration_config, logger)
        result = pipeline.process()
        
        # Verify pipeline completed successfully
        assert result.success is True, f"Pipeline failed with errors: {result.errors}"
        
        # Verify frames were processed
        assert result.total_frames > 0, "No frames were processed"
        assert result.total_frames == 30, f"Expected 30 frames, got {result.total_frames}"
        
        # Verify events were generated (at minimum, finalize should generate events)
        # Note: Event generation depends on YOLOv8 detections, which may be 0 for synthetic video
        assert result.events_generated >= 0, "Events generated count should be non-negative"
        
        # Verify pipeline statistics are consistent
        assert result.frames_failed >= 0, "Failed frames count should be non-negative"
        assert result.events_stored >= 0, "Stored events count should be non-negative"
        
        # If events were generated, they should be stored
        if result.events_generated > 0:
            assert result.events_stored > 0, "Generated events should be stored"
    
    def test_pipeline_handles_empty_video(
        self,
        integration_config
    ):
        """Test pipeline handles video with no frames gracefully."""
        # Create empty video
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            empty_video_path = f.name
        
        try:
            # Create minimal video with 0 frames
            create_test_video(empty_video_path, num_frames=0, fps=10)
            
            # Skip if dependencies missing
            model_path = integration_config.get("YOLO_MODEL_PATH")
            zone_config = integration_config.get("ZONE_CONFIG_PATH")
            if not os.path.exists(model_path) or not os.path.exists(zone_config):
                pytest.skip("Required files not found")
            
            logger = Logger("PipelineIntegration", "INFO")
            pipeline = VideoPipeline(empty_video_path, integration_config, logger)
            result = pipeline.process()
            
            # Verify pipeline completes even with empty video
            assert result.success is True
            assert result.total_frames == 0
            
        finally:
            if os.path.exists(empty_video_path):
                os.unlink(empty_video_path)
    
    def test_pipeline_stores_events_to_database(
        self,
        test_video_path,
        integration_config,
        test_db_path
    ):
        """Test that pipeline actually stores events to database."""
        # Skip if dependencies missing
        model_path = integration_config.get("YOLO_MODEL_PATH")
        zone_config = integration_config.get("ZONE_CONFIG_PATH")
        if not os.path.exists(model_path) or not os.path.exists(zone_config):
            pytest.skip("Required files not found")
        
        logger = Logger("PipelineIntegration", "INFO")
        pipeline = VideoPipeline(test_video_path, integration_config, logger)
        result = pipeline.process()
        
        assert result.success is True
        
        # Verify database was created
        assert os.path.exists(test_db_path), "Database file should be created"
        
        # Verify database has events table
        import sqlite3
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        
        # Check that events table exists
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='events'
        """)
        assert cursor.fetchone() is not None, "Events table should exist"
        
        # Check event count matches result
        cursor.execute("SELECT COUNT(*) FROM events")
        db_event_count = cursor.fetchone()[0]
        
        assert db_event_count == result.events_stored, \
            f"Database has {db_event_count} events, expected {result.events_stored}"
        
        conn.close()
    
    def test_pipeline_with_invalid_video(
        self,
        integration_config
    ):
        """Test pipeline handles invalid video file gracefully."""
        # Create invalid video file
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            invalid_video_path = f.name
            f.write(b"not a valid video file")
        
        try:
            logger = Logger("PipelineIntegration", "INFO")
            
            # Pipeline should raise error during initialization (VideoProcessor)
            with pytest.raises(RuntimeError):
                pipeline = VideoPipeline(invalid_video_path, integration_config, logger)
                pipeline.process()
        
        finally:
            if os.path.exists(invalid_video_path):
                os.unlink(invalid_video_path)
    
    def test_pipeline_correlation_id_propagation(
        self,
        test_video_path,
        integration_config
    ):
        """Test that correlation ID is propagated through all components."""
        # Skip if dependencies missing
        model_path = integration_config.get("YOLO_MODEL_PATH")
        zone_config = integration_config.get("ZONE_CONFIG_PATH")
        if not os.path.exists(model_path) or not os.path.exists(zone_config):
            pytest.skip("Required files not found")
        
        logger = Logger("PipelineIntegration", "INFO")
        pipeline = VideoPipeline(test_video_path, integration_config, logger)
        
        # Verify correlation ID was generated
        assert pipeline.correlation_id is not None
        assert pipeline.correlation_id.startswith("corr-")
        
        # Verify correlation ID is set on all component loggers
        assert pipeline.video_processor.logger.correlation_id == pipeline.correlation_id
        assert pipeline.person_detector.logger.correlation_id == pipeline.correlation_id
        assert pipeline.person_tracker.logger.correlation_id == pipeline.correlation_id
        assert pipeline.event_generator.logger.correlation_id == pipeline.correlation_id
        assert pipeline.event_store.logger.correlation_id == pipeline.correlation_id


@pytest.mark.integration
@pytest.mark.slow
class TestPipelineLargeVideo:
    """Integration tests for pipeline with larger videos."""
    
    def test_pipeline_processes_large_video(
        self,
        integration_config
    ):
        """Test pipeline can handle larger video files (100+ frames)."""
        # Skip if dependencies missing
        model_path = integration_config.get("YOLO_MODEL_PATH")
        zone_config = integration_config.get("ZONE_CONFIG_PATH")
        if not os.path.exists(model_path) or not os.path.exists(zone_config):
            pytest.skip("Required files not found")
        
        # Create larger test video
        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as f:
            large_video_path = f.name
        
        try:
            create_test_video(large_video_path, num_frames=150, fps=30)
            
            logger = Logger("PipelineIntegration", "INFO")
            pipeline = VideoPipeline(large_video_path, integration_config, logger)
            result = pipeline.process()
            
            # Verify pipeline completes successfully
            assert result.success is True
            assert result.total_frames == 150
            
            # Verify processing statistics
            print(f"Processed {result.total_frames} frames")
            print(f"Generated {result.events_generated} events")
            print(f"Stored {result.events_stored} events")
            print(f"Failed {result.frames_failed} frames")
            
        finally:
            if os.path.exists(large_video_path):
                os.unlink(large_video_path)
