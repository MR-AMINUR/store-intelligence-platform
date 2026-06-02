"""Unit tests for PersonDetector."""

import numpy as np
import pytest
from unittest.mock import Mock, MagicMock, patch

from src.person_detector import PersonDetector
from src.logger import Logger
from src.models import BoundingBox, Detection


@pytest.fixture
def mock_logger():
    """Create a mock logger for testing."""
    logger = Mock(spec=Logger)
    logger.info = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    logger.error = Mock()
    return logger


@pytest.fixture
def mock_yolo_model():
    """Create a mock YOLO model for testing."""
    with patch('src.person_detector.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.to = Mock(return_value=mock_model)
        yield mock_model


class TestPersonDetectorInitialization:
    """Tests for PersonDetector initialization."""
    
    def test_initialization_success(self, mock_logger, mock_yolo_model):
        """Test PersonDetector can be initialized successfully."""
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        assert detector.confidence_threshold == 0.5
        assert detector.logger == mock_logger
        assert detector.device in ['cuda', 'cpu']
        assert detector.model is not None
    
    def test_initialization_with_invalid_confidence_threshold(self, mock_logger):
        """Test PersonDetector raises ValueError for invalid confidence threshold."""
        with pytest.raises(ValueError, match="Confidence threshold must be in"):
            PersonDetector(
                model_path="yolov8n.pt",
                confidence_threshold=1.5,
                logger=mock_logger
            )
        
        with pytest.raises(ValueError, match="Confidence threshold must be in"):
            PersonDetector(
                model_path="yolov8n.pt",
                confidence_threshold=-0.1,
                logger=mock_logger
            )
    
    def test_initialization_logs_device_detection(self, mock_logger, mock_yolo_model):
        """Test PersonDetector logs device detection."""
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Check that device detection was logged
        mock_logger.info.assert_any_call("Device detected", device=detector.device)
    
    def test_initialization_logs_model_loading(self, mock_logger, mock_yolo_model):
        """Test PersonDetector logs model loading."""
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Check that model loading was logged
        mock_logger.info.assert_any_call(
            "Loading YOLOv8 model",
            model_path="yolov8n.pt",
            device=detector.device
        )
        mock_logger.info.assert_any_call(
            "YOLOv8 model loaded successfully",
            model_path="yolov8n.pt",
            device=detector.device,
            confidence_threshold=0.5
        )
    
    def test_initialization_with_model_file_not_found(self, mock_logger):
        """Test PersonDetector raises FileNotFoundError for missing model file."""
        with patch('src.person_detector.YOLO') as mock_yolo_class:
            mock_yolo_class.side_effect = FileNotFoundError("Model file not found")
            
            with pytest.raises(FileNotFoundError):
                PersonDetector(
                    model_path="nonexistent.pt",
                    confidence_threshold=0.5,
                    logger=mock_logger
                )
            
            # Check that error was logged
            mock_logger.error.assert_called()
    
    def test_initialization_with_model_loading_failure(self, mock_logger):
        """Test PersonDetector raises RuntimeError for model loading failure."""
        with patch('src.person_detector.YOLO') as mock_yolo_class:
            mock_yolo_class.side_effect = Exception("Failed to load model")
            
            with pytest.raises(RuntimeError, match="Failed to load YOLOv8 model"):
                PersonDetector(
                    model_path="invalid.pt",
                    confidence_threshold=0.5,
                    logger=mock_logger
                )
            
            # Check that error was logged
            mock_logger.error.assert_called()
    
    def test_device_selection_cpu(self, mock_logger, mock_yolo_model):
        """Test PersonDetector selects CPU when CUDA is not available."""
        with patch('src.person_detector.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = False
            
            detector = PersonDetector(
                model_path="yolov8n.pt",
                confidence_threshold=0.5,
                logger=mock_logger
            )
            
            assert detector.device == "cpu"
    
    def test_device_selection_cuda(self, mock_logger, mock_yolo_model):
        """Test PersonDetector selects CUDA when available."""
        with patch('src.person_detector.torch') as mock_torch:
            mock_torch.cuda.is_available.return_value = True
            
            detector = PersonDetector(
                model_path="yolov8n.pt",
                confidence_threshold=0.5,
                logger=mock_logger
            )
            
            assert detector.device == "cuda"


class TestPersonDetectorDetection:
    """Tests for PersonDetector.detect() method."""
    
    def test_detect_with_valid_frame(self, mock_logger, mock_yolo_model):
        """Test detect() returns detections for valid frame."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock detection result
        mock_box = MagicMock()
        mock_box.conf = [0.85]
        mock_box.cls = [0]  # person class
        mock_box.xyxy = [np.array([100.0, 200.0, 150.0, 280.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify results
        assert len(detections) == 1
        assert detections[0].confidence == 0.85
        assert detections[0].class_id == 0
        assert detections[0].bbox.x == 100.0
        assert detections[0].bbox.y == 200.0
        assert detections[0].bbox.width == 50.0
        assert detections[0].bbox.height == 80.0
    
    def test_detect_filters_low_confidence_detections(self, mock_logger, mock_yolo_model):
        """Test detect() filters detections below confidence threshold."""
        # Create detector with threshold 0.7
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.7,
            logger=mock_logger
        )
        
        # Create mock detection results with varying confidence
        mock_box1 = MagicMock()
        mock_box1.conf = [0.85]  # Above threshold
        mock_box1.cls = [0]
        mock_box1.xyxy = [np.array([100.0, 200.0, 150.0, 280.0])]
        
        mock_box2 = MagicMock()
        mock_box2.conf = [0.45]  # Below threshold
        mock_box2.cls = [0]
        mock_box2.xyxy = [np.array([300.0, 400.0, 350.0, 480.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify only high-confidence detection is returned
        assert len(detections) == 1
        assert detections[0].confidence == 0.85
    
    def test_detect_filters_non_person_classes(self, mock_logger, mock_yolo_model):
        """Test detect() filters detections that are not person class (class_id != 0)."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock detection results with different classes
        mock_box1 = MagicMock()
        mock_box1.conf = [0.85]
        mock_box1.cls = [0]  # person class
        mock_box1.xyxy = [np.array([100.0, 200.0, 150.0, 280.0])]
        
        mock_box2 = MagicMock()
        mock_box2.conf = [0.90]
        mock_box2.cls = [2]  # car class (not person)
        mock_box2.xyxy = [np.array([300.0, 400.0, 350.0, 480.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify only person detection is returned
        assert len(detections) == 1
        assert detections[0].class_id == 0
    
    def test_detect_with_multiple_detections(self, mock_logger, mock_yolo_model):
        """Test detect() returns multiple detections correctly."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock detection results with multiple people
        mock_box1 = MagicMock()
        mock_box1.conf = [0.85]
        mock_box1.cls = [0]
        mock_box1.xyxy = [np.array([100.0, 200.0, 150.0, 280.0])]
        
        mock_box2 = MagicMock()
        mock_box2.conf = [0.75]
        mock_box2.cls = [0]
        mock_box2.xyxy = [np.array([300.0, 400.0, 350.0, 480.0])]
        
        mock_box3 = MagicMock()
        mock_box3.conf = [0.92]
        mock_box3.cls = [0]
        mock_box3.xyxy = [np.array([500.0, 100.0, 580.0, 250.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box1, mock_box2, mock_box3]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify all detections are returned
        assert len(detections) == 3
        assert detections[0].confidence == 0.85
        assert detections[1].confidence == 0.75
        assert detections[2].confidence == 0.92
    
    def test_detect_with_no_detections(self, mock_logger, mock_yolo_model):
        """Test detect() returns empty list when no people detected."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock result with no boxes
        mock_result = MagicMock()
        mock_result.boxes = []
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify empty list is returned
        assert len(detections) == 0
    
    def test_detect_with_none_frame(self, mock_logger, mock_yolo_model):
        """Test detect() handles None frame gracefully."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Run detection with None frame
        detections = detector.detect(None)
        
        # Verify empty list is returned and warning is logged
        assert len(detections) == 0
        mock_logger.warning.assert_called()
    
    def test_detect_with_empty_frame(self, mock_logger, mock_yolo_model):
        """Test detect() handles empty frame gracefully."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create empty frame
        frame = np.array([])
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify empty list is returned and warning is logged
        assert len(detections) == 0
        mock_logger.warning.assert_called()
    
    def test_detect_logs_detection_count(self, mock_logger, mock_yolo_model):
        """Test detect() logs detection count."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock detection result
        mock_box = MagicMock()
        mock_box.conf = [0.85]
        mock_box.cls = [0]
        mock_box.xyxy = [np.array([100.0, 200.0, 150.0, 280.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify logging
        mock_logger.debug.assert_called_with(
            "Detection complete",
            detections_count=1,
            frame_shape=(480, 640, 3)
        )
    
    def test_detect_handles_inference_failure(self, mock_logger, mock_yolo_model):
        """Test detect() handles inference failure gracefully."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Make model inference raise exception
        mock_yolo_model.side_effect = Exception("Inference failed")
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify empty list is returned and error is logged
        assert len(detections) == 0
        mock_logger.error.assert_called()
    
    def test_detect_bounding_box_conversion(self, mock_logger, mock_yolo_model):
        """Test detect() converts bounding box from xyxy to xywh format."""
        # Create detector
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=0.5,
            logger=mock_logger
        )
        
        # Create mock detection with specific coordinates
        # xyxy: (100, 200, 250, 350)
        # Expected xywh: x=100, y=200, w=150, h=150
        mock_box = MagicMock()
        mock_box.conf = [0.85]
        mock_box.cls = [0]
        mock_box.xyxy = [np.array([100.0, 200.0, 250.0, 350.0])]
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        
        mock_yolo_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Verify bounding box conversion
        assert len(detections) == 1
        assert detections[0].bbox.x == 100.0
        assert detections[0].bbox.y == 200.0
        assert detections[0].bbox.width == 150.0
        assert detections[0].bbox.height == 150.0
