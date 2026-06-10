import player_classes
import pygame


'''this is the enemy class....later on add ai and movement mechanics...
for now it is just a place to test enemy movements,attacks,etc...'''



class Enemy(pygame.sprite.Sprite):
    def __init__(self,player_reference):
        super().__init__()

        basic_enemy = pygame.image.load('random_images_not_sorted/pixil-frame-0.png').convert_alpha()

        self.image = pygame.transform.scale_by(basic_enemy, 1.5)
        self.rect = self.image.get_rect(midbottom = (400,360))
        self.player = player_reference


    def movement(self):
        self.rect.x = self.player.rect.x+ 40
        self.rect.y = self.player.rect.y


    def update(self):
        # self.movement() #tempory
        pass




#enemy ai...in the works
'''enemy is a arrow for now
drop down 
follow the player
attack the player
be animated 
have a health bar on display
'''