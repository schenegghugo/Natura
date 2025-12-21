import os

def load_shader(filename):
    """
    Reads a shader file from assets/shaders/ regardless of run location.
    """
    # 1. Get the directory containing this script (src/utils/)
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Go up two levels to project root, then into assets/shaders
    #    (src/utils -> src -> root -> assets -> shaders)
    shader_dir = os.path.join(current_dir, '..', '..', 'assets', 'shaders')
    
    # 3. Construct full path
    filepath = os.path.join(shader_dir, filename)
    
    # 4. Read and return string
    try:
        with open(filepath, 'r') as f:
            return f.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"Shader not found at: {filepath}")
