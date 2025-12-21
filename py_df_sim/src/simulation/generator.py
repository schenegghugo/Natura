import numpy as np
import noise
from config import CHUNK_SIZE

class TerrainGenerator:
    def __init__(self, seed=None):
        self.seed = seed if seed else np.random.randint(0, 1000)
        
        # INCREASED SCALE: 
        # 0.005 was too zoomed in (making it look like gradients/stretched lines).
        # 0.02 lets us see "Features" (blobs, hills) within a single chunk.
        self.base_scale = 0.02 
        
        self.octaves = 4      # Reduced from 6 for speed
        self.persistence = 0.5
        self.lacunarity = 2.0

    def generate_chunk_data(self, cx, cy, level):
        """
        Generates heightmap for a specific chunk.
        """
        # 1. Calculate Step Size based on Zoom Level
        step = self.base_scale / (2 ** level)
        
        # 2. World Offsets
        # We use a large multiplier (10000) for the seed to ensure different seeds 
        # look vastly different, but we add it to the coordinates.
        world_offset_x = (cx * CHUNK_SIZE * step) + self.seed
        world_offset_y = (cy * CHUNK_SIZE * step) + self.seed
        
        # 3. Pre-allocate the array
        data = np.zeros((CHUNK_SIZE, CHUNK_SIZE), dtype=np.float32)
        
        # 4. The Loop
        # We iterate through every pixel of the chunk.
        for y in range(CHUNK_SIZE):
            # Calculate the global Y coordinate for this row
            global_y = world_offset_y + (y * step)
            
            for x in range(CHUNK_SIZE):                
                # Calculate the global X coordinate for this column
                global_x = world_offset_x + (x * step)
                
                # Generate Noise
                # IMPORTANT: We removed 'repeatx' and 'repeaty'. 
                # This allows the noise to be truly infinite.
                n = noise.pnoise2(
                    global_x, 
                    global_y, 
                    octaves=self.octaves, 
                    persistence=self.persistence, 
                    lacunarity=self.lacunarity
                )
                data[y, x] = n

        # Normalize [-1, 1] -> [0, 1]
        data = (data + 1) / 2.0
        
        # FIX: DO NOT FLIP. 
        # Index 0 is Low Y. OpenGL puts Index 0 at Bottom. 
        # This matches perfectly.
        return data

    def generate_chunk_texture(self, cx, cy, level):
        height_map = self.generate_chunk_data(cx, cy, level)
        
        # Create RGBA array
        texture_data = np.zeros((CHUNK_SIZE, CHUNK_SIZE, 4), dtype=np.uint8)
        
        # Determine Water/Land
        water_mask = height_map < 0.5
        land_mask = ~water_mask
        
        # Water: Blue
        texture_data[water_mask] = [0, 0, 200, 255]
        
        # Land: Green Gradient
        # Map height 0.5-1.0 to color 50-255
        land_heights = height_map[land_mask]
        
        # Normalize land heights to 0.0 - 1.0 relative to land mass
        # (val - min) / (max - min)
        # Note: We safeguard against division by zero if a chunk is perfectly flat
        val_norm = (land_heights - 0.5) * 2.0 
        
        green_vals = (val_norm * 200 + 55).astype(np.uint8)
        
        # We need to assign this properly to the green channel
        # Advanced indexing in numpy can be tricky with multiple dimensions.
        # Let's do it explicitly:
        
        # Create a temporary land color array
        land_colors = np.zeros((np.count_nonzero(land_mask), 4), dtype=np.uint8)
        land_colors[:, 0] = 0           # R
        land_colors[:, 1] = green_vals  # G
        land_colors[:, 2] = 0           # B
        land_colors[:, 3] = 255         # A
        
        texture_data[land_mask] = land_colors
        
        return texture_data.tobytes()
