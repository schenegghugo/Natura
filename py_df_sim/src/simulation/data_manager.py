from simulation.chunk_data import ChunkData

class DataManager:
    def __init__(self, generator, save_manager):
        self.generator = generator
        self.save_manager = save_manager  # Reference to the Save System
        
        # The RAM Cache: Dictionary mapping (x, y, level) -> ChunkData object
        self.loaded_chunks = {}

    def get_chunk(self, x, y, level):
        """
        Returns a ChunkData object.
        Priority:
        1. RAM (Fastest)
        2. Disk (Fast)
        3. Generator (Slowest - creates new data)
        """
        key = (x, y, level)
        
        # 1. RAM CHECK
        # If we have it in memory, return it immediately.
        if key in self.loaded_chunks:
            return self.loaded_chunks[key]
        
        # 2. DISK CHECK
        # Ask the SaveManager if this file exists on the hard drive.
        height_map = self.save_manager.load_chunk_data(x, y, level)
        
        if height_map is not None:
            # We found it on disk! 
            # Wrap the raw numpy array in our ChunkData object.
            chunk = ChunkData(x, y, level, height_map)
        else:
            # 3. GENERATOR FALLBACK
            # It's not in RAM and not on Disk. It is "Void".
            # We must generate it from scratch using the math.
            height_map = self.generator.generate_chunk_data(x, y, level)
            chunk = ChunkData(x, y, level, height_map)
        
        # Store the result in RAM so we don't look it up again next frame.
        self.loaded_chunks[key] = chunk
        
        return chunk

    def save_all_loaded_chunks(self):
        """
        Iterates through all chunks currently in RAM and saves them to disk.
        Useful for 'Save Game' functionality.
        """
        print(f"Saving {len(self.loaded_chunks)} chunks to disk...")
        for key, chunk in self.loaded_chunks.items():
            # In a real optimization, we would only save chunks where 
            # chunk.is_dirty == True (chunks that changed).
            # For now, we save everything to be safe.
            self.save_manager.save_chunk(chunk)

    def prune(self, visible_nodes):
        """
        Optional: Removes chunks from RAM that are very far away.
        If RAM usage gets high, we implement logic here to delete keys 
        from self.loaded_chunks that aren't in visible_nodes.
        """
        pass
