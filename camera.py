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

    def _clamp_axis(self, value, map_length, screen_length):
        """Clamp an offset on one axis, handling maps smaller than the screen."""
        min_offset = -(map_length - screen_length)
        max_offset = 0
        if min_offset > max_offset:
            return (screen_length - map_length) / 2
        return max(min_offset, min(max_offset, value))

    def _target_offset(self):
        # Follow the player horizontally...
        target_x = -self.player.rect.centerx + self.screen_width // 2

        target_y = -self.player.rect.bottom + self.screen_height
        return target_x, target_y

    def snap_to_player(self):
        """Jump the camera straight to the player's position, bypassing the
        trail effect. Use this right after spawn/respawn so the camera
        doesn't visibly glide in from wherever it was last sitting."""
        target_x, target_y = self._target_offset()
        self.offset.x = target_x
        self.offset.y = target_y
        self.offset.x = self._clamp_axis(self.offset.x, self.map_rect.width, self.screen_width)
        self.offset.y = self._clamp_axis(self.offset.y, self.map_rect.height, self.screen_height)
        self.camera_rect.topleft = self.offset

    def update(self):
        target_x, target_y = self._target_offset()

        # Apply trailing effect on both axes - same lag, same speed
        if self.trail_speed < 1.0:
            self.offset.x += (target_x - self.offset.x) * self.trail_speed
            self.offset.y += (target_y - self.offset.y) * self.trail_speed
        else:
            self.offset.x = target_x
            self.offset.y = target_y

        self.offset.x = self._clamp_axis(self.offset.x, self.map_rect.width, self.screen_width)
        self.offset.y = self._clamp_axis(self.offset.y, self.map_rect.height, self.screen_height)

        # Update the camera_rect's position based on the offset
        # This rect represents the top-left corner of the *visible* part of the world
        self.camera_rect.topleft = self.offset