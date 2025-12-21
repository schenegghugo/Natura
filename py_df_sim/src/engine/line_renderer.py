import moderngl
import numpy as np
import config

class LineRenderer:
    def __init__(self, ctx):
        self.ctx = ctx
        
        # 1. UPDATED SHADER with Aspect Ratio
        self.prog = self.ctx.program(
            vertex_shader="""
            #version 330 core
            in vec2 in_vert;
            
            uniform vec2 u_camera_pos;
            uniform float u_zoom;
            uniform float u_aspect_ratio; // <--- ADDED
            
            void main() {
                vec2 offset = in_vert - u_camera_pos;
                vec2 zoomed = offset * u_zoom;
                
                // Fix Aspect Ratio (Same as ChunkRenderer)
                zoomed.x *= u_aspect_ratio; 
                
                // Convert to NDC
                gl_Position = vec4(zoomed.x * 2.0, zoomed.y * 2.0, 0.0, 1.0);
            }
            """,
            fragment_shader="""
            #version 330 core
            out vec4 f_color;
            void main() {
                f_color = vec4(1.0, 0.0, 0.0, 1.0);
            }
            """
        )
        self.vbo = self.ctx.buffer(reserve=4 * 8 * 1024) 
        self.vao = self.ctx.vertex_array(self.prog, [(self.vbo, '2f', 'in_vert')])

    def render(self, nodes, camera_pos, zoom):
        # ... (Vertex generation code stays the same) ...
        # ... (Looping through nodes and creating vertices) ...
        vertices = []
        for node in nodes:
            u, v = node.uv_pos
            s = node.size
            l, t, r, b = u, v, u+s, v+s
            vertices.extend([l, t, r, t, r, t, r, b, r, b, l, b, l, b, l, t])

        if not vertices: return

        data = np.array(vertices, dtype='f4')
        self.vbo.write(data.tobytes())
        
        # 2. UPDATE UNIFORMS
        self.prog['u_camera_pos'].value = tuple(camera_pos)
        self.prog['u_zoom'].value = zoom
        self.prog['u_aspect_ratio'].value = config.SCREEN_HEIGHT / config.SCREEN_WIDTH # <--- ADDED
        
        self.vao.render(moderngl.LINES, vertices=len(vertices)//2)
