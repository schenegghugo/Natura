#!/bin/bash

PROJECT_NAME="py_df_sim"

echo "Creating project: $PROJECT_NAME..."

# 1. Create Directory Structure
mkdir -p $PROJECT_NAME/src/engine
mkdir -p $PROJECT_NAME/src/simulation
mkdir -p $PROJECT_NAME/src/utils
mkdir -p $PROJECT_NAME/assets/shaders

cd $PROJECT_NAME

# 2. Create Python Package markers
touch src/__init__.py
touch src/engine/__init__.py
touch src/simulation/__init__.py
touch src/utils/__init__.py

# 3. Create Configuration and Main Entry
cat <<EOT >> src/config.py
# Global Constants
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60

# World Generation
WORLD_SIZE = 256  # 256x256 Grid
SEED = 42
TILE_SIZE = 4     # How big a pixel/tile looks on screen
EOT

cat <<EOT >> src/main.py
import pygame
import sys
from engine.renderer import Renderer
from simulation.world import World
from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS

def main():
    pygame.init()
    pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.RESIZABLE)
    clock = pygame.time.Clock()

    # Initialize Core Systems
    world = World()
    renderer = Renderer(world)

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time in seconds

        # Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Simulation Update
        world.update(dt)

        # Render
        renderer.render()
        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
EOT

# 4. Create Engine Scripts
cat <<EOT >> src/engine/renderer.py
import moderngl
import numpy as np

class Renderer:
    def __init__(self, world_ref):
        self.ctx = moderngl.create_context()
        self.world = world_ref
        # TODO: Day 1 - Setup Quad VBO and Shader Program here
        pass

    def render(self):
        self.ctx.clear(0.1, 0.1, 0.1)
        # TODO: Day 1 - Render the world texture to a quad
        pass
EOT

touch src/engine/input.py

# 5. Create Simulation Scripts
cat <<EOT >> src/simulation/world.py
import numpy as np
from config import WORLD_SIZE

class World:
    def __init__(self):
        # Shape: (Width, Height, Channels)
        # Channels: 0:Elevation, 1:Moisture, 2:Temp, 3:Biomass
        self.map_data = np.zeros((WORLD_SIZE, WORLD_SIZE, 4), dtype=np.float32)
        
        # Agent Lists
        self.entities = [] 

    def update(self, dt):
        # TODO: Day 3 - Weather logic
        # TODO: Day 4 - Plant growth
        # TODO: Day 5 - Entity movement
        pass
EOT

cat <<EOT >> src/simulation/weather.py
# TODO: Day 3 - Implement Rain, Wind, Cycle logic
class WeatherSystem:
    pass
EOT

cat <<EOT >> src/simulation/entities.py
# TODO: Day 5 & 6 - Agent Classes (Herbivore, Carnivore)
class Entity:
    def __init__(self, x, y):
        self.x = x
        self.y = y
EOT

# 6. Create Utilities
cat <<EOT >> src/utils/noise.py
# TODO: Day 2 - Perlin/Simplex noise wrappers
pass
EOT

cat <<EOT >> src/utils/shader_loader.py
def load_shader(ctx, vertex_path, fragment_path):
    with open(vertex_path, 'r') as f:
        vertex_code = f.read()
    with open(fragment_path, 'r') as f:
        fragment_code = f.read()
    return ctx.program(vertex_shader=vertex_code, fragment_shader=fragment_code)
EOT

# 7. Create Basic Shaders (Day 1 Prep)
cat <<EOT >> assets/shaders/vertex.glsl
#version 330 core
in vec2 in_vert;
in vec2 in_text;
out vec2 v_text;
void main() {
    v_text = in_text;
    gl_Position = vec4(in_vert, 0.0, 1.0);
}
EOT

cat <<EOT >> assets/shaders/fragment.glsl
#version 330 core
in vec2 v_text;
out vec4 f_color;
// uniform sampler2D world_texture;
void main() {
    // Placeholder debug color (UV gradient)
    f_color = vec4(v_text.x, v_text.y, 0.0, 1.0);
}
EOT

# 8. Create Requirements
cat <<EOT >> requirements.txt
pygame
moderngl
numpy
noise
EOT

echo "------------------------------------------------"
echo "Project structure created at ./$PROJECT_NAME"
echo "------------------------------------------------"
echo "Next Steps:"
echo "1. cd $PROJECT_NAME"
echo "2. python3 -m venv venv"
echo "3. source venv/bin/activate"
echo "4. pip install -r requirements.txt"
echo "5. python src/main.py"
echo "------------------------------------------------"
