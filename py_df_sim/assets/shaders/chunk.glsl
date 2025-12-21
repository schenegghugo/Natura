#version 330 core

// --- VERTEX SHADER ---
#if defined(VERTEX_SHADER)

in vec2 in_vert; 
out vec2 v_uv;

uniform vec2 u_camera_pos;
uniform float u_zoom;
uniform float u_aspect_ratio;

// Chunk specific uniforms
uniform vec2 u_chunk_pos;  
uniform float u_chunk_size; 

void main() {
    v_uv = in_vert;

    // 1. Calculate World Position
    vec2 world_pos = (in_vert * u_chunk_size) + u_chunk_pos;

    // 2. Apply Camera 
    vec2 view_pos = (world_pos - u_camera_pos) * u_zoom;

    // 3. Aspect Ratio
    view_pos.x *= u_aspect_ratio;

    // 4. Output to Clip Space
    // Multiply by 2.0 to map World Unit (1.0) to NDC Range (2.0)
    gl_Position = vec4(view_pos * 2.0, 0.0, 1.0); 
}
#endif 


// --- FRAGMENT SHADER ---
#if defined(FRAGMENT_SHADER)

in vec2 v_uv;
out vec4 f_color;

uniform sampler2D u_texture; 

void main() {
    vec4 tex = texture(u_texture, v_uv);
    
    // Debug: Yellow border
    if (v_uv.x < 0.02 || v_uv.y < 0.02 || v_uv.x > 0.98 || v_uv.y > 0.98) {
        f_color = vec4(1.0, 1.0, 0.0, 1.0); 
    } else {
        f_color = tex;
    }
}
#endif
