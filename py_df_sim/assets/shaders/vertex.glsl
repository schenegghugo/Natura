#version 330 core

in vec2 in_vert;
out vec2 v_uv;

uniform vec2 u_camera_pos; // Center of the screen in UV space (0.0 to 1.0)
uniform float u_zoom;      // Scale factor (1.0 = zoomed out, larger = zoomed in)

void main() {
    gl_Position = vec4(in_vert, 0.0, 1.0);
    
    // 1. Calculate Base UV (0.0 to 1.0)
    vec2 base_uv = (in_vert + 1.0) * 0.5;
    
    // 2. Apply Camera Transform
    // Logic: 
    // a. Center the UVs around (0,0) by subtracting 0.5
    // b. Scale them by (1.0 / zoom) - High zoom means smaller UV range
    // c. Add the camera position
    
    v_uv = (base_uv - 0.5) * (1.0 / u_zoom) + u_camera_pos;
}
