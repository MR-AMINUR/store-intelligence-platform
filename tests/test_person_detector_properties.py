"""Property-based tests for PersonDetector using Hypothesis.

This module contains property tests that validate universal correctness
properties of the PersonDetector, specifically confidence filtering and
detection structure validity.
"""

import numpy as np
from hypothesis import given, strategies as st, settings, assume
from unittest.mock import MagicMock, patch

from src.person_detector import PersonDetector
from src.logger import Logger
from src.models import Detection


# Strategy for generating valid confidence scores
confidence_scores = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)

# Strategy for generating frame shapes
frame_shapes = st.tuples(
    st.integers(min_value=1, max_value=1080),  # height
    st.integers(min_value=1, max_value=1920),  # width
    st.just(3)  # channels (BGR)
)


def create_mock_detection_box(confidence: float, class_id: int, x1: float, y1: float, x2: float, y2: float):
    """Helper to create a mock YOLOv8 detection box."""
    mock_box = MagicMock()
    mock_box.conf = [confidence]
    mock_box.cls = [class_id]
    mock_box.xyxy = [np.array([x1, y1, x2, y2])]
    return mock_box


# Property 6: Detection Confidence Filtering
# **Validates: Requirements 2.4**
@settings(max_examples=50)
@given(
    threshold=confidence_scores,
    detection_confidences=st.lists(
        confidence_scores,
        min_size=1,
        max_size=20
    ),
    frame_shape=frame_shapes
)
def test_property_confidence_filtering(threshold, detection_confidences, frame_shape):
    """
    Property 6: Detection Confidence Filtering
    
    For ANY confidence threshold and ANY set of detections, the detector SHALL
    exclude all detections with confidence scores below the configured threshold.
    
    This property validates Requirement 2.4:
    - WHEN confidence score is below the threshold, THE Person_Detector SHALL exclude the detection
    """
    # Create mock logger
    mock_logger = MagicMock(spec=Logger)
    
    # Create PersonDetector with mocked YOLO model
    with patch('src.person_detector.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.to = MagicMock(return_value=mock_model)
        
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=threshold,
            logger=mock_logger
        )
        
        # Create mock detection results
        mock_boxes = []
        for i, conf in enumerate(detection_confidences):
            # Create bounding box coordinates
            x1, y1, x2, y2 = 100.0 + i * 50, 100.0, 150.0 + i * 50, 200.0
            mock_box = create_mock_detection_box(conf, 0, x1, y1, x2, y2)
            mock_boxes.append(mock_box)
        
        mock_result = MagicMock()
        mock_result.boxes = mock_boxes
        mock_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros(frame_shape, dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Property 1: All returned detections must have confidence >= threshold
        for detection in detections:
            assert detection.confidence >= threshold, \
                f"Detection with confidence {detection.confidence} should be filtered (threshold={threshold})"
        
        # Property 2: The number of detections should match expected count
        expected_count = sum(1 for conf in detection_confidences if conf >= threshold)
        assert len(detections) == expected_count, \
            f"Expected {expected_count} detections, got {len(detections)} (threshold={threshold})"
        
        # Property 3: All detections below threshold must be excluded
        for conf in detection_confidences:
            if conf < threshold:
                # Verify this confidence is not in the results
                assert conf not in [d.confidence for d in detections], \
                    f"Detection with confidence {conf} should be filtered (threshold={threshold})"
        
        # Property 4: All detections above threshold must be included
        for conf in detection_confidences:
            if conf >= threshold:
                # Verify this confidence is in the results
                assert conf in [d.confidence for d in detections], \
                    f"Detection with confidence {conf} should be included (threshold={threshold})"


# Property 7: Detection Structure Validity
# **Validates: Requirements 2.2, 2.3**
@settings(max_examples=50)
@given(
    threshold=confidence_scores,
    num_detections=st.integers(min_value=1, max_value=10),
    frame_shape=frame_shapes
)
def test_property_detection_structure_validity(threshold, num_detections, frame_shape):
    """
    Property 7: Detection Structure Validity
    
    For ANY detection returned by the Person_Detector, the detection SHALL include:
    1. A complete bounding box with x, y, width, height
    2. A confidence score in the range [0, 1]
    3. A class_id (person = 0)
    4. All numeric fields with valid (non-NaN, non-infinite) values
    
    This property validates Requirements 2.2, 2.3:
    - 2.2: THE Person_Detector SHALL return bounding box coordinates (x, y, width, height)
    - 2.3: THE Person_Detector SHALL return confidence scores for each detection
    """
    # Create mock logger
    mock_logger = MagicMock(spec=Logger)
    
    # Create PersonDetector with mocked YOLO model
    with patch('src.person_detector.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.to = MagicMock(return_value=mock_model)
        
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=threshold,
            logger=mock_logger
        )
        
        # Create mock detection results with valid confidences (above threshold)
        mock_boxes = []
        for i in range(num_detections):
            # Ensure confidence is above threshold
            conf = threshold + (1.0 - threshold) * (i + 1) / (num_detections + 1)
            x1, y1, x2, y2 = 100.0 + i * 60, 50.0 + i * 30, 180.0 + i * 60, 150.0 + i * 30
            
            # Ensure x2 > x1 and y2 > y1 for valid bounding boxes
            assume(x2 > x1 and y2 > y1)
            
            mock_box = create_mock_detection_box(conf, 0, x1, y1, x2, y2)
            mock_boxes.append(mock_box)
        
        mock_result = MagicMock()
        mock_result.boxes = mock_boxes
        mock_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros(frame_shape, dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Property 1: All detections must have valid Detection structure
        for detection in detections:
            assert isinstance(detection, Detection), \
                f"Detection must be a Detection instance, got {type(detection)}"
        
        # Property 2: All detections must have complete bounding box
        for detection in detections:
            assert hasattr(detection, 'bbox'), "Detection must have bbox attribute"
            assert hasattr(detection.bbox, 'x'), "BoundingBox must have x coordinate"
            assert hasattr(detection.bbox, 'y'), "BoundingBox must have y coordinate"
            assert hasattr(detection.bbox, 'width'), "BoundingBox must have width"
            assert hasattr(detection.bbox, 'height'), "BoundingBox must have height"
        
        # Property 3: All bounding box coordinates must be valid numbers
        for detection in detections:
            assert not np.isnan(detection.bbox.x), "BoundingBox x must not be NaN"
            assert not np.isnan(detection.bbox.y), "BoundingBox y must not be NaN"
            assert not np.isnan(detection.bbox.width), "BoundingBox width must not be NaN"
            assert not np.isnan(detection.bbox.height), "BoundingBox height must not be NaN"
            
            assert not np.isinf(detection.bbox.x), "BoundingBox x must not be infinite"
            assert not np.isinf(detection.bbox.y), "BoundingBox y must not be infinite"
            assert not np.isinf(detection.bbox.width), "BoundingBox width must not be infinite"
            assert not np.isinf(detection.bbox.height), "BoundingBox height must not be infinite"
        
        # Property 4: All bounding boxes must have positive width and height
        for detection in detections:
            assert detection.bbox.width > 0, \
                f"BoundingBox width must be positive, got {detection.bbox.width}"
            assert detection.bbox.height > 0, \
                f"BoundingBox height must be positive, got {detection.bbox.height}"
        
        # Property 5: All detections must have confidence in [0, 1]
        for detection in detections:
            assert hasattr(detection, 'confidence'), "Detection must have confidence attribute"
            assert 0.0 <= detection.confidence <= 1.0, \
                f"Confidence must be in [0, 1], got {detection.confidence}"
            assert not np.isnan(detection.confidence), "Confidence must not be NaN"
            assert not np.isinf(detection.confidence), "Confidence must not be infinite"
        
        # Property 6: All detections must have class_id = 0 (person)
        for detection in detections:
            assert hasattr(detection, 'class_id'), "Detection must have class_id attribute"
            assert detection.class_id == 0, \
                f"Person detections must have class_id=0, got {detection.class_id}"
        
        # Property 7: Bounding box coordinates must be non-negative
        for detection in detections:
            assert detection.bbox.x >= 0, f"BoundingBox x must be non-negative, got {detection.bbox.x}"
            assert detection.bbox.y >= 0, f"BoundingBox y must be non-negative, got {detection.bbox.y}"
        
        # Property 8: Number of detections must match expected count (all above threshold)
        assert len(detections) == num_detections, \
            f"Expected {num_detections} detections, got {len(detections)}"


# Additional Property: Confidence Threshold Boundary
@settings(max_examples=50)
@given(
    threshold=confidence_scores,
    frame_shape=frame_shapes
)
def test_property_confidence_threshold_boundary(threshold, frame_shape):
    """
    Property: Confidence Threshold Boundary
    
    For ANY confidence threshold, detections with confidence EXACTLY equal to
    the threshold SHALL be included in the results.
    
    This validates the boundary condition of the confidence filtering requirement.
    """
    # Create mock logger
    mock_logger = MagicMock(spec=Logger)
    
    # Create PersonDetector with mocked YOLO model
    with patch('src.person_detector.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.to = MagicMock(return_value=mock_model)
        
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=threshold,
            logger=mock_logger
        )
        
        # Create mock detection with confidence exactly equal to threshold
        mock_box = create_mock_detection_box(threshold, 0, 100.0, 100.0, 200.0, 200.0)
        
        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros(frame_shape, dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Property: Detection with confidence equal to threshold must be included
        assert len(detections) == 1, \
            f"Detection with confidence={threshold} (equal to threshold) should be included"
        assert detections[0].confidence == threshold, \
            f"Detection confidence should match threshold: {threshold}"


# Additional Property: Non-Person Class Filtering
@settings(max_examples=50)
@given(
    threshold=confidence_scores,
    class_ids=st.lists(
        st.integers(min_value=0, max_value=79),  # YOLOv8 has 80 classes (0-79)
        min_size=1,
        max_size=10
    ),
    frame_shape=frame_shapes
)
def test_property_non_person_class_filtering(threshold, class_ids, frame_shape):
    """
    Property: Non-Person Class Filtering
    
    For ANY set of detections with different class IDs, ONLY detections with
    class_id = 0 (person) SHALL be returned, regardless of confidence score.
    
    This validates Requirement 2.1: THE Person_Detector SHALL detect people
    (not other object classes).
    """
    # Create mock logger
    mock_logger = MagicMock(spec=Logger)
    
    # Create PersonDetector with mocked YOLO model
    with patch('src.person_detector.YOLO') as mock_yolo_class:
        mock_model = MagicMock()
        mock_yolo_class.return_value = mock_model
        mock_model.to = MagicMock(return_value=mock_model)
        
        detector = PersonDetector(
            model_path="yolov8n.pt",
            confidence_threshold=threshold,
            logger=mock_logger
        )
        
        # Create mock detection results with different class IDs
        # All with high confidence to ensure they would pass confidence filter
        high_confidence = max(threshold, 0.9)
        mock_boxes = []
        for i, class_id in enumerate(class_ids):
            x1, y1, x2, y2 = 100.0 + i * 50, 100.0, 150.0 + i * 50, 200.0
            mock_box = create_mock_detection_box(high_confidence, class_id, x1, y1, x2, y2)
            mock_boxes.append(mock_box)
        
        mock_result = MagicMock()
        mock_result.boxes = mock_boxes
        mock_model.return_value = [mock_result]
        
        # Create test frame
        frame = np.zeros(frame_shape, dtype=np.uint8)
        
        # Run detection
        detections = detector.detect(frame)
        
        # Property 1: All returned detections must have class_id = 0
        for detection in detections:
            assert detection.class_id == 0, \
                f"Only person detections (class_id=0) should be returned, got class_id={detection.class_id}"
        
        # Property 2: Number of detections should match number of person class (0) detections
        expected_count = sum(1 for class_id in class_ids if class_id == 0)
        assert len(detections) == expected_count, \
            f"Expected {expected_count} person detections, got {len(detections)}"
        
        # Property 3: All non-person classes must be excluded
        for class_id in class_ids:
            if class_id != 0:
                # Verify no detections with this class_id in results
                assert class_id not in [d.class_id for d in detections], \
                    f"Non-person class {class_id} should be filtered out"
