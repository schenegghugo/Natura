#version 330 core

in vec2 v_uv;
out vec4 f_color;

// The texture we uploaded
uniform sampler2D u_world_texture;

void main() {
    // 1. Sample the texture at the current UV coordinate
    vec4 data = texture(u_world_texture, v_uv);
    
    // 2. Extract height from Red channel
    float height = data.r;
    
    // 3. Color Mapping
    vec3 color;
    
    if (height < 0.25) {
        color = vec3(0.1, 0.3, 0.8); // Deep Water (Blue)
    } else if (height < 0.3) {
        color = vec3(0.2, 0.5, 0.9); // Shallow Water (Light Blue)
    } else if (height < 0.35) {
        color = vec3(0.9, 0.8, 0.5); // Sand (Yellow/Tan)
    } else if (height < 0.7) {
        color = vec3(0.2, 0.7, 0.2); // Grass (Green)
    } else {
        color = vec3(0.5, 0.5, 0.5); // Mountain (Grey)
    }
    
    // 4. Output final color
    f_color = vec4(color, 1.0);
}
