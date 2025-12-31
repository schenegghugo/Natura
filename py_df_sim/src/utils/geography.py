# src/utils/geography.py
import math
from src.config import WORLD_SCALE, MAX_LATITUDE, MIN_LATITUDE

class GeoMath:
    @staticmethod
    def get_latitude(z_coord):
        """
        Converts world Z coordinate to Latitude (-90 to 90).
        Stops at the poles (Clamping).
        """
        # Convert units to degrees
        deg = z_coord / WORLD_SCALE
        
        # Clamp between South Pole and North Pole
        return max(MIN_LATITUDE, min(MAX_LATITUDE, deg))

    @staticmethod
    def get_longitude(x_coord):
        """
        Converts world X coordinate to Longitude (-180 to 180).
        Wraps around (Modulus).
        """
        # Convert units to degrees
        deg = x_coord / WORLD_SCALE
        
        # Wrap around -180 to 180 logic
        # ((deg + 180) % 360) - 180 is a common formula for this
        return ((deg + 180) % 360) - 180

    @staticmethod
    def get_lat_lon(x, z):
        return GeoMath.get_latitude(z), GeoMath.get_longitude(x)
