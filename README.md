## Installation & Setup

1. Prerequisites

    Python 3.10 or higher.
    A Graphics Card supporting OpenGL 3.3+.

2. Install Dependencies

    pip install pygame moderngl numpy noise

3. Run the Engine

    python src/main.py

## Architecture & Core Concepts

1. Dynamic Level of Detail (LOD) via Quadtree

The engine abandons the traditional fixed-grid approach in favor of a recursive Quadtree structure. This allows for an infinite coordinate system where detail is relative to the camera's perspective.

    Recursive Subdivision: As the camera zooms in, visible nodes split into smaller children, increasing vertex density only where needed.
    Screen-Space Error Metric: The system ensures that a chunk covering 100 pixels on screen has roughly the same vertex count whether it represents 1 meter or 10 kilometers of terrain.
    Result: Visual fidelity remains constant while rendering performance stays stable (O(1) complexity relative to world size).

2. The Three-Tier Data Pipeline

To manage an infinite world with finite resources, the DataManager treats terrain data as a fluid resource flowing through three states of existence. When the renderer requests a chunk, the engine follows this strict fallback chain:

    RAM (The Cache):
        Priority: Immediate access.
        Storage: Python Dictionary of ChunkData objects.
        Role: Holds the "Active Set"—chunks currently inside the viewport.
    DISK (The Persistence Layer):
        Priority: Fallback if RAM misses.
        Storage: Compressed NumPy binaries (.npy) indexed by coordinates.
        Role: Stores the "Passive Set"—chunks previously visited or modified but currently out of view.
    VOID (The Generator):
        Priority: Final fallback.
        Storage: None (Pure Mathematics).
        Role: Generates fresh terrain using deterministic Perlin Noise for coordinates never visited before.

3. Aggressive Memory Management

Infinite exploration requires aggressive garbage collection to prevent memory leaks and ensure smooth performance.

    Visibility Pruning:
    The engine runs a cleanup cycle every frame. It calculates the difference between the Loaded Set (RAM) and the Visible Set (Quadtree). Any chunk that leaves the camera's view is immediately evicted from RAM, ensuring memory usage stays flat regardless of session length.

    Smart Serialization (Dirty Flags):
    To avoid IO bottlenecks during saving, every chunk tracks its own state via an is_dirty flag.
        New/Modified Chunks: Marked True. Written to disk on Save.
        Cached Chunks: Marked False. Ignored during Save operations. This "Delta Saving" approach means pressing F5 is near-instant, as it only writes the specific bits of data that changed since the last save.

## Project Structure

py_df_sim/
├── saves/                  # Generated save files (auto-created)
│   └── default/
│       ├── world.json      # Global state (Seed, Camera X/Y, Zoom)
│       └── chunks/         # .npy heightmap binary files
├── src/
│   ├── main.py             # Entry point & Game Loop
│   ├── config.py           # Constants (Screen size, colors)
│   ├── engine/
│   │   ├── camera.py       # Infinite coordinate system & Physics
│   │   ├── chunk_renderer.py # OpenGL Rendering logic
│   │   ├── save_manager.py # Disk I/O (JSON & NPY handling)
│   │   └── texture_manager.py # VRAM (Texture) Management
│   ├── simulation/
│   │   ├── data_manager.py # RAM Management, Caching & Pruning Logic
│   │   ├── generator.py    # Math / Noise Generation
│   │   ├── quadtree.py     # LOD Calculation
│   │   └── chunk_data.py   # Data container + Dirty Flags
│   └── shaders/
│       ├── vertex.glsl     # Vertex Shader
│       └── fragment.glsl   # Fragment Shader
