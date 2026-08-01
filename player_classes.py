import pygame
from sys import exit


#classes



#player
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        # world bounds for wall collision - set from outside via set_world_bounds()
        # once the map size is known; defaults to "no bound" until then.
        self.world_width = None
        # obstacle-course platforms - set from outside via set_platforms();
        # None means "no platforms exist yet, just the flat ground_y floor"
        self.platforms = None
        # whichever platform the player is currently standing on, if any
        # (None when on the ground floor or airborne). Used to carry the
        # player along with a MovingPlatform each frame - see
        # apply_gravity() and player_input()'s movement-order handling.
        self.standing_platform = None
        # blocking walls - vertical obstacles that stop horizontal
        # movement (walking, sprinting, dashing) but don't affect
        # vertical movement at all; used to physically prevent a big
        # sprint/dash jump from skipping past an intermediate platform.
        # Set from outside via set_walls(); None/empty means no walls.
        self.walls = []


        self.player_stand = pygame.image.load('player_animations/player_idle/1_player_idle.png').convert_alpha()


        player_blink_1 = pygame.image.load('player_animations/player_idle/player_idle_1.png').convert_alpha()
        player_blink_2 = pygame.image.load('player_animations/player_idle/player_idle_2.png').convert_alpha()
        player_blink_3 = pygame.image.load('player_animations/player_idle/player_idle_3.png').convert_alpha()
        self.player_blinking = [self.player_stand,self.player_stand,self.player_stand,player_blink_1,player_blink_2,player_blink_3]


        player_walk_1 = pygame.image.load('player_animations/player_walk/player_walk_1.png').convert_alpha()
        player_walk_2 = pygame.image.load('player_animations/player_walk/player_walk_2.png').convert_alpha()
        player_walk_3 = pygame.image.load('player_animations/player_walk/player_walk_3.png').convert_alpha()
        player_walk_4 = pygame.image.load('player_animations/player_walk/player_walk_4.png').convert_alpha()
        self.player_walking = [player_walk_1,player_walk_2,player_walk_3,player_walk_4]




        player_sprint_1 = pygame.image.load('player_animations/player_sprint/player_sprint_1.png').convert_alpha()
        player_sprint_2 = pygame.image.load('player_animations/player_sprint/player_sprint_2.png').convert_alpha()
        player_sprint_3 = pygame.image.load('player_animations/player_sprint/player_sprint_3.png').convert_alpha()
        player_sprint_4 = pygame.image.load('player_animations/player_sprint/player_sprint_4.png').convert_alpha()
        player_sprint_5 = pygame.image.load('player_animations/player_sprint/player_sprint_5.png').convert_alpha()
        player_sprint_6 = pygame.image.load('player_animations/player_sprint/player_sprint_6.png').convert_alpha()
        player_sprint_7 = pygame.image.load('player_animations/player_sprint/player_sprint_7.png').convert_alpha()
        player_sprint_8 = pygame.image.load('player_animations/player_sprint/player_sprint_8.png').convert_alpha()
        self.player_sprinting = [player_sprint_1,player_sprint_2,player_sprint_3,player_sprint_4,player_sprint_5,player_sprint_6,player_sprint_7,player_sprint_8]


        player_jump_1 = pygame.image.load('player_animations/player_jump/player_jump_1.png').convert_alpha()
        player_jump_2 = pygame.image.load('player_animations/player_jump/player_jump_2.png').convert_alpha()
        player_jump_3 = pygame.image.load('player_animations/player_jump/player_jump_3.png').convert_alpha()
        player_jump_4 = pygame.image.load('player_animations/player_jump/player_jump_4.png').convert_alpha()
        player_jump_5 = pygame.image.load('player_animations/player_jump/player_jump_5.png').convert_alpha()
        player_jump_6 = pygame.image.load('player_animations/player_jump/player_jump_6.png').convert_alpha()
        player_jump_7 = pygame.image.load('player_animations/player_jump/player_jump_7.png').convert_alpha()
        self.player_jumping = [player_jump_1,player_jump_2,player_jump_3,player_jump_4,player_jump_5,player_jump_6,player_jump_7]






        #variables-type
        self.is_on_ground = True
        self.is_jump = False
        self.is_walk = True
        self.direction = 'right'
        self.status = 'idle'


        #variables-assigning
        self.player_index = 0
        self.vertical_momentum = 0
        self.gravity_strength = 0.5
        self.jump_initial_velocity = -10
        self.is_on_ground = True
        self.ground_y = 360
        self.min_jump_height_speed = -3
        self.is_invincible = False
        self.invincibility_duration = 1000
        self.invincibility_timer= 0#check this

        # dash
        self.is_dashing = False
        self.dash_direction = 0        # -1 left, +1 right - locked in when the dash starts
        self.dash_speed = 16
        self.dash_duration_frames = 8
        self.dash_frames_left = 0
        self.dash_cooldown_ms = 800
        self.last_dash_time = -9999    # far enough in the past that a dash is available immediately


        # health
        self.default_health = 100
        self.current_health = self.default_health
        self.is_dead = False


        #important
        self.spawn_pos = (320, 360)
        self.image = self.player_blinking[self.player_index]
        self.rect = self.image.get_rect(midbottom = self.spawn_pos)
        #location is also temporary



    def set_world_bounds(self, world_width):
        self.world_width = world_width

    def set_platforms(self, platforms):
        self.platforms = platforms

    def set_ground_level(self, ground_y):
        """Reposition the ground line - and the player's spawn point along
        with it - to match the real background image's height. ground_y
        starts as a hardcoded placeholder (360) since the actual image size
        isn't known until main.py loads it; call this once, right after
        loading the background, before the game loop starts. Without this,
        the ground stays wherever the placeholder put it regardless of how
        tall the real image actually is - on a much taller background,
        that leaves the player (and anything positioned relative to
        ground_y, like obstacle-course platforms) sitting near the very
        top of the image instead of near the bottom.
        """
        self.ground_y = ground_y
        self.spawn_pos = (self.spawn_pos[0], ground_y)
        self.rect = self.image.get_rect(midbottom=self.spawn_pos)

    def apply_platform_ride(self):
        """Shift the player horizontally by however much their current
        standing_platform moved this frame, so standing on a
        MovingPlatform actually carries the player along with it instead
        of leaving them hovering in place while the platform slides out
        from under them. No-op when standing_platform is None (ground
        floor or airborne) or when it's a static Platform (delta_x is
        always 0 there). Must be called once per frame, after the
        platform group's own update() has computed this frame's delta
        and before the player's own input/gravity pass runs.
        """
        if self.is_dead or self.standing_platform is None:
            return
        self.rect.x += self.standing_platform.delta_x
        self._clamp_to_walls(moving_right=(self.standing_platform.delta_x > 0))
        # Re-clamp to world bounds in case riding the platform pushed the
        # player past a wall - same bounds check player_input() already
        # applies to walking, kept consistent here.
        if self.world_width is not None:
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > self.world_width:
                self.rect.right = self.world_width

    def set_walls(self, walls):
        self.walls = walls

    def _clamp_to_walls(self, moving_right):
        """Stop horizontal movement at any Wall the player is currently
        overlapping vertically. Only blocks passage in the direction of
        travel (moving_right) - a wall the player is already partway
        through (e.g. spawned/placed slightly overlapping) won't trap
        them, it just stops further movement deeper into it. Called
        after every x-movement (walk, sprint, dash, and the platform
        ride-along) so none of those movement paths can tunnel through a
        wall meant to block a skip.
        """
        if not self.walls:
            return
        for wall in self.walls:
            vertically_overlapping = (
                self.rect.bottom > wall.rect.top and self.rect.top < wall.rect.bottom
            )
            if not vertically_overlapping:
                continue
            if moving_right and self.rect.right > wall.rect.left and self.rect.left < wall.rect.left:
                self.rect.right = wall.rect.left
            elif not moving_right and self.rect.left < wall.rect.right and self.rect.right > wall.rect.right:
                self.rect.left = wall.rect.right

    def player_input(self):
        if self.is_dead:
            return

        #walking
        keys = pygame.key.get_pressed()
        self.is_walk = True  # default each frame; sprint branch below overrides it

        sprinting = keys[pygame.K_LSHIFT]
        speed = 6 if sprinting else 3

        if not self.is_dashing:
            if keys[pygame.K_d]:
                self.rect.x += speed
                self.direction = 'right'
                if sprinting:
                    self.is_walk = False
                self._clamp_to_walls(moving_right=True)
            if keys[pygame.K_a]:
                self.rect.x -= speed
                self.direction = 'left'
                if sprinting:
                    self.is_walk = False
                self._clamp_to_walls(moving_right=False)

            # Wall collision: keep the player inside the map instead of letting
            # them walk off the left/right edges (this was the actual cause of
            # the "game hangs at the wall" symptom - the camera correctly stops
            # scrolling at the map edge, but the player kept walking past it,
            # off-screen, looking like a freeze).
            if self.world_width is not None:
                if self.rect.left < 0:
                    self.rect.left = 0
                if self.rect.right > self.world_width:
                    self.rect.right = self.world_width


            #jumping
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vertical_momentum = self.jump_initial_velocity
            self.is_on_ground = False
            self.is_jump = True
            # jumping cancels a dash in progress immediately, so gravity
            # resumes and the jump applies this same frame rather than
            # waiting out whatever's left of the dash's fixed duration
            self.is_dashing = False
            self.dash_frames_left = 0
        if not keys[pygame.K_SPACE] and self.vertical_momentum < self.min_jump_height_speed and not self.is_on_ground:
            self.vertical_momentum = self.min_jump_height_speed

    def apply_gravity(self):
        if self.is_dead:
            return
        if self.is_dashing:
            # Suspend gravity for the dash's duration: this is what makes
            # dashing in mid-air a clean horizontal burst instead of a
            # curve that gravity keeps fighting. Vertical state resumes
            # exactly where it left off once the dash ends.
            return

        previous_bottom = self.rect.bottom
        self.vertical_momentum += self.gravity_strength
        self.rect.y += self.vertical_momentum

        landed = False

        if self.platforms is not None and self.vertical_momentum >= 0:
            # Only consider landing while falling (or exactly at the apex,
            # momentum==0) - never while still rising, so jumping up through
            # a platform from below passes through cleanly instead of
            # snagging on its underside.
            candidates = []
            for plat in self.platforms:
                horizontally_overlapping = (
                    self.rect.right > plat.rect.left and self.rect.left < plat.rect.right
                )
                if not horizontally_overlapping:
                    continue
                # Swept check using last frame's bottom: did we cross this
                # platform's top surface during THIS frame's movement? Using
                # previous_bottom (not just the current position) means a
                # fast fall can't tunnel straight through a thin platform in
                # one big step.
                if previous_bottom <= plat.rect.top and self.rect.bottom >= plat.rect.top:
                    candidates.append(plat)
            if candidates:
                # land on the highest (smallest top) qualifying platform -
                # the first surface you'd actually hit falling from above
                landing_plat = min(candidates, key=lambda p: p.rect.top)
                self.rect.bottom = landing_plat.rect.top
                landed = True
                self.standing_platform = landing_plat

        if not landed and self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            landed = True
            # ground floor isn't a Platform instance, so standing on it
            # means "not riding anything"
            self.standing_platform = None

        if landed:
            # Reset unconditionally while grounded, not just on the
            # airborne->grounded transition - previously this only fired
            # once on landing, so vertical_momentum quietly kept
            # accumulating every frame the player stood still afterward
            # (harmless on its own since the ground clamp above always
            # corrected the position anyway, but it meant gravity would
            # "resume" a dash from a large stale value instead of a clean
            # one if the player dashed after standing still for a while).
            self.is_on_ground = True
            self.is_jump = False
            self.vertical_momentum = 0
        else:
            # Nothing supports the player this frame - matters now that
            # platforms have edges: walking off one with no jump involved
            # needs to correctly start a fall, not leave is_on_ground stuck
            # True from whenever they last landed.
            self.is_on_ground = False
            self.standing_platform = None


    def player_status(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d] or keys[pygame.K_a]:
            self.status = 'walking'
        else:
            self.status = 'idle'


    def animation_state(self):
        if self.is_walk:
            if self.status == 'walking':
                animation_list = self.player_walking
                animation_speed = 0.11
            else:
                animation_list = self.player_blinking
                animation_speed = 0.05

        else:
            animation_list = self.player_sprinting
            animation_speed = 0.2

        if self.is_jump or not self.is_on_ground:
            # not self.is_on_ground covers falling off a platform edge
            # without having jumped - now possible with real platforms,
            # and should still read visually as airborne, not mid-walk-cycle
            animation_list = self.player_jumping
            animation_speed = 0.1

        if self.is_dead:
            # freeze on the current frame instead of looping forever
            animation_list = [self.image]
            animation_speed = 0

        self.player_index += animation_speed

        if self.player_index >= len(animation_list):
            self.player_index = 0

        # Re-anchor on midbottom every frame: different animation frames can
        # have different surface sizes/padding, so keep the rect's bottom
        # pinned to where the player actually stands instead of letting it
        # drift from whatever size the rect happened to be last frame.
        anchor = self.rect.midbottom
        self.image = animation_list[int(self.player_index)]
        self.rect = self.image.get_rect(midbottom=anchor)


        if self.direction == 'left':
            self.image = pygame.transform.flip(self.image, True, False)


        if self.is_invincible:
            if pygame.time.get_ticks() // 100%2 == 0:
                alpha = 128
            else:
                alpha = 255
            self.image.set_alpha(alpha)
        else:
            self.image.set_alpha(255)

    def invincibility_frames(self):
        if self.is_invincible:
            current_time = pygame.time.get_ticks()
            if current_time - self.invincibility_timer >= self.invincibility_duration:
                self.is_invincible = False
                self.invincibility_timer = 0

#is payer gets hit - basicaly the health system
    def get_hit(self,amount):
        if not self.is_invincible:
            print("collision detected")
            self.is_invincible = True
            self.invincibility_timer = pygame.time.get_ticks()

            if self.is_dead:
                return
            # add if game active statements
            self.current_health -= amount
            if self.current_health <= 0:
                self.current_health = 0
                self.is_dead = True
                print("Player defeated!")
                return  # This could trigger a 'game over' state
            else:
                print(f"Player took 10 damage. Current health: {self.current_health}/{self.default_health}")
                return

    def start_dash(self):
        """Trigger a momentary dash in the direction the player is currently
        facing. No-ops if already dashing, dead, or still on cooldown."""
        if self.is_dead or self.is_dashing:
            return
        now = pygame.time.get_ticks()
        if now - self.last_dash_time < self.dash_cooldown_ms:
            return  # still on cooldown
        self.is_dashing = True
        self.dash_frames_left = self.dash_duration_frames
        self.dash_direction = 1 if self.direction == 'right' else -1
        self.last_dash_time = now

    def apply_dash(self):
        if not self.is_dashing:
            return
        if self.is_dead:
            self.is_dashing = False
            return

        self.rect.x += self.dash_speed * self.dash_direction
        self._clamp_to_walls(moving_right=(self.dash_direction > 0))

        # same wall clamp as normal movement - dashing into a wall just
        # stops you at the wall rather than punching through it
        if self.world_width is not None:
            if self.rect.left < 0:
                self.rect.left = 0
            if self.rect.right > self.world_width:
                self.rect.right = self.world_width

        self.dash_frames_left -= 1
        if self.dash_frames_left <= 0:
            self.is_dashing = False

    def draw_dash_indicator(self, display_surf):
        bar_width = 60
        now = pygame.time.get_ticks()
        fraction = min(1.0, (now - self.last_dash_time) / self.dash_cooldown_ms)
        fill_width = int(bar_width * fraction)
        ready_color = (60, 200, 220)
        charging_color = (90, 90, 100)
        color = ready_color if fraction >= 1.0 else charging_color

        pygame.draw.rect(display_surf, (0, 0, 0), (9, 19, bar_width + 2, 7), 2)
        pygame.draw.rect(display_surf, color, (10, 20, fill_width, 5))

    def draw_health(self,display_surf):
        pygame.draw.rect(display_surf, (0,0,0), (9, 9, 102, 7),2)
        pygame.draw.rect(display_surf,(32, 156, 5),(10,10,self.current_health,5))
        pygame.draw.rect(display_surf, (0,255,0), (10, 10, self.current_health, 2))

    def restart(self):
        """Reset the player back to a fresh, alive state at the spawn point.
        Called after is_dead, e.g. when the player presses the restart key."""
        self.current_health = self.default_health
        self.is_dead = False
        self.is_invincible = False
        self.invincibility_timer = 0

        self.vertical_momentum = 0
        self.is_on_ground = True
        self.is_jump = False
        self.is_walk = True
        self.direction = 'right'
        self.status = 'idle'
        self.player_index = 0

        self.is_dashing = False
        self.dash_frames_left = 0
        self.last_dash_time = -9999  # dash immediately available after respawn

        self.image = self.player_blinking[0]
        self.image.set_alpha(255)
        self.rect = self.image.get_rect(midbottom=self.spawn_pos)


    def player_locate(self):
         #if u want the screen to wrap around
          if self.rect.left >= 670:
              self.rect.left = -30
          if self.rect.left < -30:
              self.rect.left = 660

    def debug(self, screen, camera=None):
        rect_to_draw = camera.apply(self.rect) if camera else self.rect
        pygame.draw.rect(screen, 'Green', rect_to_draw, 2)


    def update(self):
        self.player_status()
        self.player_input()
        # gravity must be checked/applied BEFORE apply_dash() decrements the
        # dash timer - otherwise, on the dash's last frame, apply_dash()
        # would already flip is_dashing to False before apply_gravity() runs,
        # letting one frame of gravity sneak in right at the tail end of an
        # otherwise gravity-free dash.
        self.apply_gravity()
        self.apply_dash()
        # animation runs last so it re-anchors to this frame's *final* rect
        # position (post-gravity/post-movement), not last frame's stale one
        self.animation_state()
        self.invincibility_frames()#update this
        #temporary to not lose the player
        # self.player_locate()