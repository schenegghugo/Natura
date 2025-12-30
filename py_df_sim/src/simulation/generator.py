import numpy as np
import noise
from config import CHUNK_SIZE

class TerrainGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed else 12345
        
        # Scale Settings
        self.base_scale = 0.02 
        self.octaves = 4
        self.persistence = 0.5
        self.lacunarity = 2.0
        
        # Layer Offsets
        # We use these to sample different parts of the infinite noise plane
        # ensuring that Temperature doesn't look identical to Height, etc.
        self.offsets = {
            'temp':   50000,
            'hum':    100000,
            'bio':    150000,
            'wind_x': 200000,
            'wind_y': 250000,
            'air_t':  300000,
            'air_h':  350000
        }

    def _get_noise(self, gx, gy, offset, scale_mod=1.0, octaves=2):
        """
        Helper method to generate specific noise layers.
        scale_mod: Multiplier for coordinates (lower = larger features).
        """
        return noise.pnoise2(
            (gx + offset) * scale_mod, 
            (gy + offset) * scale_mod, 
            octaves=octaves, 
            persistence=0.5, 
            lacunarity=2.0
        )

    def generate_chunk_data(self, cx, cy, level):
        """
        Generates an 8-channel data chunk (Float32).
        
        Layers 0-3 (Terrain):
          0: Height
          1: Ground Temperature
          2: Ground Humidity
          3: Biomass/Magic
          
        Layers 4-7 (Atmosphere):
          4: Wind X Direction
          5: Wind Y Direction
          6: Air Temperature
          7: Air Humidity (Cloud Density)
        """
        # 1. Calculate Step Size based on Zoom Level
        step = self.base_scale / (2 ** level)
        
        # 2. Base World Offsets for this chunk
        base_wx = (cx * CHUNK_SIZE * step) + self.seed
        base_wy = (cy * CHUNK_SIZE * step) + self.seed
        
        # 3. Pre-allocate the array: (33, 33, 8)
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE, 8), dtype=np.float32)
        
        # 4. Loop through pixels
        for y in range(CHUNK_SIZE):
            global_y = base_wy + (y * step)
            
            for x in range(CHUNK_SIZE):                
                global_x = base_wx + (x * step)
                
                # --- TERRAIN GENERATION (Layers 0-3) ---
                
                # Height (Standard rough terrain)
                n_height = noise.pnoise2(
                    global_x, 
                    global_y, 
                    octaves=self.octaves, 
                    persistence=self.persistence, 
                    lacunarity=self.lacunarity
                )
                
                # Temperature (Smoother, large biomes)
                n_temp = self._get_noise(global_x, global_y, self.offsets['temp'], scale_mod=0.5)
                
                # Humidity (Smoother, large biomes)
                n_hum = self._get_noise(global_x, global_y, self.offsets['hum'], scale_mod=0.5)
                
                # Biomass (Detail layer)
                n_bio = self._get_noise(global_x, global_y, self.offsets['bio'], scale_mod=2.0, octaves=1)


                # --- ATMOSPHERE GENERATION (Layers 4-7) ---
                
                # Wind Vectors (Large swirling patterns)
                n_wx = self._get_noise(global_x, global_y, self.offsets['wind_x'], scale_mod=0.3)
                n_wy = self._get_noise(global_x, global_y, self.offsets['wind_y'], scale_mod=0.3)
                
                # Air Temp (Can differ from ground temp)
                n_at = self._get_noise(global_x, global_y, self.offsets['air_t'], scale_mod=0.4)
                
                # Cloud Density (High frequency for fluffy clouds)
                n_ah = self._get_noise(global_x, global_y, self.offsets['air_h'], scale_mod=1.5)


                # --- NORMALIZATION & STORAGE ---
                # We normalize all noise from approx [-1, 1] to [0, 1]
                # This makes shader logic consistent.
                
                # Terrain
                data[y, x, 0] = (n_height + 1) / 2.0
                data[y, x, 1] = (n_temp + 1) / 2.0
                data[y, x, 2] = (n_hum + 1) / 2.0
                data[y, x, 3] = (n_bio + 1) / 2.0
                
                # Atmosphere
                data[y, x, 4] = (n_wx + 1) / 2.0 # 0.5 = No Wind
                data[y, x, 5] = (n_wy + 1) / 2.0 # 0.5 = No Wind
                data[y, x, 6] = (n_at + 1) / 2.0
                data[y, x, 7] = (n_ah + 1) / 2.0

        return data
