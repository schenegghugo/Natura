import sys
import os
import pygame
import config
import math
import moderngl

sys.path.append(os.path.join(os.path.dirname(__file__), '.'))

from engine.chunk_renderer import ChunkRenderer 
from simulation.world import World
from simulation.quadtree import QuadtreeManager 
from engine.line_renderer import LineRenderer 
from simulation.generator import TerrainGenerator
from engine.texture_manager import TextureManager

class Camera:
    def __init__(self):
        self.uv_pos = [0.5, 0.5] 
        self.zoom = 1.0
        self.is_dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            zoom_factor = 1.1
            if event.y > 0: self.zoom *= zoom_factor
            elif event.y < 0: self.zoom /= zoom_factor
            self.zoom = max(1.0, min(100.0, self.zoom))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.is_dragging = True
                pygame.mouse.get_rel() 

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                w, h = pygame.display.get_surface().get_size()
                dx, dy = event.rel
                
                # Aspect Ratio Correction:
                # We divide by height (h) to keep movement proportional
                uv_dx = (dx / h) / self.zoom
                uv_dy = (dy / h) / self.zoom
                
                # X Axis: Standard
                self.uv_pos[0] -= uv_dx 
                
                # Y Axis: INVERTED
                # Screen Y is Down-Positive. World Y is Up-Positive.
                # Dragging Mouse Down (+dy) should move Camera Up (+y) 
                # to make the world feel like it's being dragged Down.
                self.uv_pos[1] += uv_dy 

def main():
    # 1. Pygame Setup
    pygame.init()
    pygame.display.set_mode((config.SCREEN_WIDTH, config.SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    
    # 2. ModernGL Context
    ctx = moderngl.create_context()
    ctx.enable(moderngl.BLEND)
    
    # 3. Instantiate Systems
    camera = Camera()
    
    # The Brain: Decides what chunks exist
    quadtree = QuadtreeManager()
    
    # The Artist: Creates the noise data
    generator = TerrainGenerator(seed=12345)
    
    # The Gallery: Manages VRAM
    texture_manager = TextureManager(ctx, pool_size=64)
    
    # The Painters: Draw to the screen
    chunk_renderer = ChunkRenderer(ctx)
    line_renderer = LineRenderer(ctx)
    
    clock = pygame.time.Clock()
    running = True
    
    print("Engine Started. Pan: Mouse Drag. Zoom: Scroll Wheel.")

    while running:
        # --- A. Input Handling ---
        events = pygame.event.get()
        for event in events:
            if event.type == pygame.QUIT:
                running = False
            # Pass events to camera
            camera.handle_event(event)
        
        # --- B. Simulation / Logic Updates ---
        
        # 1. Update Camera Physics (Momentum, Zoom smoothing)
        # (Assuming you have a simple .update() in Camera, if not, it's fine)
        
        # 2. Update Quadtree (The "Active Set")
        # Calculates which grid squares are currently visible based on camera
        quadtree.update(camera.uv_pos, camera.zoom)
        
        # 3. Update Texture Manager (The "Streaming")
        # - Checks which nodes from the Quadtree are new.
        # - Generates noise for them using the Generator.
        # - Uploads them to GPU.
        # - Recycles old textures.
        texture_manager.update(quadtree.visible_nodes, generator)
        
        # --- C. Rendering ---
        
        # 1. Clear Screen (Dark Grey background)
        ctx.clear(0.1, 0.1, 0.1)
        
        # 2. Render the Terrain Chunks
        chunk_renderer.render(
            quadtree.visible_nodes, 
            texture_manager, 
            camera.uv_pos, 
            camera.zoom
        )
        
        # 3. Render Debug Lines (Optional - Toggle this to see the grid!)
        line_renderer.render(
            quadtree.visible_nodes, 
            camera.uv_pos, 
            camera.zoom
        )
        
        # 4. Swap Buffers
        pygame.display.flip()
        clock.tick(60)
        
        # Optional: Title bar debug info
        pygame.display.set_caption(f"FPS: {clock.get_fps():.1f} | Chunks: {len(quadtree.visible_nodes)} | Zoom: {camera.zoom:.2f}")

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
