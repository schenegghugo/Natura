import pygame
import moderngl
import sys
import config

# Engine Systems
from engine.camera import Camera
from engine.chunk_renderer import ChunkRenderer
from engine.line_renderer import LineRenderer
from engine.texture_manager import TextureManager
from engine.save_manager import SaveManager

# Simulation Systems
from simulation.quadtree import QuadtreeManager
from simulation.generator import TerrainGenerator
from simulation.data_manager import DataManager

# Step 2 & 3: Time and Orbit Systems
from simulation.chronos import Chronos 
from simulation.celestials import Celestials

def main():
    # 1. Pygame & OpenGL Setup
    pygame.init()
    pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    
    # Create ModernGL Context
    ctx = moderngl.create_context()
    ctx.enable(moderngl.BLEND) # Enable transparency
    
    # 2. Initialize Persistence Layer
    save_manager = SaveManager()
    
    # Check if a save exists
    saved_state = save_manager.load_global_state()
    
    # Default Defaults
    seed = 12345
    start_pos = (0, 0)
    start_zoom = 1.0
    
    if saved_state:
        print(">>> Save file found! Resuming world...")
        seed = saved_state['seed']
        start_pos = (saved_state['camera_x'], saved_state['camera_y'])
        start_zoom = saved_state['zoom']
    else:
        print(">>> No save found. Creating new world.")

    # 3. Instantiate Systems
    
    # Camera: Handles Viewport
    camera = Camera()
    camera.pos = list(start_pos) # Apply loaded position
    camera.zoom = start_zoom     # Apply loaded zoom
    
    # Quadtree: The "Brain" (Spatial partitioning)
    quadtree = QuadtreeManager()
    
    # Generator: The "Artist" (Math & Noise)
    generator = TerrainGenerator(seed=seed)
    
    # DataManager: The "Memory" (RAM + Disk Cache)
    data_manager = DataManager(generator, save_manager)
    
    # TextureManager: The "Gallery" (VRAM Management)
    texture_manager = TextureManager(ctx, pool_size=64)
    
    # Renderers: The "Painters"
    chunk_renderer = ChunkRenderer(ctx)
    line_renderer = LineRenderer(ctx)
    
    # --- SIMULATION CORE ---
    # Step 2: Initialize Chronos (The Clock)
    chronos = Chronos()
    
    # Step 3: Initialize Celestials (The Orbits)
    # This takes chronos as a dependency to calculate sun/moon position
    celestials = Celestials(chronos)
    
    # Loop Setup
    clock = pygame.time.Clock()
    running = True
    
    print("\n--- ENGINE STARTED ---")
    print("Controls: WASD or Drag to Pan | Scroll to Zoom")
    print("F5: Quick Save | F9: Reload World")
    print("----------------------\n")

    while running:
        # --- Time Management ---
        # clock.tick returns milliseconds passed since last frame.
        # We convert to seconds (dt) for the simulation.
        dt_ms = clock.tick(config.FPS) 
        dt = dt_ms / 1000.0

        # --- A. Input Handling ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            
            # --- SAVE / LOAD CONTROLS ---
            if event.type == pygame.KEYDOWN:
                # SAVE
                if event.key == pygame.K_F5:
                    print("\n>>> SAVING GAME...")
                    # 1. Save Camera & Seed
                    save_manager.save_global_state(generator.seed, camera)
                    # 2. Save all Modified/Loaded Chunks
                    data_manager.save_all_loaded_chunks()
                    # (Optional: Save chronos.time_of_day and chronos.day_of_year here later)
                    print(">>> SAVE COMPLETE.\n")
                
                # LOAD (Hot Reload)
                elif event.key == pygame.K_F9:
                    print("\n>>> RELOADING FROM DISK...")
                    saved_state = save_manager.load_global_state()
                    
                    if saved_state:
                        # 1. Restore Camera
                        camera.pos = [saved_state['camera_x'], saved_state['camera_y']]
                        camera.zoom = saved_state['zoom']
                        
                        # 2. Flush RAM (Data Manager)
                        data_manager.loaded_chunks.clear()
                        
                        # 3. Flush VRAM (Texture Manager)
                        texture_manager.node_to_texture_id.clear()
                        texture_manager.available_indices = list(range(texture_manager.pool_size))
                        
                        # (Optional: Reload chronos state here later)
                        print(">>> RELOAD COMPLETE.\n")
                    else:
                        print(">>> NO SAVE FOUND.\n")

            # Pass generic events to camera
            camera.handle_event(event)
        
        # --- B. Simulation Updates ---
        
        # 1. Update Time (Step 2)
        chronos.update(dt)

        # 2. Update Orbits (Step 3)
        # Calculates new Solar Declination and Hour Angle based on updated time
        celestials.update()

        # 3. Update Quadtree
        quadtree.update(camera.pos, camera.zoom)

        # Free up RAM for chunks we can't see anymore
        data_manager.prune(quadtree.visible_nodes)

        # 4. Update Textures
        texture_manager.update(quadtree.visible_nodes, data_manager, generator)
        
        # --- C. Rendering ---
        
        # 1. Clear Screen (Dark Grey)
        ctx.clear(0.1, 0.1, 0.1)
        
        # 2. Draw Terrain
        # We now pass 'celestials' so the shader gets the computed angles (Declination, GHA)
        chunk_renderer.render(
            quadtree.visible_nodes, 
            texture_manager, 
            camera.pos, 
            camera.zoom,
            celestials 
        )
        
        # 3. Draw Debug Grid
        line_renderer.render(
            quadtree.visible_nodes, 
            camera.pos, 
            camera.zoom
        )
        
        # 4. Refresh Display
        pygame.display.flip()
        
        # Window Title Status
        pygame.display.set_caption(
            f"FPS: {clock.get_fps():.1f} | "
            f"Zoom: {camera.zoom:.2f} | "
            f"Year: {chronos.year} Day: {chronos.day_of_year} Hour: {chronos.time_of_day:.1f}"
        )

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
