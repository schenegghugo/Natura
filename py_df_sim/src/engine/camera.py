import pygame

class Camera:
    def __init__(self):
        # Renamed 'uv_pos' to 'pos' so main.py doesn't crash
        self.pos = [0.0, 0.0] 
        self.zoom = 1.0
        self.is_dragging = False
        
        # Multiplier to adapt the 0.0-1.0 logic to the Infinite World coordinate system
        self.move_speed = 1.0 

    def handle_event(self, event):
        if event.type == pygame.MOUSEWHEEL:
            zoom_factor = 1.1
            if event.y > 0: self.zoom *= zoom_factor
            elif event.y < 0: self.zoom /= zoom_factor
            
            # Note: I expanded the lower limit to 0.1 so you can 
            # actually zoom out enough to see new chunks loading.
            self.zoom = max(0.1, min(100.0, self.zoom))

        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                self.is_dragging = True
                pygame.mouse.get_rel() 

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False

        elif event.type == pygame.MOUSEMOTION:
            if self.is_dragging:
                # We need the surface size for your aspect ratio correction
                w, h = pygame.display.get_surface().get_size()
                dx, dy = event.rel
                
                # Aspect Ratio Correction (Your logic):
                uv_dx = (dx / h) / self.zoom
                uv_dy = (dy / h) / self.zoom
                
                # Apply with speed multiplier so we move more than 1 pixel
                self.pos[0] -= uv_dx * self.move_speed
                
                # Y Axis: INVERTED (Your logic)
                self.pos[1] += uv_dy * self.move_speed
