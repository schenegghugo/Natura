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
        Removes chunks from RAM that are no longer visible.
        """
        # 1. Identify keys to remove
        current_keys = set(self.loaded_chunks.keys())
        
        # FIX: Construct the tuple manually from node attributes
        visible_keys = set((n.x, n.y, n.level) for n in visible_nodes)
        
        # Calculate difference (Items in RAM but NOT in View)
        to_remove = current_keys - visible_keys
        
        # 2. Delete them
        for key in to_remove:
            # We assume "dirty" chunks are mostly new generated ones.
            # If we delete a dirty chunk without saving, that work is lost.
            # However, auto-saving on prune causes stutter.
            # For now, we accept that uncached data is lost until F5 is pressed.
            del self.loaded_chunks[key]
            
        # Optional debug (Uncomment to see memory cleanup in action)
        if len(to_remove) > 0:
            print(f"Pruned {len(to_remove)} chunks. RAM: {len(self.loaded_chunks)}")
