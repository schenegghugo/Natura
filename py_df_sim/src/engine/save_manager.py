import os
import json
import numpy as np
import config

SAVE_DIR = "saves/default"

class SaveManager:
    def __init__(self):
        self.ensure_save_directory()

    def ensure_save_directory(self):
        if not os.path.exists(SAVE_DIR):
            os.makedirs(SAVE_DIR)
        
        # Subfolder for chunk arrays
        chunks_dir = os.path.join(SAVE_DIR, "chunks")
        if not os.path.exists(chunks_dir):
            os.makedirs(chunks_dir)

    def save_global_state(self, seed, camera):
        """Saves seed and camera position to a JSON file."""
        data = {
            "seed": seed,
            "camera_x": camera.pos[0],
            "camera_y": camera.pos[1],
            "zoom": camera.zoom
        }
        
        path = os.path.join(SAVE_DIR, "world.json")
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)
        print("Global state saved.")

    def load_global_state(self):
        """Returns a dict of global state, or None if no save exists."""
        path = os.path.join(SAVE_DIR, "world.json")
        if not os.path.exists(path):
            return None
            
        with open(path, 'r') as f:
            return json.load(f)

    def save_chunk(self, chunk_data):
        """Saves a single ChunkData object to .npy file."""
        # Filename format: chunk_x_y_level.npy
        filename = f"chunk_{chunk_data.x}_{chunk_data.y}_{chunk_data.level}.npy"
        path = os.path.join(SAVE_DIR, "chunks", filename)
        
        np.save(path, chunk_data.height_map)

    def load_chunk_data(self, x, y, level):
        """
        Attempts to load chunk heightmap from disk.
        Returns numpy array if found, None if not.
        """
        filename = f"chunk_{x}_{y}_{level}.npy"
        path = os.path.join(SAVE_DIR, "chunks", filename)
        
        if os.path.exists(path):
            return np.load(path)
        return None
