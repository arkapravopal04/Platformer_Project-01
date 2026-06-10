import pygame

class Camera(pygame.sprite.Sprite):
    def __init__(self, player_reference, map_size, screen_size):
        super().__init__()

        self.player = player_reference
        self.map_rect = pygame.Rect(0, 0, map_size[0], map_size[1])
        self.screen_width, self.screen_height = screen_size
        self.camera_rect = pygame.Rect(0, 0, self.screen_width, self.screen_height)
        self.offset = pygame.math.Vector2(0, 0)

        self.trail_speed = 0.2 # between 0 and 1. 1 means no trail (snaps to player)

    def apply(self, target_rect):
        # player sprite adjustment
        return target_rect.move(self.offset.x, self.offset.y)

    def draw_debug_box(self, screen):
        # debug box drawing - should move
        pygame.draw.rect(screen, 'Blue', self.camera_rect, 2)


    def update(self):
        # Calculate target camera position (centered on player)
        target_x = -self.player.rect.centerx + self.screen_width // 2
        target_y = -self.player.rect.centery + self.screen_height // 2

        # Apply trailing effect (optional)
        if self.trail_speed < 1.0:
            self.offset.x += (target_x - self.offset.x) * self.trail_speed
            self.offset.y += (target_y - self.offset.y) * self.trail_speed
        else:
            self.offset.x = target_x
            self.offset.y = target_y

        # Clamp the camera to the map boundaries
        # This prevents the camera from showing areas outside your defined map
        self.offset.x = max(-(self.map_rect.width - self.screen_width), self.offset.x)
        self.offset.x = min(0, self.offset.x)


        self.offset.y = max(-(self.map_rect.height - self.screen_height), self.offset.y)
        self.offset.y = min(0, self.offset.y)

        # Update the camera_rect's position based on the offset
        # This rect represents the top-left corner of the *visible* part of the world
        self.camera_rect.topleft = self.offset

