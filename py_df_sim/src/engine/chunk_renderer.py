import moderngl
import numpy as np
import os
import time
import config

class ChunkRenderer:
    def __init__(self, ctx):
        self.ctx = ctx
        
        # --- PATH LOGIC ---
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
        
        # Compile one program for both stages
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

    def render(self, visible_nodes, texture_manager, camera_pos, zoom, celestials):        
        """
        Renders the visible chunks using texture arrays.
        Args:
            visible_nodes: List of ChunkNode objects
            texture_manager: The texture manager instance
            camera_pos: Tuple (x, y)
            zoom: Float
            celestials: The Celestials simulation instance (handles orbits)
        """
        # Enable Alpha Blending (Crucial for Atmosphere/clouds/water transparency)
        self.ctx.enable(moderngl.BLEND)
        self.ctx.blend_func = moderngl.SRC_ALPHA, moderngl.ONE_MINUS_SRC_ALPHA
        
        # -----------------------------------------------------------------
        # 1. CAMERA & SYSTEM UNIFORMS
        # -----------------------------------------------------------------
        if 'u_camera_pos' in self.prog:
            self.prog['u_camera_pos'].value = tuple(camera_pos)
        if 'u_zoom' in self.prog:
            self.prog['u_zoom'].value = zoom
        if 'u_aspect_ratio' in self.prog:
            self.prog['u_aspect_ratio'].value = config.SCREEN_HEIGHT / config.SCREEN_WIDTH
        
        # System Time (for rain/water animations, distinct from game time)
        if 'u_time' in self.prog:
            self.prog['u_time'].value = time.time()

        # -----------------------------------------------------------------
        # 2. GEOGRAPHY UNIFORMS (Coordinate System)
        # -----------------------------------------------------------------
        if 'u_WorldScale' in self.prog:
            self.prog['u_WorldScale'].value = config.WORLD_SCALE
        
        if 'u_GlobalOffset' in self.prog:
            offset = getattr(config, 'GLOBAL_OFFSET', (0.0, 0.0)) 
            self.prog['u_GlobalOffset'].value = offset

        # -----------------------------------------------------------------
        # 3. ORBITAL UNIFORMS (The Celestials System)
        # -----------------------------------------------------------------
        # These values drive the day/night cycle and seasons in the shader
        
        # SUN
        if 'u_SolarDeclination' in self.prog:
            self.prog['u_SolarDeclination'].value = celestials.solar_declination
        if 'u_GHA' in self.prog:
            self.prog['u_GHA'].value = celestials.greenwich_hour_angle
            
        # MOON
        if 'u_LunarDeclination' in self.prog:
            self.prog['u_LunarDeclination'].value = celestials.lunar_declination
        if 'u_LunarGHA' in self.prog:
            self.prog['u_LunarGHA'].value = celestials.lunar_gha

        # -----------------------------------------------------------------
        # 4. TEXTURE BINDING
        # -----------------------------------------------------------------
        texture_manager.bind_textures(location_terrain=0, location_atmos=1)
        
        if 'u_terrain_arr' in self.prog:
            self.prog['u_terrain_arr'].value = 0
        if 'u_atmos_arr' in self.prog:
            self.prog['u_atmos_arr'].value = 1
        
        # -----------------------------------------------------------------
        # 5. RENDER LOOP
        # -----------------------------------------------------------------
        for node in visible_nodes:
            layer_id = texture_manager.get_texture_id(node)
            
            if layer_id != -1:
                # Position: Where is this chunk?
                if 'u_chunk_pos' in self.prog:
                    self.prog['u_chunk_pos'].value = node.uv_pos 
                
                # Size: How big is this chunk?
                if 'u_chunk_size' in self.prog:
                    self.prog['u_chunk_size'].value = node.size
                
                # Layer: Which slice of the array?
                if 'u_layer' in self.prog:
                    self.prog['u_layer'].value = layer_id
                
                # Draw
                self.vao.render(moderngl.TRIANGLE_STRIP)
