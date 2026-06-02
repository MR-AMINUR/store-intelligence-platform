"""Person tracking module using ByteTrack algorithm.

This module provides the PersonTracker class which maintains consistent
identities for detected persons across video frames using the ByteTrack
tracking algorithm.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

import numpy as np

from src.logger import Logger
from src.models import BoundingBox, Detection, Track, TrackState


@dataclass
class Position:
    """Represents a position in 2D space.
    
    Attributes:
        x: X-coordinate (pixels)
        y: Y-coordinate (pixels)
        frame_number: Frame number at which this position was recorded
    """
    x: float
    y: float
    frame_number: int


@dataclass
class TrackedObject:
    """Internal representation of a tracked object.
    
    Attributes:
        track_id: Unique identifier for this track
        bbox: Current bounding box
        frame_number: Frame number of last update
        age: Number of frames since last detection
        state: Current track state
        hits: Number of consecutive detections
        trajectory: List of positions over time
    """
    track_id: int
    bbox: BoundingBox
    frame_number: int
    age: int = 0
    state: TrackState = TrackState.ACTIVE
    hits: int = 1
    trajectory: List[Position] = field(default_factory=list)


class PersonTracker:
    """Tracks detected persons across video frames using ByteTrack algorithm.
    
    ByteTrack is a simple yet effective multi-object tracking algorithm that
    associates detection boxes across frames using IoU (Intersection over Union)
    matching with Kalman filtering for motion prediction.
    
    Attributes:
        max_age: Maximum number of frames to keep a track without detections
        logger: Logger instance for structured logging
        next_id: Next available track ID
        tracks: Dictionary of active tracks (track_id -> TrackedObject)
        trajectories: Dictionary storing trajectory history (track_id -> List[Position])
    """
    
    def __init__(self, max_age: int = 30, logger: Logger = None):
        """Initialize PersonTracker with ByteTrack.
        
        Args:
            max_age: Maximum number of frames to keep a track without detections.
                    Tracks without detections for more than max_age frames are removed.
            logger: Logger instance for structured logging
        
        Raises:
            ValueError: If max_age is not positive
        """
        if max_age <= 0:
            raise ValueError(f"max_age must be positive, got {max_age}")
        
        self.max_age = max_age
        self.logger = logger
        self.next_id = 1
        self.tracks: Dict[int, TrackedObject] = {}
        self.trajectories: Dict[int, List[Position]] = {}
        
        if self.logger:
            self.logger.info(
                "PersonTracker initialized",
                max_age=max_age
            )
    
    def update(self, detections: List[Detection], frame_number: int) -> List[Track]:
        """Update tracks with new detections from current frame.
        
        This method performs the following steps:
        1. Match detections to existing tracks using IoU
        2. Update matched tracks with new detections
        3. Create new tracks for unmatched detections
        4. Age tracks that were not matched (occlusion handling)
        5. Remove tracks that exceed max_age
        6. Store trajectory positions for all active tracks
        
        Args:
            detections: List of detections from the current frame
            frame_number: Current frame number
        
        Returns:
            List of Track objects representing current tracked persons
        """
        if self.logger:
            self.logger.debug(
                "Updating tracks",
                detections_count=len(detections),
                frame_number=frame_number,
                active_tracks=len(self.tracks)
            )
        
        # Handle edge case: empty detections
        if not detections:
            return self._age_tracks(frame_number)
        
        # Match detections to existing tracks
        matched_tracks, unmatched_detections = self._match_detections_to_tracks(detections)
        
        # Track which tracks received updates (matched + newly created)
        updated_track_ids = set()
        
        # Update matched tracks
        for track_id, detection in matched_tracks:
            self._update_track(track_id, detection, frame_number)
            updated_track_ids.add(track_id)
        
        # Create new tracks for unmatched detections
        for detection in unmatched_detections:
            track_id = self._create_track(detection, frame_number)
            updated_track_ids.add(track_id)
        
        # Age unmatched tracks (those not updated)
        self._age_unmatched_tracks(updated_track_ids, frame_number)
        
        # Remove old tracks
        self._remove_old_tracks()
        
        # Return current tracks
        return self._get_current_tracks()
    
    def get_trajectory(self, track_id: int) -> List[Position]:
        """Return position history for a specific track.
        
        Args:
            track_id: ID of the track to retrieve trajectory for
        
        Returns:
            List of Position objects representing the track's trajectory.
            Returns empty list if track_id is not found.
        """
        return self.trajectories.get(track_id, [])
    
    def _match_detections_to_tracks(
        self,
        detections: List[Detection]
    ) -> Tuple[List[Tuple[int, Detection]], List[Detection]]:
        """Match detections to existing tracks using IoU.
        
        Uses greedy IoU matching: for each detection, find the track with
        highest IoU overlap. Matches are accepted if IoU > threshold.
        
        Args:
            detections: List of detections to match
        
        Returns:
            Tuple of (matched_tracks, unmatched_detections) where:
            - matched_tracks: List of (track_id, detection) tuples
            - unmatched_detections: List of detections that were not matched
        """
        if not self.tracks:
            return [], detections
        
        # Calculate IoU matrix
        track_ids = list(self.tracks.keys())
        iou_matrix = np.zeros((len(detections), len(track_ids)))
        
        for i, detection in enumerate(detections):
            for j, track_id in enumerate(track_ids):
                track = self.tracks[track_id]
                iou_matrix[i, j] = self._compute_iou(detection.bbox, track.bbox)
        
        # Greedy matching with IoU threshold
        iou_threshold = 0.3
        matched_tracks = []
        matched_detection_indices = set()
        matched_track_indices = set()
        
        # Sort matches by IoU (highest first)
        matches = []
        for i in range(len(detections)):
            for j in range(len(track_ids)):
                if iou_matrix[i, j] > iou_threshold:
                    matches.append((i, j, iou_matrix[i, j]))
        
        matches.sort(key=lambda x: x[2], reverse=True)
        
        # Assign matches greedily
        for det_idx, track_idx, iou in matches:
            if det_idx not in matched_detection_indices and track_idx not in matched_track_indices:
                matched_tracks.append((track_ids[track_idx], detections[det_idx]))
                matched_detection_indices.add(det_idx)
                matched_track_indices.add(track_idx)
        
        # Unmatched detections
        unmatched_detections = [
            detections[i] for i in range(len(detections))
            if i not in matched_detection_indices
        ]
        
        if self.logger:
            self.logger.debug(
                "Detection-to-track matching complete",
                matched_count=len(matched_tracks),
                unmatched_count=len(unmatched_detections)
            )
        
        return matched_tracks, unmatched_detections
    
    def _compute_iou(self, bbox1: BoundingBox, bbox2: BoundingBox) -> float:
        """Compute Intersection over Union (IoU) between two bounding boxes.
        
        Args:
            bbox1: First bounding box
            bbox2: Second bounding box
        
        Returns:
            IoU value in range [0, 1]
        """
        # Calculate intersection coordinates
        x1_inter = max(bbox1.x, bbox2.x)
        y1_inter = max(bbox1.y, bbox2.y)
        x2_inter = min(bbox1.x + bbox1.width, bbox2.x + bbox2.width)
        y2_inter = min(bbox1.y + bbox1.height, bbox2.y + bbox2.height)
        
        # Calculate intersection area
        inter_width = max(0, x2_inter - x1_inter)
        inter_height = max(0, y2_inter - y1_inter)
        inter_area = inter_width * inter_height
        
        # Calculate union area
        bbox1_area = bbox1.width * bbox1.height
        bbox2_area = bbox2.width * bbox2.height
        union_area = bbox1_area + bbox2_area - inter_area
        
        # Avoid division by zero
        if union_area == 0:
            return 0.0
        
        return inter_area / union_area
    
    def _update_track(self, track_id: int, detection: Detection, frame_number: int) -> None:
        """Update an existing track with a new detection.
        
        Args:
            track_id: ID of track to update
            detection: New detection to update track with
            frame_number: Current frame number
        """
        track = self.tracks[track_id]
        track.bbox = detection.bbox
        track.frame_number = frame_number
        track.age = 0  # Reset age since track is detected
        track.state = TrackState.ACTIVE
        track.hits += 1
        
        # Store trajectory position
        center_x = detection.bbox.x + detection.bbox.width / 2
        center_y = detection.bbox.y + detection.bbox.height / 2
        position = Position(x=center_x, y=center_y, frame_number=frame_number)
        
        if track_id not in self.trajectories:
            self.trajectories[track_id] = []
        self.trajectories[track_id].append(position)
    
    def _create_track(self, detection: Detection, frame_number: int) -> int:
        """Create a new track from an unmatched detection.
        
        Args:
            detection: Detection to create track from
            frame_number: Current frame number
        
        Returns:
            The track_id of the newly created track
        """
        track_id = self.next_id
        self.next_id += 1
        
        # Create tracked object
        track = TrackedObject(
            track_id=track_id,
            bbox=detection.bbox,
            frame_number=frame_number,
            age=0,
            state=TrackState.ACTIVE,
            hits=1,
            trajectory=[]
        )
        
        self.tracks[track_id] = track
        
        # Store initial trajectory position
        center_x = detection.bbox.x + detection.bbox.width / 2
        center_y = detection.bbox.y + detection.bbox.height / 2
        position = Position(x=center_x, y=center_y, frame_number=frame_number)
        
        self.trajectories[track_id] = [position]
        
        if self.logger:
            self.logger.debug(
                "New track created",
                track_id=track_id,
                frame_number=frame_number
            )
        
        return track_id
    
    def _age_unmatched_tracks(self, matched_track_ids: set, frame_number: int) -> None:
        """Increment age for tracks that were not matched.
        
        Args:
            matched_track_ids: Set of track IDs that were matched in this frame
            frame_number: Current frame number
        """
        for track_id, track in self.tracks.items():
            if track_id not in matched_track_ids:
                track.age += 1
                track.state = TrackState.LOST
    
    def _age_tracks(self, frame_number: int) -> List[Track]:
        """Age all tracks when no detections are present.
        
        Args:
            frame_number: Current frame number
        
        Returns:
            List of current tracks after aging
        """
        for track in self.tracks.values():
            track.age += 1
            track.state = TrackState.LOST
        
        self._remove_old_tracks()
        return self._get_current_tracks()
    
    def _remove_old_tracks(self) -> None:
        """Remove tracks that exceed max_age threshold."""
        tracks_to_remove = []
        
        for track_id, track in self.tracks.items():
            if track.age > self.max_age:
                track.state = TrackState.REMOVED
                tracks_to_remove.append(track_id)
        
        for track_id in tracks_to_remove:
            del self.tracks[track_id]
            if self.logger:
                self.logger.debug(
                    "Track removed",
                    track_id=track_id,
                    reason="exceeded max_age"
                )
    
    def _get_current_tracks(self) -> List[Track]:
        """Convert internal tracked objects to Track data model.
        
        Returns:
            List of Track objects
        """
        return [
            Track(
                track_id=track.track_id,
                bbox=track.bbox,
                frame_number=track.frame_number,
                age=track.age,
                state=track.state
            )
            for track in self.tracks.values()
        ]
