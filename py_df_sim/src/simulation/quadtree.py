import math
import config

class QuadtreeNode:
    def __init__(self, x, y, level):
        self.x = x
        self.y = y
        self.level = level
        
    @property
    def size(self):
        return 1.0 / (2 ** self.level)

    @property
    def uv_pos(self):
        # Returns the Top-Left UV coordinate (in our Y-Up system, this is actually Bottom-Left relative to the grid index)
        # But for math consistency, let's keep it simple:
        s = self.size
        return (self.x * s, self.y * s)

class QuadtreeManager:
    def __init__(self):
        self.visible_nodes = []
        self.max_level = 6

    def update(self, cam_pos, cam_zoom):
        self.visible_nodes = []
        
        # --- 1. ASPECT RATIO CORRECTION ---
        aspect = config.SCREEN_HEIGHT / config.SCREEN_WIDTH
        
        # Calculate View Height (World Units)
        # 1.0 / zoom is the baseline. 
        # We multiply by 1.2 to have a small safety margin (preload).
        view_h = (1.0 / cam_zoom) * 1.2
        
        # Calculate View Width (World Units)
        # Since aspect < 1.0 (e.g., 0.56), dividing by it makes width LARGER.
        # This matches the wide screen.
        view_w = view_h / aspect 
        
        # Define World Boundaries
        # We use min/max to be safe regardless of coordinate system direction
        x_min = cam_pos[0] - view_w / 2
        x_max = cam_pos[0] + view_w / 2
        y_min = cam_pos[1] - view_h / 2
        y_max = cam_pos[1] + view_h / 2

        # 2. Identify Grid Indices
        # We use floor for min and ceil for max to ensure we catch partial tiles
        start_x = math.floor(x_min)
        end_x   = math.ceil(x_max)
        start_y = math.floor(y_min)
        end_y   = math.ceil(y_max)

        # 3. Loop through visible roots
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):                
                root = QuadtreeNode(x, y, 0)
                
                # Pass the calculated boundaries for culling
                view_rect = {'l': x_min, 'r': x_max, 'b': y_min, 't': y_max}
                self._process_node(root, cam_zoom, view_rect)

    def _process_node(self, node, zoom, view_rect):
        u, v = node.uv_pos
        s = node.size
        
        # Culling (Intersection Test)
        # If the square is completely outside the view_rect
        if (u > view_rect['r'] or u + s < view_rect['l'] or
            v > view_rect['t'] or v + s < view_rect['b']):
            return

        # Heuristic: Split if covers > 75% of screen
        should_split = (s * zoom) > 0.75

        if should_split and node.level < self.max_level:
            cx, cy = node.x * 2, node.y * 2
            lvl = node.level + 1
            
            self._process_node(QuadtreeNode(cx, cy, lvl), zoom, view_rect)
            self._process_node(QuadtreeNode(cx + 1, cy, lvl), zoom, view_rect)
            self._process_node(QuadtreeNode(cx, cy + 1, lvl), zoom, view_rect)
            self._process_node(QuadtreeNode(cx + 1, cy + 1, lvl), zoom, view_rect)
        else:
            self.visible_nodes.append(node)
