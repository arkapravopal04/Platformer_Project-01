import pygame
from sys import exit


#classes



#player
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()


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


        # health
        self.default_health = 100
        self.current_health = self.default_health
        self.is_dead = False


        #important
        self.image = self.player_blinking[self.player_index]
        self.rect = self.image.get_rect(midbottom = (320,360))
        #location is also temporary



    def player_input(self):

        #walking
        keys = pygame.key.get_pressed()
        if keys[pygame.K_d]:
            self.rect.x += 3
            self.direction = 'right'
        if keys[pygame.K_a]:
            self.rect.x -= 3
            self.direction = 'left'

            #sprinting
        if keys[pygame.K_LSHIFT] and keys[pygame.K_d]:
            self.rect.x += 4
            self.direction = 'right'
            self.is_walk = False
        if keys[pygame.K_LSHIFT] and keys[pygame.K_a]:
            self.rect.x -= 4
            self.direction = 'left'
            self.is_walk = False


            #jumping
        if keys[pygame.K_SPACE] and self.is_on_ground:
            self.vertical_momentum = self.jump_initial_velocity
            self.is_on_ground = False
            self.is_jump = True
        if not keys[pygame.K_SPACE] and self.vertical_momentum < self.min_jump_height_speed and not self.is_on_ground:
            self.vertical_momentum = self.min_jump_height_speed

    def apply_gravity(self):
        self.vertical_momentum += self.gravity_strength
        self.rect.y += self.vertical_momentum

        # Check for ground collision
        if self.rect.bottom >= self.ground_y:
            self.rect.bottom = self.ground_y
            if not self.is_on_ground:
                self.is_on_ground = True
                self.is_jump = False
                self.vertical_momentum = 0


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
            self.is_walk = True

        if self.is_jump:
            animation_list = self.player_jumping
            animation_speed = 0.1

        self.player_index += animation_speed

        if self.player_index >= len(animation_list):
            self.player_index = 0
        self.image = animation_list[int(self.player_index)]


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

    def draw_health(self,display_surf):
        pygame.draw.rect(display_surf, (0,0,0), (9, 9, 102, 7),2)
        pygame.draw.rect(display_surf,(32, 156, 5),(10,10,self.current_health,5))
        pygame.draw.rect(display_surf, (0,255,0), (10, 10, self.current_health, 2))


    def player_locate(self):
         #if u want the screen to wrap around
          if self.rect.left >= 670:
              self.rect.left = -30
          if self.rect.left < -30:
              self.rect.left = 660

    def debug(self, screen):

        pygame.draw.rect(screen, 'Green', self.rect, 2)


    def update(self):
        self.player_status()
        self.animation_state()
        self.player_input()
        self.apply_gravity()
        self.invincibility_frames()#update this
        #temporary to not lose the player
        # self.player_locate()



