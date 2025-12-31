import numpy as np
import noise
import math
from config import CHUNK_SIZE

class TerrainGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed else 12345
        
        # Scale Settings
        self.base_scale = 0.02 
        self.octaves = 4
        self.persistence = 0.5
        self.lacunarity = 2.0
        
        # Exponent for terrain sharpness
        # 1.0 = Linear
        # 3.0 = Cubic (Flat coasts, Deep Trenches, Steep Peaks)
        self.height_exponent = 3.0 
        
        # Layer Offsets
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
        """
        # 1. Calculate Step Size
        step = self.base_scale / (2 ** level)
        
        # 2. Base World Offsets
        base_wx = (cx * CHUNK_SIZE * step) + self.seed
        base_wy = (cy * CHUNK_SIZE * step) + self.seed
        
        # 3. Pre-allocate array
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE, 8), dtype=np.float32)
        
        # 4. Loop through pixels
        for y in range(CHUNK_SIZE):
            global_y = base_wy + (y * step)
            
            for x in range(CHUNK_SIZE):                
                global_x = base_wx + (x * step)
                
                # --- TERRAIN GENERATION (Layers 0-3) ---
                                
                # 1. Raw Height Noise (-1.0 to 1.0)
                n_height = noise.pnoise2(
                    global_x, 
                    global_y, 
                    octaves=self.octaves, 
                    persistence=self.persistence, 
                    lacunarity=self.lacunarity
                )
                
                # 2. Normalize to 0.0 -> 1.0
                h_norm = (n_height + 1) / 2.0
                
                # 3. Apply Polynomial Curve (x^3 + x)
                # This creates a "rolling" slope at sea level (linear) 
                # but still gets steeper towards peaks and trenches.
                
                # Shift to -1..1 (and clamp to prevent noise artifacts exploding)
                h_signed = max(-1.0, min(1.0, (h_norm - 0.5) * 2.0))
                
                # Apply f(x) = x^3 + x
                # Resulting range is approx -2.0 to 2.0
                h_poly = (h_signed ** 3) + h_signed
                
                # Normalize polynomial result back to -1..1
                # We divide by 2.0 because the max possible value is (1^3 + 1) = 2
                h_curved = h_poly / 2.0
                
                # Shift back to 0..1 for storage
                h_final = (h_curved / 2.0) + 0.5                
                # ----------------------------------------------------

                # Temperature
                n_temp = self._get_noise(global_x, global_y, self.offsets['temp'], scale_mod=0.5)
                
                # Humidity
                n_hum = self._get_noise(global_x, global_y, self.offsets['hum'], scale_mod=0.5)
                
                # Biomass
                n_bio = self._get_noise(global_x, global_y, self.offsets['bio'], scale_mod=2.0, octaves=1)

                # --- ATMOSPHERE GENERATION (Layers 4-7) ---
                n_wx = self._get_noise(global_x, global_y, self.offsets['wind_x'], scale_mod=0.3)
                n_wy = self._get_noise(global_x, global_y, self.offsets['wind_y'], scale_mod=0.3)
                n_at = self._get_noise(global_x, global_y, self.offsets['air_t'], scale_mod=0.4)
                n_ah = self._get_noise(global_x, global_y, self.offsets['air_h'], scale_mod=1.5)

                # --- STORAGE ---
                data[y, x, 0] = h_final  # Storing the curved height
                data[y, x, 1] = (n_temp + 1) / 2.0
                data[y, x, 2] = (n_hum + 1) / 2.0
                data[y, x, 3] = (n_bio + 1) / 2.0
                
                data[y, x, 4] = (n_wx + 1) / 2.0 
                data[y, x, 5] = (n_wy + 1) / 2.0 
                data[y, x, 6] = (n_at + 1) / 2.0
                data[y, x, 7] = (n_ah + 1) / 2.0

        return data
