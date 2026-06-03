"""Event generation module for Store Intelligence Platform.

This module provides the EventGenerator class which transforms tracking data
into structured events (ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL,
BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY).
"""

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.logger import Logger
from src.models import Event, EventType, Point, Track, Zone, ZoneType


class EventGenerator:
    """Generates structured events from person tracking data.
    
    The EventGenerator analyzes tracking data across video frames to detect
    meaningful events such as store entry/exit, zone interactions, billing
    queue activities, and customer reentry.
    
    Attributes:
        store_id: Identifier for the store
        zones: List of Zone definitions for spatial analysis
        logger: Logger instance for structured logging
        fps: Video frames per second (default 30)
        track_state: Map of track_id -> last_seen_frame
        zone_state: Map of track_id -> {zone_id, enter_frame}
        exit_history: Map of track_id -> exit_timestamp
        billing_queue_state: Map of track_id -> {enter_frame, queue_position}
    """
    
    def __init__(
        self,
        store_id: str,
        zones: List[Zone],
        logger: Optional[Logger] = None,
        fps: int = 30
    ):
        """Initialize EventGenerator with store configuration.
        
        Args:
            store_id: Unique identifier for the store
            zones: List of Zone objects defining spatial regions
            logger: Optional Logger instance for structured logging
            fps: Video frames per second (default 30, used for time calculations)
        
        Raises:
            ValueError: If fps is not positive
        """
        if fps <= 0:
            raise ValueError(f"fps must be positive, got {fps}")
        
        self.store_id = store_id
        self.zones = zones
        self.logger = logger
        self.fps = fps
        
        # Track state: track_id -> last_seen_frame
        self.track_state: Dict[int, int] = {}
        
        # Zone state: track_id -> {zone_id: str, enter_frame: int}
        self.zone_state: Dict[int, Dict[str, Any]] = {}
        
        # Exit history: track_id -> exit_timestamp (datetime)
        self.exit_history: Dict[int, datetime] = {}
        
        # Billing queue state: track_id -> {enter_frame: int, queue_position: int}
        self.billing_queue_state: Dict[int, Dict[str, int]] = {}
        
        if self.logger:
            self.logger.info(
                "EventGenerator initialized",
                store_id=store_id,
                zone_count=len(zones),
                fps=fps
            )
    
    @classmethod
    def from_zone_config(
        cls,
        store_id: str,
        zone_config_path: str,
        logger: Optional[Logger] = None,
        fps: int = 30
    ) -> "EventGenerator":
        """Create EventGenerator from zone configuration file.
        
        Args:
            store_id: Unique identifier for the store
            zone_config_path: Path to zone configuration JSON file
            logger: Optional Logger instance
            fps: Video frames per second (default 30)
        
        Returns:
            EventGenerator instance
        
        Raises:
            FileNotFoundError: If zone config file doesn't exist
            ValueError: If zone config is invalid
        """
        config_path = Path(zone_config_path)
        if not config_path.exists():
            raise FileNotFoundError(f"Zone configuration not found: {zone_config_path}")
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        if 'zones' not in config:
            raise ValueError("Zone configuration must contain 'zones' key")
        
        zones = []
        for zone_data in config['zones']:
            # Parse zone type
            zone_type_str = zone_data.get('zone_type', 'GENERAL')
            zone_type = ZoneType.GENERAL if zone_type_str == 'GENERAL' else ZoneType.BILLING_QUEUE
            
            # Parse polygon points
            polygon = [Point(x=p['x'], y=p['y']) for p in zone_data['polygon']]
            
            zone = Zone(
                zone_id=zone_data['zone_id'],
                zone_name=zone_data['zone_name'],
                polygon=polygon,
                zone_type=zone_type
            )
            zones.append(zone)
        
        if logger:
            logger.info(
                "Loaded zone configuration",
                zone_config_path=zone_config_path,
                zone_count=len(zones)
            )
        
        return cls(store_id=store_id, zones=zones, logger=logger, fps=fps)
    
    def process_tracks(self, tracks: List[Track], frame_number: int) -> List[Event]:
        """Generate events from current frame's tracking data.
        
        This method performs the following analysis:
        1. Entry/Exit detection (track appearance/disappearance)
        2. Zone interaction detection (zone entry/exit/dwell)
        3. Billing queue detection (queue join/abandon)
        4. Reentry detection (returning customers)
        
        Args:
            tracks: List of Track objects from current frame
            frame_number: Current frame number
        
        Returns:
            List of Event objects generated from the tracking data
        """
        events = []
        current_track_ids = {track.track_id for track in tracks}
        
        if self.logger:
            self.logger.debug(
                "Processing tracks",
                frame_number=frame_number,
                track_count=len(tracks)
            )
        
        # 1. Detect ENTRY events (new tracks)
        for track in tracks:
            if track.track_id not in self.track_state:
                entry_event = self._generate_entry_event(track, frame_number)
                events.append(entry_event)
                
                # Check for reentry
                reentry_event = self._check_reentry(track, frame_number)
                if reentry_event:
                    events.append(reentry_event)
        
        # 2. Detect EXIT events (absent tracks)
        exit_events = self._detect_exit_events(current_track_ids, frame_number)
        events.extend(exit_events)
        
        # 3. Detect zone interactions for active tracks
        for track in tracks:
            zone_events = self._detect_zone_interactions(track, frame_number)
            events.extend(zone_events)
        
        # 4. Update track state for all current tracks
        for track in tracks:
            self.track_state[track.track_id] = frame_number
        
        if self.logger:
            self.logger.debug(
                "Events generated",
                frame_number=frame_number,
                event_count=len(events)
            )
        
        return events
    
    def finalize(self) -> List[Event]:
        """Generate final EXIT events for all remaining active tracks.
        
        This method should be called at the end of video processing to
        ensure all active tracks receive EXIT events.
        
        Returns:
            List of EXIT Event objects for remaining active tracks
        """
        events = []
        
        if self.logger:
            self.logger.info(
                "Finalizing event generation",
                remaining_tracks=len(self.track_state)
            )
        
        # Generate EXIT events for all remaining tracks
        for track_id, last_frame in self.track_state.items():
            exit_event = self._generate_exit_event(track_id, last_frame)
            events.append(exit_event)
            
            # Also handle zone exits if track was in a zone
            if track_id in self.zone_state:
                zone_exit_event = self._generate_zone_exit_event(track_id, last_frame)
                events.append(zone_exit_event)
            
            # Handle billing queue abandonment if track was in queue
            if track_id in self.billing_queue_state:
                abandon_event = self._generate_billing_queue_abandon_event(track_id, last_frame)
                events.append(abandon_event)
        
        # Clear all state
        self.track_state.clear()
        self.zone_state.clear()
        self.billing_queue_state.clear()
        
        if self.logger:
            self.logger.info(
                "Finalization complete",
                exit_events_generated=len(events)
            )
        
        return events
    
    def _generate_entry_event(self, track: Track, frame_number: int) -> Event:
        """Generate ENTRY event for a new track.
        
        Args:
            track: Track object
            frame_number: Current frame number
        
        Returns:
            ENTRY Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        event = Event(
            event_id=event_id,
            event_type=EventType.ENTRY,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={}
        )
        
        if self.logger:
            self.logger.debug(
                "ENTRY event generated",
                track_id=track.track_id,
                frame_number=frame_number
            )
        
        return event
    
    def _generate_exit_event(self, track_id: int, last_frame: int) -> Event:
        """Generate EXIT event for a track that has disappeared.
        
        Args:
            track_id: Track identifier
            last_frame: Frame number when track was last seen
        
        Returns:
            EXIT Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(last_frame)
        
        # Store exit timestamp for reentry detection
        self.exit_history[track_id] = timestamp
        
        event = Event(
            event_id=event_id,
            event_type=EventType.EXIT,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={}
        )
        
        if self.logger:
            self.logger.debug(
                "EXIT event generated",
                track_id=track_id,
                last_frame=last_frame
            )
        
        return event
    
    def _detect_exit_events(self, current_track_ids: set, frame_number: int) -> List[Event]:
        """Detect tracks that should generate EXIT events.
        
        A track generates an EXIT event when it has been absent for more than
        max_age frames (30 frames by default).
        
        Args:
            current_track_ids: Set of track IDs present in current frame
            frame_number: Current frame number
        
        Returns:
            List of EXIT events for tracks that have disappeared
        """
        events = []
        max_age = 30  # From PersonTracker default
        
        # Find tracks that are no longer present
        absent_track_ids = set(self.track_state.keys()) - current_track_ids
        
        for track_id in absent_track_ids:
            last_seen = self.track_state[track_id]
            frames_absent = frame_number - last_seen
            
            # Generate EXIT event if absent > max_age frames
            if frames_absent > max_age:
                exit_event = self._generate_exit_event(track_id, last_seen)
                events.append(exit_event)
                
                # Remove from track state
                del self.track_state[track_id]
                
                # Handle zone exit if track was in a zone
                if track_id in self.zone_state:
                    zone_exit_event = self._generate_zone_exit_event(track_id, last_seen)
                    events.append(zone_exit_event)
                    del self.zone_state[track_id]
                
                # Handle billing queue abandonment if track was in queue
                if track_id in self.billing_queue_state:
                    abandon_event = self._generate_billing_queue_abandon_event(track_id, last_seen)
                    events.append(abandon_event)
                    # Note: billing_queue_state is already cleared in _generate_billing_queue_abandon_event
        
        return events
    
    def _check_reentry(self, track: Track, frame_number: int) -> Optional[Event]:
        """Check if a track is a reentry and generate REENTRY event if so.
        
        A reentry is detected when a new track appears within 300 seconds
        of a previous EXIT event. We use a simple heuristic based on timing.
        
        Args:
            track: New track
            frame_number: Current frame number
        
        Returns:
            REENTRY Event if reentry detected, None otherwise
        """
        current_timestamp = self._frame_to_timestamp(frame_number)
        reentry_threshold = 300  # seconds
        
        # Check exit history for potential reentries
        # First, clean up old exit history (> 300 seconds old)
        tracks_to_remove = []
        for prev_track_id, exit_timestamp in self.exit_history.items():
            time_since_exit = (current_timestamp - exit_timestamp).total_seconds()
            if time_since_exit > reentry_threshold:
                tracks_to_remove.append(prev_track_id)
        
        for track_id in tracks_to_remove:
            del self.exit_history[track_id]
        
        # Now check for reentries
        for prev_track_id, exit_timestamp in list(self.exit_history.items()):
            time_since_exit = (current_timestamp - exit_timestamp).total_seconds()
            
            # If within reentry window, consider this a reentry
            if 0 <= time_since_exit <= reentry_threshold:
                event_id = str(uuid.uuid4())
                immediate_return = time_since_exit < 300
                
                event = Event(
                    event_id=event_id,
                    event_type=EventType.REENTRY,
                    timestamp=current_timestamp,
                    store_id=self.store_id,
                    track_id=track.track_id,
                    metadata={
                        'time_since_last_exit_seconds': time_since_exit,
                        'immediate_return': immediate_return,
                        'previous_track_id': prev_track_id
                    }
                )
                
                # Remove from exit history
                del self.exit_history[prev_track_id]
                
                if self.logger:
                    self.logger.debug(
                        "REENTRY event generated",
                        track_id=track.track_id,
                        previous_track_id=prev_track_id,
                        time_since_exit=time_since_exit
                    )
                
                return event
        
        return None
    
    def _detect_zone_interactions(self, track: Track, frame_number: int) -> List[Event]:
        """Detect zone entry, exit, and dwell events for a track.
        
        Args:
            track: Track object
            frame_number: Current frame number
        
        Returns:
            List of zone-related events
        """
        events = []
        
        # Calculate track centroid (center of bounding box)
        centroid_x = track.bbox.x + track.bbox.width / 2
        centroid_y = track.bbox.y + track.bbox.height / 2
        centroid = Point(x=centroid_x, y=centroid_y)
        
        # Check which zone the track is currently in (if any)
        current_zone = None
        for zone in self.zones:
            if self._point_in_polygon(centroid, zone.polygon):
                current_zone = zone
                break
        
        # Get previous zone state
        previous_zone_id = None
        if track.track_id in self.zone_state:
            previous_zone_id = self.zone_state[track.track_id].get('zone_id')
        
        # Case 1: Track entered a new zone
        if current_zone and previous_zone_id != current_zone.zone_id:
            # If was in a different zone, generate exit event first
            if previous_zone_id:
                zone_exit_event = self._generate_zone_exit_event(track.track_id, frame_number)
                events.append(zone_exit_event)
            
            # Generate zone enter event
            zone_enter_event = self._generate_zone_enter_event(track, current_zone, frame_number)
            events.append(zone_enter_event)
            
            # Update zone state
            self.zone_state[track.track_id] = {
                'zone_id': current_zone.zone_id,
                'zone_name': current_zone.zone_name,
                'zone_type': current_zone.zone_type,
                'enter_frame': frame_number
            }
            
            # Special handling for BILLING_QUEUE zones
            if current_zone.zone_type == ZoneType.BILLING_QUEUE:
                billing_join_event = self._generate_billing_queue_join_event(track, frame_number)
                events.append(billing_join_event)
        
        # Case 2: Track exited zone (no longer in any zone)
        elif not current_zone and previous_zone_id:
            zone_exit_event = self._generate_zone_exit_event(track.track_id, frame_number)
            events.append(zone_exit_event)
            
            # Check for billing queue abandonment
            zone_type = self.zone_state[track.track_id].get('zone_type')
            if zone_type == ZoneType.BILLING_QUEUE:
                abandon_event = self._generate_billing_queue_abandon_event(track.track_id, frame_number)
                events.append(abandon_event)
            
            # Remove from zone state
            del self.zone_state[track.track_id]
        
        # Case 3: Track still in same zone - check for dwell event
        elif current_zone and previous_zone_id == current_zone.zone_id:
            dwell_event = self._check_zone_dwell(track.track_id, frame_number)
            if dwell_event:
                events.append(dwell_event)
        
        return events
    
    def _generate_zone_enter_event(self, track: Track, zone: Zone, frame_number: int) -> Event:
        """Generate ZONE_ENTER event.
        
        Args:
            track: Track object
            zone: Zone object
            frame_number: Current frame number
        
        Returns:
            ZONE_ENTER Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        event = Event(
            event_id=event_id,
            event_type=EventType.ZONE_ENTER,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={
                'zone_id': zone.zone_id,
                'zone_name': zone.zone_name
            }
        )
        
        if self.logger:
            self.logger.debug(
                "ZONE_ENTER event generated",
                track_id=track.track_id,
                zone_id=zone.zone_id,
                frame_number=frame_number
            )
        
        return event
    
    def _generate_zone_exit_event(self, track_id: int, frame_number: int) -> Event:
        """Generate ZONE_EXIT event.
        
        Args:
            track_id: Track identifier
            frame_number: Current frame number
        
        Returns:
            ZONE_EXIT Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        # Get zone info from state
        zone_info = self.zone_state.get(track_id, {})
        zone_id = zone_info.get('zone_id', 'unknown')
        zone_name = zone_info.get('zone_name', 'unknown')
        enter_frame = zone_info.get('enter_frame', frame_number)
        
        # Calculate zone duration
        duration_frames = frame_number - enter_frame
        duration_seconds = duration_frames / self.fps
        
        event = Event(
            event_id=event_id,
            event_type=EventType.ZONE_EXIT,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={
                'zone_id': zone_id,
                'zone_name': zone_name,
                'zone_duration_seconds': duration_seconds
            }
        )
        
        if self.logger:
            self.logger.debug(
                "ZONE_EXIT event generated",
                track_id=track_id,
                zone_id=zone_id,
                duration_seconds=duration_seconds
            )
        
        return event
    
    def _check_zone_dwell(self, track_id: int, frame_number: int) -> Optional[Event]:
        """Check if track has dwelled in zone and generate ZONE_DWELL event.
        
        A ZONE_DWELL event is generated when a track remains in a zone for
        more than 5 seconds (150 frames at 30 fps).
        
        Args:
            track_id: Track identifier
            frame_number: Current frame number
        
        Returns:
            ZONE_DWELL Event if dwell threshold exceeded, None otherwise
        """
        zone_info = self.zone_state.get(track_id, {})
        enter_frame = zone_info.get('enter_frame')
        
        if not enter_frame:
            return None
        
        duration_frames = frame_number - enter_frame
        duration_seconds = duration_frames / self.fps
        dwell_threshold = 5.0  # seconds
        
        # Generate dwell event only once when threshold is exceeded
        # We check if duration is exactly at or just passed the threshold
        if duration_seconds >= dwell_threshold and not zone_info.get('dwell_generated', False):
            event_id = str(uuid.uuid4())
            timestamp = self._frame_to_timestamp(frame_number)
            
            zone_id = zone_info.get('zone_id', 'unknown')
            zone_name = zone_info.get('zone_name', 'unknown')
            
            event = Event(
                event_id=event_id,
                event_type=EventType.ZONE_DWELL,
                timestamp=timestamp,
                store_id=self.store_id,
                track_id=track_id,
                metadata={
                    'zone_id': zone_id,
                    'zone_name': zone_name,
                    'dwell_duration_seconds': duration_seconds
                }
            )
            
            # Mark dwell event as generated
            self.zone_state[track_id]['dwell_generated'] = True
            
            if self.logger:
                self.logger.debug(
                    "ZONE_DWELL event generated",
                    track_id=track_id,
                    zone_id=zone_id,
                    duration_seconds=duration_seconds
                )
            
            return event
        
        return None
    
    def _generate_billing_queue_join_event(self, track: Track, frame_number: int) -> Event:
        """Generate BILLING_QUEUE_JOIN event.
        
        Args:
            track: Track object
            frame_number: Current frame number
        
        Returns:
            BILLING_QUEUE_JOIN Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        # Calculate queue position (simple implementation: number of tracks in queue)
        queue_position = len(self.billing_queue_state) + 1
        
        # Store billing queue state
        self.billing_queue_state[track.track_id] = {
            'enter_frame': frame_number,
            'queue_position': queue_position
        }
        
        event = Event(
            event_id=event_id,
            event_type=EventType.BILLING_QUEUE_JOIN,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track.track_id,
            metadata={
                'queue_position': queue_position
            }
        )
        
        if self.logger:
            self.logger.debug(
                "BILLING_QUEUE_JOIN event generated",
                track_id=track.track_id,
                queue_position=queue_position
            )
        
        return event
    
    def _generate_billing_queue_abandon_event(self, track_id: int, frame_number: int) -> Event:
        """Generate BILLING_QUEUE_ABANDON event.
        
        Args:
            track_id: Track identifier
            frame_number: Current frame number
        
        Returns:
            BILLING_QUEUE_ABANDON Event
        """
        event_id = str(uuid.uuid4())
        timestamp = self._frame_to_timestamp(frame_number)
        
        # Get queue info from state
        queue_info = self.billing_queue_state.get(track_id, {})
        enter_frame = queue_info.get('enter_frame', frame_number)
        
        # Calculate wait time
        wait_frames = frame_number - enter_frame
        wait_seconds = wait_frames / self.fps
        high_wait_time = wait_seconds > 300
        
        event = Event(
            event_id=event_id,
            event_type=EventType.BILLING_QUEUE_ABANDON,
            timestamp=timestamp,
            store_id=self.store_id,
            track_id=track_id,
            metadata={
                'queue_wait_time_seconds': wait_seconds,
                'high_wait_time': high_wait_time
            }
        )
        
        # Remove from billing queue state
        if track_id in self.billing_queue_state:
            del self.billing_queue_state[track_id]
        
        if self.logger:
            self.logger.debug(
                "BILLING_QUEUE_ABANDON event generated",
                track_id=track_id,
                wait_seconds=wait_seconds,
                high_wait_time=high_wait_time
            )
        
        return event
    
    def _point_in_polygon(self, point: Point, polygon: List[Point]) -> bool:
        """Test if a point is inside a polygon using ray casting algorithm.
        
        The ray casting algorithm works by drawing a ray from the point to infinity
        and counting how many times the ray crosses the polygon boundary. If the
        count is odd, the point is inside; if even, it's outside.
        
        Args:
            point: Point to test
            polygon: List of Points defining polygon boundary
        
        Returns:
            True if point is inside polygon, False otherwise
        """
        if len(polygon) < 3:
            return False
        
        x, y = point.x, point.y
        inside = False
        
        # Iterate through polygon edges
        n = len(polygon)
        p1 = polygon[0]
        
        for i in range(1, n + 1):
            p2 = polygon[i % n]
            
            # Check if point is on the same y-level as the edge
            if y > min(p1.y, p2.y):
                if y <= max(p1.y, p2.y):
                    if x <= max(p1.x, p2.x):
                        # Calculate x-intersection of the edge with horizontal ray
                        if p1.y != p2.y:
                            x_intersection = (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        else:
                            x_intersection = p1.x
                        
                        # If point is to the left of intersection, toggle inside flag
                        if p1.x == p2.x or x <= x_intersection:
                            inside = not inside
            
            p1 = p2
        
        return inside
    
    def _frame_to_timestamp(self, frame_number: int) -> datetime:
        """Convert frame number to ISO 8601 timestamp.
        
        Args:
            frame_number: Frame number
        
        Returns:
            datetime object in UTC timezone
        """
        seconds = frame_number / self.fps
        # For simplicity, we use a base timestamp (epoch) + offset
        # In a real system, this would use the video's actual start time
        from datetime import timedelta
        base_timestamp = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        timestamp = base_timestamp + timedelta(seconds=seconds)
        return timestamp
