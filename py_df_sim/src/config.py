# src/config.py
# Global Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# OpenGL Context Settings
GL_MAJOR_VERSION = 3
GL_MINOR_VERSION = 3

# World Generation
WORLD_SIZE = 512  # 512x512 Grid will need to unify a single variable for generator.py, texture_manager.py since world is infinte WORLD_SIZE is legacy.
# Engine Settings
CHUNK_SIZE = 64   # Resolution of one texture (512x512 pixels)
SEED = 42
TILE_SIZE = 4     # How big a pixel/tile looks on screen
