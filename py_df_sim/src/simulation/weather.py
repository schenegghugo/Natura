import numpy as np
from scipy.ndimage import gaussian_filter

class WeatherSimulator:
    def __init__(self, size):
        self.size = size
        
        # Physics Constants
        self.thermal_inertia = 0.1  # How fast temp changes
        self.pressure_smoothing = 2.0 # Blurs pressure to create large weather fronts
        self.wind_strength = 0.5    # Multiplier for wind speed
        self.coriolis_effect = 0.1  # Spin of the earth deflecting wind

    def update(self, world_map, dt):
        """
        Main simulation step. Modifies world_map in place.
        world_map shape: (H, W, 8)
        
        Layers reminder:
        0: Height, 1: Ground Temp, 2: Ground Hum, 3: Bio
        4: Wind X, 5: Wind Y, 6: Air Temp, 7: Air Hum
        """
        
        # 1. Update Temperature (Radiative Heating/Cooling)
        # -------------------------------------------------
        # This would normally depend on Sun position (Lat/Lon + Time)
        # For now, let's just let the ground heat the air.
        
        # Extract layers for easier math
        height = world_map[:, :, 0]
        ground_temp = world_map[:, :, 1]
        air_temp = world_map[:, :, 6]
        
        # Air tends to match ground temp over time, but loses heat with altitude
        target_air_temp = ground_temp - (height * 0.2) # Higher = Colder
        
        # Apply thermal inertia (Air changes temp slowly)
        diff = target_air_temp - air_temp
        world_map[:, :, 6] += diff * self.thermal_inertia * dt

        # 2. Calculate Pressure System
        # -------------------------------------------------
        # Ideal Gas Law simplified: P = rho * R * T.
        # In a game: Hot = Low Pressure, Cold = High Pressure.
        # Higher Altitude = Lower Pressure.
        
        # Inverse relationship with Temp, inverse with Height
        pressure = (1.0 - world_map[:, :, 6]) * 0.8 + (1.0 - height) * 0.2
        
        # Smooth pressure to create "Regional" weather fronts rather than pixel noise
        pressure = gaussian_filter(pressure, sigma=self.pressure_smoothing)
        
        # 3. Calculate Wind (Gradient Descent)
        # -------------------------------------------------
        # Wind flows from High Pressure to Low Pressure.
        # This is the negative gradient of the pressure map.
        
        # np.gradient returns [dY, dX]
        grad_y, grad_x = np.gradient(pressure)
        
        # Invert gradient (High -> Low) and apply strength
        wind_x = -grad_x * self.wind_strength
        wind_y = -grad_y * self.wind_strength
        
        # --- Optional: Coriolis Effect ---
        # Deflects wind based on Latitude. 
        # Simple hack: rotate vector slightly based on Y position.
        # (Skipping for now to keep basic physics verifiable)

        # Update Wind Layers
        world_map[:, :, 4] = wind_x + 0.5 # Remap -0.5..0.5 to 0.0..1.0
        world_map[:, :, 5] = wind_y + 0.5

        # 4. Advection (Transport)
        # -------------------------------------------------
        # Move Air Humidity and Air Temp based on Wind Vectors.
        # This is computationally expensive to do perfectly.
        # We will do a "Semi-Lagrangian" approximation or simple neighbor blending next.
        
        return world_map
