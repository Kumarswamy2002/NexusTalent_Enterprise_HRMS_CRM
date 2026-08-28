"""
NexusTalent Geofence Engine
Calculates Great-Circle distance using Haversine algorithm to verify employee clock-in location.
"""

import math
from typing import Tuple
from backend.app.core.config import settings


class GeofenceEngine:
    EARTH_RADIUS_METERS = 6371000.0

    @classmethod
    def calculate_distance(
        cls,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> float:
        """
        Returns distance in meters between two GPS coordinates using Haversine formula.
        """
        phi1 = math.radians(lat1)
        phi2 = math.radians(lat2)
        delta_phi = math.radians(lat2 - lat1)
        delta_lambda = math.radians(lon2 - lon1)

        a = (
            math.sin(delta_phi / 2.0) ** 2 +
            math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        return cls.EARTH_RADIUS_METERS * c

    @classmethod
    def verify_location(
        cls,
        user_lat: float,
        user_lon: float,
        target_lat: float = settings.HQ_LATITUDE,
        target_lon: float = settings.HQ_LONGITUDE,
        max_allowed_meters: float = settings.GEOFENCE_RADIUS_METERS
    ) -> Tuple[bool, float]:
        """
        Verifies if coordinate is within allowable geofence radius.
        Returns: (is_within_geofence, calculated_distance_meters)
        """
        distance = cls.calculate_distance(user_lat, user_lon, target_lat, target_lon)
        is_valid = distance <= max_allowed_meters
        return is_valid, round(distance, 2)
