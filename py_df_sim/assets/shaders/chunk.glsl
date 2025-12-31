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
in vec2 v_LatLon; 

out vec4 f_color;

uniform sampler2DArray u_terrain_arr;
uniform sampler2DArray u_atmos_arr;
uniform int u_layer; 
uniform float u_time; 

// Celestials
uniform float u_SolarDeclination; 
uniform float u_GHA;              
uniform float u_LunarDeclination; 
uniform float u_LunarGHA;         
uniform float u_MoonPhase; // 0.0 (New) to 1.0 (Full)

// Terrain settings
uniform float u_HeightScale; 
uniform float u_TexRes;      

// ----------------------------------------------------------------------------
// ATMOSPHERIC SCATTERING COLORS
// ----------------------------------------------------------------------------

vec3 getSunColor(float elevation) {
    vec3 c_noon = vec3(1.0, 0.98, 0.90);
    vec3 c_gold = vec3(1.0, 0.6, 0.3);
    vec3 c_sunset = vec3(1.0, 0.2, 0.1);
    vec3 c_dusk = vec3(0.1, 0.1, 0.35);

    if (elevation > 0.3) {
        return mix(c_gold, c_noon, min(1.0, (elevation - 0.3) * 2.0));
    } else if (elevation > 0.05) {
        return mix(c_sunset, c_gold, (elevation - 0.05) * 4.0);
    } else if (elevation > -0.1) {
        return mix(c_dusk, c_sunset, (elevation + 0.1) * 6.6);
    } else {
        return c_dusk * 0.2; 
    }
}

// ----------------------------------------------------------------------------
// MATH HELPERS
// ----------------------------------------------------------------------------

float getHeight(vec2 uv) {
    return texture(u_terrain_arr, vec3(uv, u_layer)).r;
}

// 2. Calculate Surface Normal (The Slope)
vec3 getNormal(vec2 uv, float scale) {
    float h = getHeight(uv);
    
    // --- FORCE FLAT WATER ---
    // If the pixel is below sea level (0.5), we force the normal to point
    // straight up (0,0,1). This removes bumps/waves from the water surface
    // making it look like a flat mirror or lake.
    if (h < 0.5) {
        return vec3(0.0, 0.0, 1.0);
    }
    // ------------------------

    float offset = 1.0 / u_TexRes; 
    float h_right = getHeight(uv + vec2(offset, 0.0));
    float h_up    = getHeight(uv + vec2(0.0, offset));
    
    float dx = (h - h_right) * scale;
    float dy = (h - h_up)    * scale;
    
    return normalize(vec3(dx, dy, 1.0));
}

vec3 getLightVector(float lat_deg, float lon_deg, float declination, float gha) {
    float lat = radians(lat_deg);
    float lon = radians(lon_deg);
    float LHA = gha + lon; 
    float sin_lat = sin(lat); float cos_lat = cos(lat);
    float sin_dec = sin(declination); float cos_dec = cos(declination);
    float cos_lha = cos(LHA); float sin_lha = sin(LHA);
    float x = -cos_dec * sin_lha;
    float y = (sin_dec * cos_lat) - (cos_dec * sin_lat * cos_lha);
    float z = (sin_lat * sin_dec) + (cos_lat * cos_dec * cos_lha);
    return normalize(vec3(x, y, z));
}

float calculateShadow(vec2 uv, vec3 lightDir, float startHeight) {
    if (lightDir.z <= 0.0) return 0.0;
    int STEPS = 24;                 
    float stepSize = 1.0 / u_TexRes; 
    vec2 rayPos = uv;
    float rayHeight = startHeight;
    vec2 dir_xy = lightDir.xy * stepSize; 
    float slope_z = lightDir.z / length(lightDir.xy) * stepSize;
    if (lightDir.z > 0.9) return 1.0; 

    for(int i = 0; i < STEPS; i++) {
        rayPos -= dir_xy; 
        rayHeight += slope_z; 
        if(rayPos.x < 0.0 || rayPos.x > 1.0 || rayPos.y < 0.0 || rayPos.y > 1.0) break;
        if(getHeight(rayPos) > rayHeight) return 0.0;
    }
    return 1.0; 
}

void main() {
    // --- TERRAIN DATA ---
    vec4 t_data = texture(u_terrain_arr, vec3(v_uv, u_layer));
    vec4 a_data = texture(u_atmos_arr, vec3(v_uv, u_layer));
    
    float h = t_data.r;
    float t_temp = t_data.g;
    float t_hum = t_data.b;
    float w_x = a_data.r; 
    float w_y = a_data.g; 
    float a_hum = a_data.a; 

    // Base Color (Simple Biome Logic)
    vec3 color;
    if (h < 0.5) {
        // We keep the color gradient (Deep water is darker) because that looks good,
        // but the lighting normal is now flat.
        color = mix(vec3(0.01, 0.05, 0.2), vec3(0.0, 0.3, 0.6), h*2.0); 
    } else {
        float elev = (h - 0.5) * 2.0;
        if (t_temp < 0.35) color = vec3(0.95, 0.95, 1.0); // Snow
        else if (t_temp > 0.65) {
            if (t_hum < 0.3) color = vec3(0.85, 0.75, 0.5); // Desert
            else color = vec3(0.05, 0.25, 0.05); // Jungle
        } else {
            if (t_hum < 0.4) color = vec3(0.5, 0.6, 0.2); // Savannah
            else color = vec3(0.1, 0.5, 0.1); // Forest
        }
        color *= (0.8 + 0.2 * elev);
    }

    // Weather Overlay (Clouds)
    if (a_hum > 0.6) {
        float cloud_density = (a_hum - 0.6) * 2.5; 
        color = mix(color, vec3(0.9), cloud_density * 0.8);
    }
    
    // ---------------------------------------------------------
    // DYNAMIC LIGHTING
    // ---------------------------------------------------------
    
    vec3 normal = getNormal(v_uv, u_HeightScale); 
    
    vec3 sunVec  = getLightVector(v_LatLon.y, v_LatLon.x, u_SolarDeclination, u_GHA);
    vec3 moonVec = getLightVector(v_LatLon.y, v_LatLon.x, u_LunarDeclination, u_LunarGHA);

    vec3 sun_color_dynamic = getSunColor(sunVec.z);
    
    float sun_diffuse  = max(0.0, dot(normal, sunVec));
    float moon_diffuse = max(0.0, dot(normal, moonVec));
    
    float sun_shadow = 1.0;
    if(sun_diffuse > 0.0) sun_shadow = calculateShadow(v_uv, sunVec, h);
    
    float moon_shadow = 1.0;
    if(moon_diffuse > 0.0 && u_MoonPhase > 0.05) moon_shadow = calculateShadow(v_uv, moonVec, h);

    // Specular (Water Reflection)
    vec3 specular = vec3(0.0);
    if (h < 0.5) {
        vec3 viewDir = vec3(0.0, 0.0, 1.0);
        
        // Sun Glint
        if (sun_shadow > 0.0 && sunVec.z > -0.1) {
            vec3 reflectSun = reflect(-sunVec, normal);
            float spec = pow(max(dot(viewDir, reflectSun), 0.0), 64.0); // Sharper reflection (64.0)
            specular += sun_color_dynamic * spec * sun_shadow * 1.5;
        }
        
        // Moon Glint
        if (moon_shadow > 0.0 && moonVec.z > 0.0) {
            vec3 reflectMoon = reflect(-moonVec, normal);
            float spec = pow(max(dot(viewDir, reflectMoon), 0.0), 32.0);
            specular += vec3(0.6, 0.7, 1.0) * spec * moon_shadow * u_MoonPhase * 0.8;
        }
    }

    // Compose Light
    vec3 ambient = vec3(0.02, 0.02, 0.04);
    
    float sun_fade = smoothstep(-0.1, 0.1, sunVec.z); 
    vec3 sun_light = sun_color_dynamic * sun_diffuse * sun_shadow * sun_fade;
    
    float moon_fade = smoothstep(-0.05, 0.05, moonVec.z);
    vec3 moon_light_color = vec3(0.5, 0.6, 0.9);
    vec3 moon_light = moon_light_color * moon_diffuse * moon_shadow * u_MoonPhase * moon_fade * 0.3;

    vec3 total_light = ambient + sun_light + moon_light;
    
    f_color = vec4((color * total_light) + specular, 1.0);
}
#endif
