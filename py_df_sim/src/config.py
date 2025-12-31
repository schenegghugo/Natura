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

# --- PLANETARY DIMENSIONS ---
# How many game units (meters/pixels) represent one degree of latitude?
# Earth is approx 111km per degree.
# For a game, you usually want this smaller so players can actually travel between biomes.
WORLD_SCALE = 1000.0  # 1000 units = 1 degree of latitude/longitude.
GLOBAL_OFFSET = (0.0, 0.0)  # Offset to center the map (if needed)

# Bounds
MAX_LATITUDE = 90.0
MIN_LATITUDE = -90.0
MAX_LONGITUDE = 180.0
MIN_LONGITUDE = -180.0

# Optional: Offset the starting position (0,0) to be somewhere specific
# 50 degrees * 1000 scale = 50,000 Y offset
GLOBAL_OFFSET = (0.0, 0.0) 

# --- CHRONOS (TIME) SETTINGS ---
# How many real-world seconds equal one in-game day?
# 60.0 = 1 minute per day (Fast, good for testing)
# 1200.0 = 20 minutes per day (Minecraft speed)
REAL_SECONDS_PER_GAME_DAY = 60.0 

# Calendar
DAYS_PER_YEAR = 360  # Simplifies math (12 months of 30 days), or use 365
STARTING_HOUR = 12.0 # Noon
