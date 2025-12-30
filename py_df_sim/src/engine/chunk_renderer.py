import moderngl
import numpy as np
import os
import time
import config

class ChunkRenderer:
    def __init__(self, ctx):
        self.ctx = ctx
        
        # --- PATH LOGIC (Preserved) ---
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(script_dir))
        shader_path = os.path.join(project_root, "assets", "shaders", "chunk.glsl")

        # Load the shader source
        try:
            with open(shader_path, "r") as f:
                full_source = f.read()
        except FileNotFoundError:
            print(f"ERROR: Shader file not found at: {shader_path}")
            raise

        # --- SHADER COMPILATION ---
        lines = full_source.splitlines()
        version_line = lines[0] 
        rest_of_code = "\n".join(lines[1:])
        
        self.prog = self.ctx.program(
            vertex_shader=f"{version_line}\n#define VERTEX_SHADER\n{rest_of_code}",
            fragment_shader=f"{version_line}\n#define FRAGMENT_SHADER\n{rest_of_code}",
        )
            
        # Basic Quad (0,0 to 1,1)
        vertices = np.array([
            0.0, 0.0,
            1.0, 0.0,
            0.0, 1.0,
            1.0, 1.0,
        ], dtype='f4')
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f', 'in_vert')])

    def render(self, visible_nodes, texture_manager, camera_pos, zoom):
        # Enable Alpha Blending (Crucial for Atmosphere/clouds)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # 1. Set Global Uniforms
        self.prog['u_camera_pos'].value = tuple(camera_pos)
        self.prog['u_zoom'].value = zoom
        self.prog['u_aspect_ratio'].value = config.SCREEN_HEIGHT / config.SCREEN_WIDTH
        self.prog['u_time'].value = time.time() # Used for rain/snow animation
        
        # 2. Bind Texture Arrays
        # Instead of binding one texture per chunk, we bind the two massive arrays once.
        # Unit 0 = Terrain Array
        # Unit 1 = Atmosphere Array
        texture_manager.bind_textures(location_terrain=0, location_atmos=1)
        
        # Tell the shader which texture unit corresponds to which sampler
        self.prog['u_terrain_arr'].value = 0
        self.prog['u_atmos_arr'].value = 1
        
        # 3. Render Loop
        for node in visible_nodes:
            # We need to know which "Slice" (Layer ID) of the array contains this chunk's data
            layer_id = texture_manager.get_texture_id(node)
            
            # If layer_id is -1, the texture isn't loaded yet, so skip rendering
            if layer_id != -1:
                # Set Chunk Positioning
                self.prog['u_chunk_pos'].value = node.uv_pos 
                self.prog['u_chunk_size'].value = node.size
                
                # Set the Layer Index so the shader reads the correct data slice
                self.prog['u_layer'].value = layer_id
                
                # Draw the Quad
                self.vao.render(moderngl.TRIANGLE_STRIP)
