# src/simulation/chronos.py
from config import REAL_SECONDS_PER_GAME_DAY, DAYS_PER_YEAR, STARTING_HOUR

class Chronos:
    def __init__(self):
        # 0.0 to 24.0
        self.time_of_day = STARTING_HOUR
        
        # 1 to DAYS_PER_YEAR
        self.day_of_year = 1
        
        # Years passed
        self.year = 1
        
        # Total accumulated game hours (good for continuous functions)
        self.total_game_hours = STARTING_HOUR

    def update(self, dt):
        """
        dt: Delta Time in seconds from the main game loop
        """
        # 1. Calculate how many game-hours passed in this frame
        # Formula: (RealDT / RealSecPerDay) * 24 hours
        game_hours_passed = (dt / REAL_SECONDS_PER_GAME_DAY) * 24.0
        
        self.total_game_hours += game_hours_passed
        self.time_of_day += game_hours_passed
        
        # 2. Check for End of Day (24h rollover)
        if self.time_of_day >= 24.0:
            self.time_of_day -= 24.0
            self.day_of_year += 1
            
            # 3. Check for End of Year
            if self.day_of_year > DAYS_PER_YEAR:
                self.day_of_year = 1
                self.year += 1
                print(f"Happy New Year! Year {self.year}")

    def get_info(self):
        return f"Y:{self.year} D:{self.day_of_year} H:{self.time_of_day:.2f}"
    
    # Normalized time for shaders (0.0 to 1.0 representing 00:00 to 24:00)
    @property
    def day_progress(self):
        return self.time_of_day / 24.0

    @property
    def year_progress(self):
        """Returns year progress 0.0 to 1.0."""
        return self.day_of_year / DAYS_PER_YEAR
