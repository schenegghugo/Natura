#version 330 core

// --- VERTEX SHADER ---
#if defined(VERTEX_SHADER)

in vec2 in_vert; 

// Outputs to Fragment Shader
out vec2 v_uv;       // Texture coordinates (0.0 to 1.0)
out vec2 v_LatLon;   // Global Coordinates (x=Longitude, y=Latitude)

// Camera / View Uniforms
uniform vec2 u_camera_pos;
uniform float u_zoom;
uniform float u_aspect_ratio;

// Chunk Positioning Uniforms
uniform vec2 u_chunk_pos;   // The world position of this chunk (Bottom-Left)
uniform float u_chunk_size; // The width/height of this chunk

// Geography Uniforms
uniform float u_WorldScale;   // How many units = 1 degree?
uniform vec2 u_GlobalOffset;  // Optional world center offset

void main() {
    v_uv = in_vert;

    // 1. Calculate Absolute World Position (Game Units)
    vec2 world_pos = (in_vert * u_chunk_size) + u_chunk_pos;

    // 2. Calculate Geographic Coordinates (Degrees)
    vec2 geo_pos = world_pos + u_GlobalOffset;

    // Convert Units -> Degrees
    float lon = geo_pos.x / u_WorldScale;
    float lat = geo_pos.y / u_WorldScale;

    // Clamp Latitude to Poles (-90 to 90)
    lat = clamp(lat, -90.0, 90.0);
    
    // Pass to Fragment Shader
    v_LatLon = vec2(lon, lat);

    // 3. Standard Camera Projection
    vec2 view_pos = (world_pos - u_camera_pos) * u_zoom;
    view_pos.x *= u_aspect_ratio;
    
    // Convert to Clip Space (-1.0 to 1.0)
    gl_Position = vec4(view_pos * 2.0, 0.0, 1.0); 
}
#endif 

// --- FRAGMENT SHADER ---
#if defined(FRAGMENT_SHADER)

in vec2 v_uv;
in vec2 v_LatLon; // Received from Vertex Shader

out vec4 f_color;

// Texture Arrays
uniform sampler2DArray u_terrain_arr;
uniform sampler2DArray u_atmos_arr;
uniform int u_layer; 
uniform float u_time; // Engine time (seconds) for rain animation

// --- CELESTIAL UNIFORMS ---
// Provided by src/simulation/celestials.py

// The Sun
uniform float u_SolarDeclination; 
uniform float u_GHA;              

// The Moon
uniform float u_LunarDeclination; 
uniform float u_LunarGHA;         

// --- HELPER FUNCTION: ORBITAL MATH ---
// Calculates the intensity (Cosine of Zenith Angle) for any celestial body
// 1.0 = Overhead, 0.0 = Horizon, < 0.0 = Below Horizon
float getCelestialIntensity(float lat_deg, float lon_deg, float declination, float gha) {
    
    // Convert current pixel coordinates to Radians for Trig
    float lat = radians(lat_deg);
    float lon = radians(lon_deg);

    // 1. Calculate Local Hour Angle (LHA)
    // The celestial body's position relative to THIS longitude.
    float LHA = gha + lon; 

    // 2. Spherical Trigonometry (The Cosine Zenith Formula)
    // Formula: sin(Lat)sin(Dec) + cos(Lat)cos(Dec)cos(LHA)
    float sin_phi = sin(lat);
    float cos_phi = cos(lat);
    float sin_delta = sin(declination);
    float cos_delta = cos(declination);
    float cos_h = cos(LHA);

    float elevation = (sin_phi * sin_delta) + (cos_phi * cos_delta * cos_h);

    // 3. Return Intensity (Clamped)
    // We ignore negative values (Night/Below Horizon)
    return max(0.0, elevation);
}

void main() {
    // ---------------------------------------------------------
    // 1. EXISTING BIOME & WEATHER LOGIC
    // ---------------------------------------------------------
    
    // Read Data
    vec4 t_data = texture(u_terrain_arr, vec3(v_uv, u_layer));
    vec4 a_data = texture(u_atmos_arr, vec3(v_uv, u_layer));
    
    // Unpack
    float h = t_data.r;
    float t_temp = t_data.g;
    float t_hum = t_data.b;
    
    float w_x = a_data.r; 
    float w_y = a_data.g; 
    float a_temp = a_data.b;
    float a_hum = a_data.a; 

    // Calculate Biome Color
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

    // Weather Overlays
    if (a_hum > 0.6) {
        float cloud_density = (a_hum - 0.6) * 2.5; 
        color = mix(color, vec3(1.0), cloud_density * 0.8);
        
        if (a_hum > 0.75) {
            if (a_temp < 0.35) {
                float noise = fract(sin(dot(v_uv * 50.0 + u_time * 0.1, vec2(12.9898,78.233))) * 43758.5453);
                if (noise > 0.9) color = vec3(1.0);
            } else {
                float rain_angle = (v_uv.x * w_x + v_uv.y * w_y) * 20.0 + u_time * 5.0;
                float rain_streak = fract(sin(rain_angle) * 43758.5453);
                if (rain_streak > 0.9) color = mix(color, vec3(0.6, 0.7, 1.0), 0.5);
            }
        }
    }
    
    // ---------------------------------------------------------
    // 2. ORBITAL LIGHTING (Physically Based)
    // ---------------------------------------------------------
    
    // A. Sun Intensity
    float sun_intensity = getCelestialIntensity(v_LatLon.y, v_LatLon.x, u_SolarDeclination, u_GHA);
    
    // B. Moon Intensity
    float moon_intensity = getCelestialIntensity(v_LatLon.y, v_LatLon.x, u_LunarDeclination, u_LunarGHA);
    
    // C. Light Configuration
    // Sun: Warm, yellowish, very bright (Intensity 1.0)
    vec3 sun_light = vec3(1.0, 0.98, 0.9) * sun_intensity * 1.0;
    
    // Moon: Cold, blue-ish, dim (Intensity 0.25 max)
    // Note: 0.25 is actually quite bright for moonlight (gameplay visibility),
    // physically it would be ~0.002, but that's too dark for a game.
    vec3 moon_light = vec3(0.6, 0.7, 1.0) * moon_intensity * 0.25;
    
    // Ambient: Starlight / Atmosphere scattering.
    // Prevents pitch black shadows.
    vec3 ambient_light = vec3(0.05, 0.05, 0.08);
    
    // D. Combine
    // The lights are additive.
    // If Sun and Moon are both up (e.g., afternoon), the moon adds a tiny tint, but sun dominates.
    // If only Moon is up (e.g., full moon night), it provides the main light.
    vec3 total_light = ambient_light + sun_light + moon_light;
    
    // E. Apply to Biome Color
    f_color = vec4(color * total_light, 1.0);
}
#endif
