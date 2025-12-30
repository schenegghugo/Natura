# Natura (py_df_sim)

**Natura** is a high-performance, infinite procedural world simulation engine written in Python. It utilizes **ModernGL** for GPU acceleration, moving the heavy lifting of biome calculation and weather rendering from the CPU to the Fragment Shader.

The engine uses a **Quadtree-based Level of Detail (LOD)** system to render massive worlds with seamless zooming, from planetary views down to individual pixels.

## 🚀 Key Features

*   **Infinite Procedural Terrain:** Generates terrain on-the-fly using Perlin noise.
*   **GPU-Driven Biomes:** The CPU sends raw data; the GPU determines if a pixel is a Jungle, Desert, Ocean, or Snow based on height, temperature, and humidity.
*   **8-Layer Data Simulation:**
    *   **Terrain:** Height, Ground Temperature, Humidity, Biomass.
    *   **Atmosphere:** Wind Vector (X, Y), Air Temperature, Cloud Density.
*   **Dynamic Weather:** Real-time, animated rain, snow, and cloud cover simulated entirely in the shader.
*   **High Precision:** Uses `Float32` texture arrays for accurate physics simulation.
*   **Chunk Serialization:** Saves/Loads generated chunks to disk to persist world state.

---

## Architecture: The "Data Sandwich"

Unlike traditional engines that generate a color texture on the CPU, Natura generates **raw physics data**.

1.  **CPU (`generator.py`):** Generates an `(8, 33, 33)` NumPy array of raw floats for every chunk.
2.  **VRAM (`texture_manager.py`):** Data is uploaded to **Texture Arrays** using floating-point precision (`dtype='f4'`).
3.  **GPU (`chunk.glsl`):**
    *   **Vertex Shader:** Handles positioning and camera zoom/pan.
    *   **Fragment Shader:** Reads the 8 data layers, mixes them, calculates lighting/colors, and renders animated weather effects (Rain/Snow) based on the `Wind` vectors and `Time`.

---

## Project Structure

```text
py_df_sim/
├── assets/
│   └── shaders/
│       ├── chunk.glsl       # The core logic: Biomes & Weather rendering
│       ├── vertex.glsl      # UI/Debug shaders
│       └── fragment.glsl    # UI/Debug shaders
├── saves/                   # World data storage (JSON + Binary chunks)
├── src/
│   ├── main.py              # Entry point
│   ├── config.py            # Global constants (Screen size, Chunk size)
│   ├── engine/              # Graphics & IO System
│   │   ├── chunk_renderer.py  # Manages the VBOs and Shader Uniforms
│   │   ├── texture_manager.py # Handles VRAM allocation & Texture Arrays
│   │   ├── camera.py          # Coordinate transformation
│   │   └── input.py           # Mouse/Keyboard handling
│   ├── simulation/          # Game Logic & Data Generation
│   │   ├── generator.py       # Noise generation (The 8-layer data source)
│   │   ├── quadtree.py        # LOD management
│   │   ├── data_manager.py    # Caching and fetching chunk data
│   │   └── world.py           # High-level simulation coordinator
│   └── utils/               # Helper functions
│       └── noise.py           # Perlin noise wrappers
└── requirements.txt         # Python dependencies
```

## Installation

1.  **Create a Virtual Environment:**
    ```bash
    python -m venv venv
    source venv/bin/activate  # Linux/Mac
    # venv\Scripts\activate   # Windows
    ```

2.  **Install Dependencies:**
    ```bash
    pip install -r py_df_sim/requirements.txt
    ```
    *Core dependencies:* `moderngl`, `numpy`, `glfw`, `noise`.

## Usage

**Run the simulation:**
```bash
python py_df_sim/src/main.py
```

**Controls:**
*   **WASD / Arrow Keys:** Pan the camera.
*   **Scroll Wheel:** Zoom in/out.
*   **ESC:** Quit.

## ⚠️ Note on Save Files

Because the engine now uses an 8-layer float data format, **old save files are incompatible**.
If the engine crashes on load, delete the `saves/` folder:

```bash
rm -rf py_df_sim/saves/
```

## 📜 License

MIT
