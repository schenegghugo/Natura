import numpy as np

class ChunkData:
    """
    Holds the pure gameplay data for a specific chunk.
    This is decoupled from OpenGL or Visuals.
    """
    def __init__(self, x, y, level, height_map):
        self.x = x
        self.y = y
        self.level = level
        
        # The core data: A 2D numpy array of floats (0.0 to 1.0)
        self.height_map = height_map
        
        # Flags for the future
        self.is_dirty = False  # If True, needs to be re-saved to disk
        self.needs_texture_update = False # If True, GPU needs a new texture
