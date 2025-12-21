import moderngl
import numpy as np
import config

class ChunkRenderer:
    def __init__(self, ctx):
        self.ctx = ctx
        
        # Load the shader file
        with open("assets/shaders/chunk.glsl", "r") as f:
            full_source = f.read()

        # --- GLSL VERSION FIX ---
        # We need to inject #define VERTEX_SHADER *after* the #version tag.
        # 1. Split into lines
        lines = full_source.splitlines()
        
        # 2. Extract version (assuming it's the first line, which is standard)
        # If your file has comments at the top, this might need adjustment, 
        # but for now we assume line 0 is #version.
        version_line = lines[0] 
        rest_of_code = "\n".join(lines[1:])
        
        # 3. Construct the shaders
        # Result looks like:
        #   #version 330 core
        #   #define VERTEX_SHADER
        #   ... rest of code ...
        self.prog = self.ctx.program(
            vertex_shader=f"{version_line}\n#define VERTEX_SHADER\n{rest_of_code}",
            fragment_shader=f"{version_line}\n#define FRAGMENT_SHADER\n{rest_of_code}",
        )
            
        # Basic 0..1 Quad
        # Note: 0,0 is Bottom-Left, 1,1 is Top-Right
        vertices = np.array([
            0.0, 0.0,  # Bottom Left
            1.0, 0.0,  # Bottom Right
            0.0, 1.0,  # Top Left
            1.0, 1.0,  # Top Right
        ], dtype='f4')
        
        self.vbo = self.ctx.buffer(vertices.tobytes())
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f', 'in_vert')])

    def render(self, visible_nodes, texture_manager, camera_pos, zoom):
        self.ctx.enable(moderngl.BLEND)
        
        # 1. Set Global Uniforms (Once per frame)
        self.prog['u_camera_pos'].value = tuple(camera_pos)
        self.prog['u_zoom'].value = zoom
        self.prog['u_aspect_ratio'].value = config.SCREEN_HEIGHT / config.SCREEN_WIDTH
        
        # 2. Iterate and Render
        for node in visible_nodes:
            # A. Get the specific texture for this chunk
            tex = texture_manager.get_texture(node)
            
            if tex:
                # B. Bind it to Texture Unit 0
                tex.use(location=0)
                self.prog['u_texture'].value = 0
                
                # C. Set Position/Size Uniforms
                self.prog['u_chunk_pos'].value = node.uv_pos 
                self.prog['u_chunk_size'].value = node.size
                
                # D. Draw
                self.vao.render(moderngl.TRIANGLE_STRIP)
