import math
from config import DAYS_PER_YEAR

class Celestials:
    def __init__(self, chronos):
        self.chronos = chronos
        
        # --- OUTPUTS (Equatorial Coordinates) ---
        self.solar_declination = 0.0     
        self.greenwich_hour_angle = 0.0  
        
        self.lunar_declination = 0.0
        self.lunar_gha = 0.0
        
        # --- CONSTANTS (The Physics) ---
        # 1. Earth's Axial Tilt (Obliquity of the Ecliptic)
        self.epsilon = math.radians(23.44) 
        
        # 2. Moon's Orbital Tilt relative to Ecliptic
        self.i_moon = math.radians(5.14)   

        # 3. Orbital Periods (Days)
        self.lunar_period_synodic = 29.53  # Phase cycle (New Moon to New Moon)
        self.lunar_period_sidereal = 27.32 # Orbital cycle relative to stars
        self.lunar_node_cycle = 6793.5     # 18.6 years (Nodal Precession)

    def update(self):
        """
        Calculates precise orbital positions using Ecliptic -> Equatorial conversion.
        """
        # =========================================================
        # 1. TIME PARAMETERS
        # =========================================================
        # Continuous time in days including years
        total_days = self.chronos.day_of_year + (self.chronos.year * DAYS_PER_YEAR)
        # Fraction of the current day (0.0 to 1.0)
        day_frac = self.chronos.time_of_day / 24.0
        
        # Exact time t (in days)
        t = total_days + day_frac

        # =========================================================
        # 2. THE SUN (The Ecliptic Baseline)
        # =========================================================
        
        # Mean Longitude of the Sun (0 to 2PI)
        # This is the Sun's angle on the Ecliptic plane (The Year)
        # We offset by PI/2 so Day 0 is Spring Equinox (Dec=0) not Winter Solstice
        sun_long = (2.0 * math.pi * (self.chronos.day_of_year / DAYS_PER_YEAR))
        
        # Sun Declination Formula (Ecliptic -> Equatorial)
        # sin(Dec) = sin(Obliquity) * sin(Longitude)
        self.solar_declination = math.asin(math.sin(self.epsilon) * math.sin(sun_long))

        # Sun GHA (Earth's Rotation)
        # Noon (12.0) = 0.0 rads. Earth rotates East, Sun moves West (-).
        time_norm = (self.chronos.time_of_day - 12.0) / 12.0
        self.greenwich_hour_angle = time_norm * math.pi * -1.0

        # =========================================================
        # 3. THE MOON (The Complex Body)
        # =========================================================
        
        # A. Lunar Mean Longitude (lambda_m)
        # Where is the moon along its orbit relative to the stars?
        # It circles the full 360 degrees every 27.32 days.
        moon_long = (t / self.lunar_period_sidereal) * 2.0 * math.pi
        
        # B. Lunar Latitude (beta_m)
        # The Moon wobbles up and down by 5.14 degrees relative to the sun's path.
        # This depends on the Nodes (where moon crosses ecliptic).
        # The nodes rotate backwards once every 18.6 years.
        node_long = (t / self.lunar_node_cycle) * 2.0 * math.pi * -1.0 # Retrograde
        
        # Distance from Ascending Node
        dist_from_node = moon_long - node_long
        
        # Ecliptic Latitude of Moon
        moon_lat = self.i_moon * math.sin(dist_from_node)
        
        # C. Coordinate Transformation: Ecliptic -> Equatorial
        # This is the "Not Cheap" Math.
        # We are converting from the Solar System plane to the Earth's Tilted plane.
        
        # Formula:
        # sin(dec) = sin(lat)*cos(eps) + cos(lat)*sin(eps)*sin(long)
        
        sin_dec = (math.sin(moon_lat) * math.cos(self.epsilon)) + \
                  (math.cos(moon_lat) * math.sin(self.epsilon) * math.sin(moon_long))
        
        self.lunar_declination = math.asin(sin_dec)

        # D. Lunar GHA
        # We need the difference between Sun and Moon (Phase) to determine offset.
        # Phase Angle = Moon Longitude - Sun Longitude
        # But we need to project this onto the Equator for GHA.
        # A solid approximation for GHA is:
        # GHA_Moon = GHA_Sun - (RightAscension_Moon - RightAscension_Sun)
        
        # Let's calculate Right Ascension (RA) for both
        ra_sun = math.atan2(math.cos(self.epsilon) * math.sin(sun_long), math.cos(sun_long))
        
        # RA Moon (Simplified projection onto ecliptic longitude for RA is usually close enough for games,
        # but let's do the atan2 to be safe)
        # y = sin(long)*cos(eps) - tan(lat)*sin(eps)  <-- Full formula is messy
        # Let's stick to the Phase Lag Logic relative to the Sun's GHA, but use the calculated Longitudes.
        
        # Difference in Ecliptic Longitude (How far Moon is from Sun)
        long_diff = moon_long - sun_long
        
        # The Moon lags the Sun by this longitudinal difference
        self.lunar_gha = self.greenwich_hour_angle - long_diff
