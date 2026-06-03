"""Person detection module using YOLOv8.

This module provides the PersonDetector class that uses YOLOv8 for detecting
people in video frames. It supports GPU acceleration with automatic CPU fallback
and configurable confidence thresholds.
"""

from typing import List

import numpy as np
import torch
from ultralytics import YOLO

from src.logger import Logger
from src.models import BoundingBox, Detection


class PersonDetector:
    """Person detector using YOLOv8.
    
    This class wraps the YOLOv8 model to detect people in video frames.
    It automatically detects GPU availability and falls back to CPU if needed.
    Detections are filtered by confidence threshold and class ID (person = 0).
    
    Attributes:
        model: YOLOv8 model instance
        confidence_threshold: Minimum confidence score for detections
        logger: Logger instance for structured logging
        device: Device being used ('cuda' or 'cpu')
    
    Example:
        >>> detector = PersonDetector("yolov8n.pt", 0.5, logger)
        >>> detections = detector.detect(frame)
        >>> print(f"Found {len(detections)} people")
    """
    
    def __init__(
        self,
        model_path: str,
        confidence_threshold: float,
        logger: Logger
    ):
        """Initialize PersonDetector with YOLOv8 model.
        
        Args:
            model_path: Path to YOLOv8 model weights file
            confidence_threshold: Minimum confidence score [0, 1] for detections
            logger: Logger instance for structured logging
        
        Raises:
            FileNotFoundError: If model_path does not exist
            ValueError: If confidence_threshold is not in [0, 1]
            RuntimeError: If model fails to load
        """
        self.logger = logger
        self.confidence_threshold = confidence_threshold
        
        # Validate confidence threshold
        if not 0 <= confidence_threshold <= 1:
            error_msg = f"Confidence threshold must be in [0, 1], got {confidence_threshold}"
            self.logger.error("Invalid confidence threshold", threshold=confidence_threshold)
            raise ValueError(error_msg)
        
        # Detect device (GPU or CPU)
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.logger.info("Device detected", device=self.device)
        
        try:
            # Load YOLOv8 model
            self.logger.info("Loading YOLOv8 model", model_path=model_path, device=self.device)
            
            # Patch ultralytics torch_safe_load for PyTorch 2.6+ compatibility
            # PyTorch 2.6 changed torch.load to use weights_only=True by default
            # which breaks YOLOv8 model loading. We monkey-patch to use weights_only=False.
            try:
                import ultralytics.nn.tasks as tasks_module
                original_load = torch.load
                
                def patched_load(f: Any, *args: Any, **kwargs: Any) -> Any:
                    # Force weights_only=False for YOLOv8 model loading
                    kwargs['weights_only'] = False
                    return original_load(f, *args, **kwargs)
                
                # Temporarily replace torch.load
                torch.load = patched_load
                self.model = YOLO(model_path)
                # Restore original torch.load
                torch.load = original_load
            except Exception as patch_error:
                # Fallback: try loading without patch
                self.logger.warning("Failed to patch torch.load, trying direct load", error=str(patch_error))
                self.model = YOLO(model_path)
            
            # Move model to device
            self.model.to(self.device)
            
            self.logger.info(
                "YOLOv8 model loaded successfully",
                model_path=model_path,
                device=self.device,
                confidence_threshold=confidence_threshold
            )
        except FileNotFoundError as e:
            self.logger.error("Model file not found", model_path=model_path, error=str(e))
            raise
        except Exception as e:
            self.logger.error("Failed to load YOLOv8 model", model_path=model_path, error=str(e))
            raise RuntimeError(f"Failed to load YOLOv8 model: {e}") from e
    
    def detect(self, frame: np.ndarray) -> List[Detection]:
        """Detect people in a video frame.
        
        Runs YOLOv8 inference on the input frame and returns detections of people
        (class_id = 0) that meet the confidence threshold.
        
        Args:
            frame: Video frame as numpy array in HxWx3 BGR format (OpenCV format)
        
        Returns:
            List of Detection objects containing bounding boxes and confidence scores
            for all detected people. Returns empty list if no people detected or
            if inference fails.
        
        Example:
            >>> frame = cv2.imread("frame.jpg")
            >>> detections = detector.detect(frame)
            >>> for det in detections:
            ...     print(f"Person at ({det.bbox.x}, {det.bbox.y}) with confidence {det.confidence}")
        """
        if frame is None or frame.size == 0:
            self.logger.warning("Invalid frame provided", frame_shape=None if frame is None else frame.shape)
            return []
        
        try:
            # Run YOLOv8 inference
            # verbose=False to suppress YOLOv8 output
            results = self.model(frame, verbose=False, device=self.device)
            
            # Extract detections
            detections: List[Detection] = []
            
            # YOLOv8 returns a list of Results objects (one per image)
            # We only process the first result since we pass a single frame
            if len(results) > 0:
                result = results[0]
                
                # Get boxes, confidences, and class IDs
                boxes = result.boxes
                
                for box in boxes:
                    # Extract confidence, class_id, and coordinates
                    confidence = float(box.conf[0])
                    class_id = int(box.cls[0])
                    
                    # Filter by confidence threshold and person class (class_id = 0)
                    if confidence >= self.confidence_threshold and class_id == 0:
                        # Extract bounding box coordinates (xyxy format)
                        x1, y1, x2, y2 = box.xyxy[0].tolist()
                        
                        # Convert to (x, y, width, height) format
                        bbox = BoundingBox(
                            x=float(x1),
                            y=float(y1),
                            width=float(x2 - x1),
                            height=float(y2 - y1)
                        )
                        
                        detection = Detection(
                            bbox=bbox,
                            confidence=confidence,
                            class_id=class_id
                        )
                        detections.append(detection)
            
            self.logger.debug(
                "Detection complete",
                detections_count=len(detections),
                frame_shape=frame.shape
            )
            
            return detections
            
        except Exception as e:
            self.logger.error(
                "Detection failed",
                error=str(e),
                frame_shape=frame.shape
            )
            # Return empty list on failure to allow processing to continue
            return []
