import moderngl
from config import CHUNK_SIZE

class TextureManager:
    def __init__(self, ctx, pool_size=64):
        self.ctx = ctx
        self.pool_size = pool_size
        
        # 1. Pre-allocate VRAM
        # We create 'pool_size' empty textures immediately.
        # This is our "Budget". We cannot exceed this.
        self.textures = []
        for _ in range(pool_size):
            texture = self.ctx.texture((CHUNK_SIZE, CHUNK_SIZE), 4)
            
            # NEAREST = Pixelated look (Minecraft style)
            # LINEAR = Smooth look (Simcity style)
            texture.filter = (moderngl.NEAREST, moderngl.NEAREST) 
            texture.swizzle = 'RGBA'
            self.textures.append(texture)
            
        # 2. Tracking System
        # available: List of indices [0, 1, 2... 63] that are currently empty.
        self.available_indices = list(range(pool_size))
        
        # mapping: Dictionary linking a Chunk Coordinate to a Texture Index
        # Key: (x, y, level) -> Value: texture_index (int)
        self.node_to_texture_id = {}

    def update(self, visible_nodes, data_manager, generator): 
        """
        Syncs the GPU textures with the Quadtree.
        1. Deletes textures for chunks that went off-screen.
        2. Generates and Uploads textures for new chunks.
        """
        
        # A. Identify what is currently needed
        # We create a set of keys {(x,y,lvl), ...} for fast lookup
        needed_keys = set()
        for node in visible_nodes:
            needed_keys.add((node.x, node.y, node.level))
            
        # B. Garbage Collection (Unload old chunks)
        # Look at every chunk we currently have loaded
        # If it is NOT in the 'needed_keys' list, dump it.
        # We wrap keys() in list() because we are modifying the dictionary during iteration
        for key in list(self.node_to_texture_id.keys()):
            if key not in needed_keys:
                # 1. Get the texture index being used
                tex_id = self.node_to_texture_id[key]
                
                # 2. Remove from mapping
                del self.node_to_texture_id[key]
                
                # 3. Return the index to the free pool
                self.available_indices.append(tex_id)

        # C. Loading (Upload new chunks)
        for node in visible_nodes:
            key = (node.x, node.y, node.level)
            
            if key not in self.node_to_texture_id:
                if not self.available_indices:
                    continue
                
                tex_id = self.available_indices.pop()
                self.node_to_texture_id[key] = tex_id
                
                # --- CHANGED SECTION START ---
                
                # 1. Get Data (From RAM or Generator)
                chunk_data = data_manager.get_chunk(node.x, node.y, node.level)
                
                # 2. Convert Data to Pixels (Using the helper we made)
                pixel_data = generator.colorize_chunk(chunk_data.height_map)
                
                # --- CHANGED SECTION END ---
                
                self.textures[tex_id].write(pixel_data)

    def get_texture(self, node):
        """
        Returns the ModernGL texture object for a given node.
        Returns None if not loaded (shouldn't happen if update is called first).
        """
        key = (node.x, node.y, node.level)
        if key in self.node_to_texture_id:
            tex_id = self.node_to_texture_id[key]
            return self.textures[tex_id]
        return None
