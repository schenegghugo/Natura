#version 330 core

// --- VERTEX SHADER ---
#if defined(VERTEX_SHADER)

in vec2 in_vert; 
out vec2 v_uv;

uniform vec2 u_camera_pos;
uniform float u_zoom;
uniform float u_aspect_ratio;

uniform vec2 u_chunk_pos;  
uniform float u_chunk_size; 

void main() {
    v_uv = in_vert;
    vec2 world_pos = (in_vert * u_chunk_size) + u_chunk_pos;
    vec2 view_pos = (world_pos - u_camera_pos) * u_zoom;
    view_pos.x *= u_aspect_ratio;
    gl_Position = vec4(view_pos * 2.0, 0.0, 1.0); 
}
#endif 

// --- FRAGMENT SHADER ---
#if defined(FRAGMENT_SHADER)

in vec2 v_uv;
out vec4 f_color;

// We use sampler2DArray now!
uniform sampler2DArray u_terrain_arr;
uniform sampler2DArray u_atmos_arr;
uniform int u_layer; // Which slice of the array to read
uniform float u_time;

void main() {
    // 1. Read Terrain (Unit 0)
    // coordinate is vec3(u, v, layer)
    vec4 t_data = texture(u_terrain_arr, vec3(v_uv, u_layer));
    
    // 2. Read Atmosphere (Unit 1)
    vec4 a_data = texture(u_atmos_arr, vec3(v_uv, u_layer));
    
    // Unpack
    float h = t_data.r;
    float t_temp = t_data.g;
    float t_hum = t_data.b;
    
    float w_x = a_data.r; // Wind X
    float w_y = a_data.g; // Wind Y
    float a_temp = a_data.b;
    float a_hum = a_data.a; // Cloud Density

    // --- TERRAIN COLOR ---
    vec3 color;
    if (h < 0.5) {
        color = mix(vec3(0.0, 0.05, 0.2), vec3(0.0, 0.4, 0.8), h*2.0);
    } else {
        float elev = (h - 0.5) * 2.0;
        if (t_temp < 0.35) color = vec3(0.95, 0.95, 1.0); 
        else if (t_temp > 0.65) {
            if (t_hum < 0.3) color = vec3(0.9, 0.8, 0.5); 
            else color = vec3(0.05, 0.3, 0.05); 
        } else {
            if (t_hum < 0.4) color = vec3(0.6, 0.7, 0.2); 
            else color = vec3(0.1, 0.6, 0.1); 
        }
        color *= (0.8 + 0.2 * elev);
    }

    // --- ATMOSPHERE OVERLAYS ---
    
    // 1. Clouds
    // If air humidity is high, draw white clouds
    if (a_hum > 0.6) {
        float cloud_density = (a_hum - 0.6) * 2.5; // 0.0 to 1.0
        color = mix(color, vec3(1.0), cloud_density * 0.8);
        
        // 2. Rain / Snow
        // If it's cloudy and...
        if (a_hum > 0.75) {
            // Rain (Hot) vs Snow (Cold)
            if (a_temp < 0.35) {
                // SNOW (Sparkles)
                float noise = fract(sin(dot(v_uv * 50.0 + u_time * 0.1, vec2(12.9898,78.233))) * 43758.5453);
                if (noise > 0.9) color = vec3(1.0);
            } else {
                // RAIN (Blue streaks)
                // Use Wind Vector to angle the rain
                float rain_angle = (v_uv.x * w_x + v_uv.y * w_y) * 20.0 + u_time * 5.0;
                float rain_streak = fract(sin(rain_angle) * 43758.5453);
                if (rain_streak > 0.9) color = mix(color, vec3(0.6, 0.7, 1.0), 0.5);
            }
        }
    }
    
    // Debug: Visualize Wind Direction arrows? (Maybe later)

    f_color = vec4(color, 1.0);
}
#endif
