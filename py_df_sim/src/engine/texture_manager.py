import moderngl
from config import CHUNK_SIZE

class TextureManager:
    def __init__(self, ctx, pool_size=64):
        self.ctx = ctx
        self.pool_size = pool_size
        
        # 1. Texture Array 0: TERRAIN (RGBA)
        self.terrain_array = ctx.texture_array((pool_size, CHUNK_SIZE, CHUNK_SIZE), 4, dtype='f4')
        self.terrain_array.filter = (moderngl.NEAREST, moderngl.NEAREST)
        
        # 2. Texture Array 1: ATMOSPHERE (RGBA)
        self.atmos_array = ctx.texture_array((pool_size, CHUNK_SIZE, CHUNK_SIZE), 4, dtype='f4')
        # Linear filter for clouds makes them look softer
        self.atmos_array.filter = (moderngl.LINEAR, moderngl.LINEAR) 

        self.available_indices = list(range(pool_size))
        self.node_to_texture_id = {}

    def update(self, visible_nodes, data_manager, generator): 
        # A. Identify needed keys
        needed_keys = set((n.x, n.y, n.level) for n in visible_nodes)
            
        # B. Garbage Collection
        for key in list(self.node_to_texture_id.keys()):
            if key not in needed_keys:
                tex_id = self.node_to_texture_id[key]
                del self.node_to_texture_id[key]
                self.available_indices.append(tex_id)

        # C. Loading
        for node in visible_nodes:
            key = (node.x, node.y, node.level)
            
            if key not in self.node_to_texture_id:
                if not self.available_indices:
                    continue
                
                tex_id = self.available_indices.pop()
                self.node_to_texture_id[key] = tex_id
                
                # 1. Get Data (8 Layers)
                chunk_data = data_manager.get_chunk(node.x, node.y, node.level)
                full_data = chunk_data.height_map 
                
                # 2. Split Data
                # Layers 0-3 -> Terrain
                terrain_bytes = full_data[:, :, 0:4].tobytes()
                
                # Layers 4-7 -> Atmos
                atmos_bytes = full_data[:, :, 4:8].tobytes()
                
                # 3. Write to Specific Layer in Texture Array
                # viewport defines which layer of the array we write to: (x, y, width, height, layer_index)
                # Ideally, texture_array.write handles 3D data, but for specific layers in an array, 
                # ModernGL requires passing the data for that specific slice.
                
                # NOTE: texture_array.write expects data for the WHOLE array or a viewport.
                # To write to a single layer Z, we calculate offsets.
                # Actually, simpler method in ModernGL for TextureArrays:
                # We can't easily write to just one layer index using standard .write without complex viewports.
                # BUT, since we built a texture_array, we treat it like a 3D texture.
                
                # Correction: The easiest way to manage this pool is actually unrelated to TextureArrays
                # if we want to write individually easily. 
                # HOWEVER, to keep your Quadtree logic fast, TextureArrays are best.
                
                # Let's use the specific write command for a layer:
                self.terrain_array.write(terrain_bytes, viewport=(0, 0, tex_id, CHUNK_SIZE, CHUNK_SIZE, 1))
                self.atmos_array.write(atmos_bytes, viewport=(0, 0, tex_id, CHUNK_SIZE, CHUNK_SIZE, 1))

    def bind_textures(self, location_terrain=0, location_atmos=1):
        """Binds the entire arrays to the shader units"""
        self.terrain_array.use(location=location_terrain)
        self.atmos_array.use(location=location_atmos)

    def get_texture_id(self, node):
        """Returns the Z-index (layer) in the array for this node"""
        key = (node.x, node.y, node.level)
        return self.node_to_texture_id.get(key, -1)
