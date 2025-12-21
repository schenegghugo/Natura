import numpy as np
import noise
import config

class World:
    def __init__(self):
        self.size = config.WORLD_SIZE  # 512
        # Create a 3D array: Width x Height x 4 Channels (RGBA)
        # We use 32-bit floats (0.0 to 1.0)
        self.data = np.zeros((self.size, self.size, 4), dtype=np.float32)
        
        self.generate_world()

    def generate_world(self):
        print(f"Generating World ({self.size}x{self.size})...")
        
        scale = 100.0       # "Zoom" level of the noise
        octaves = 6         # Detail level
        persistence = 0.5   # How much detail affects shape
        lacunarity = 2.0    # Detail frequency
        
        center_x, center_y = self.size / 2, self.size / 2

        # Iterate over every pixel
        for y in range(self.size):
            for x in range(self.size):
                
                # 1. Generate Perlin Noise
                # We divide by scale to "zoom in"
                # base=42 is the seed
                nx = x / scale
                ny = y / scale
                h = noise.pnoise2(nx, ny, octaves=octaves, persistence=persistence, 
                                  lacunarity=lacunarity, repeatx=1024, repeaty=1024, base=42)
                
                # Noise outputs -1.0 to 1.0 roughly. Normalize to 0.0 to 1.0
                h = (h + 1) / 2.0

                # 2. Apply Island Mask (Circular Gradient)
                dx = x - center_x
                dy = y - center_y
                distance = np.sqrt(dx*dx + dy*dy)
                
                # Normalize distance: 0.0 at center, 1.0 at edge
                max_width = self.size * 0.5
                gradient = distance / max_width
                
                # Subtract gradient from height.
                # Center (gradient 0) keeps original height.
                # Edges (gradient 1) get pushed down into negative (water).
                final_height = h - (gradient * 0.8)
                
                # Clamp between 0.0 and 1.0
                final_height = max(0.0, min(1.0, final_height))
                
                # 3. Write Data
                # R = Height, G/B = 0 (unused yet), A = 1 (Opaque)
                self.data[y, x, 0] = final_height
                self.data[y, x, 3] = 1.0
