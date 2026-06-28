"""Zone Management for CV Pipeline.

This module provides zone definition and point-in-polygon testing
for spatial event generation.
"""

import json
import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import List

# Configure logging
logger = logging.getLogger(__name__)


class ZoneType(Enum):
    """Zone type enumeration."""
    GENERAL = "general"
    BILLING_QUEUE = "billing_queue"


@dataclass
class Point:
    """2D point in pixel coordinates."""
    x: float
    y: float


@dataclass
class Zone:
    """Store zone definition.
    
    Attributes:
        zone_id: Unique zone identifier
        zone_name: Human-readable name
        polygon: List of points defining boundary
        zone_type: Zone type (GENERAL or BILLING_QUEUE)
    """
    zone_id: str
    zone_name: str
    polygon: List[Point]
    zone_type: ZoneType
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "zone_id": self.zone_id,
            "zone_name": self.zone_name,
            "zone_type": self.zone_type.value,
            "polygon": [{"x": p.x, "y": p.y} for p in self.polygon],
        }


class ZoneManager:
    """Manages store zones and point-in-polygon queries.
    
    Loads zone definitions from JSON configuration and provides
    methods to check which zone a point belongs to.
    
    Attributes:
        zones: List of defined zones
    """
    
    def __init__(self, zones: List[Zone]):
        """Initialize zone manager.
        
        Args:
            zones: List of Zone objects
        """
        self.zones = zones
        logger.info(f"ZoneManager initialized with {len(zones)} zones")
    
    @classmethod
    def from_config(cls, config_path: str) -> "ZoneManager":
        """Load zone manager from configuration file.
        
        Args:
            config_path: Path to zone configuration JSON
            
        Returns:
            ZoneManager instance
            
        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Zone configuration not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        if 'zones' not in config:
            raise ValueError("Zone configuration must contain 'zones' key")
        
        zones = []
        for zone_data in config['zones']:
            # Parse zone type
            zone_type_str = zone_data.get('zone_type', 'GENERAL').upper()
            if zone_type_str == 'GENERAL':
                zone_type = ZoneType.GENERAL
            elif zone_type_str == 'BILLING_QUEUE':
                zone_type = ZoneType.BILLING_QUEUE
            else:
                zone_type = ZoneType.GENERAL
            
            # Parse polygon
            polygon = [Point(x=p['x'], y=p['y']) for p in zone_data['polygon']]
            
            zone = Zone(
                zone_id=zone_data['zone_id'],
                zone_name=zone_data['zone_name'],
                polygon=polygon,
                zone_type=zone_type,
            )
            zones.append(zone)
        
        logger.info(f"Loaded {len(zones)} zones from {config_path}")
        return cls(zones)
    
    def get_zone_at_point(self, x: float, y: float) -> Zone | None:
        """Get zone containing a point.
        
        Args:
            x: X-coordinate
            y: Y-coordinate
            
        Returns:
            Zone containing the point, or None if not in any zone
        """
        point = Point(x=x, y=y)
        
        for zone in self.zones:
            if self.point_in_polygon(point, zone.polygon):
                return zone
        
        return None
    
    def point_in_polygon(self, point: Point, polygon: List[Point]) -> bool:
        """Test if point is inside polygon using ray casting.
        
        Args:
            point: Point to test
            polygon: Polygon boundary points
            
        Returns:
            True if point is inside polygon
        """
        if len(polygon) < 3:
            return False
        
        x, y = point.x, point.y
        inside = False
        
        n = len(polygon)
        p1 = polygon[0]
        
        for i in range(1, n + 1):
            p2 = polygon[i % n]
            
            if y > min(p1.y, p2.y):
                if y <= max(p1.y, p2.y):
                    if x <= max(p1.x, p2.x):
                        if p1.y != p2.y:
                            x_intersection = (y - p1.y) * (p2.x - p1.x) / (p2.y - p1.y) + p1.x
                        else:
                            x_intersection = p1.x
                        
                        if p1.x == p2.x or x <= x_intersection:
                            inside = not inside
            
            p1 = p2
        
        return inside
    
    def get_zone_by_id(self, zone_id: str) -> Zone | None:
        """Get zone by ID.
        
        Args:
            zone_id: Zone identifier
            
        Returns:
            Zone object or None if not found
        """
        for zone in self.zones:
            if zone.zone_id == zone_id:
                return zone
        return None
    
    def get_all_zones(self) -> List[Zone]:
        """Get all zones.
        
        Returns:
            List of all zones
        """
        return self.zones.copy()
