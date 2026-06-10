import pygame
from player_classes import Player
from camera import Camera
from test_enemy import Enemy


'''
this is the main game loop
1)for  now a temporary image is set to use the camera
2)...
'''


#general setup
pygame.init()
size = (640,360)
screen = pygame.display.set_mode(size)
pygame.display.set_caption("rustbound")
clock = pygame.time.Clock()





#groups


# player
player_group = pygame.sprite.GroupSingle()
player = Player()
player_group.add(player)


# enemy
enemy_group = pygame.sprite.Group()
enemy = Enemy(player_reference=player)
enemy_group.add(enemy)

#surfaces and texts
# background_image = pygame.image.load('random_images_not_sorted/big_pic.jpg').convert_alpha()
background_image = pygame.image.load('random_images_not_sorted/big_pic_2.jpg').convert_alpha()

#camera

camera = Camera(player_reference=player,map_size=background_image.get_size(),screen_size=size)



#random sprites


#event loop
while True:
    for event in pygame.event.get():
        if event.type == pygame.quit:
            pygame.quit()
            exit()
    screen.fill('#4c76a5')


    # background stuff
    # screen.blit(background_image,(0,0))
    screen.blit(background_image, camera.apply(background_image.get_rect(topleft=(0, 0))))


    # unfreesze these later
    enemy_group.draw(screen)
    enemy_group.update()

    # player_group.draw(screen)
    player_group.update()

    # camera_group.draw(screen)
    camera.update()
    screen.blit(player.image, camera.apply(player.rect))



    # debug boxes
    camera.draw_debug_box(screen)
    player.debug(screen)


    #drawing the health bar
    player.draw_health(screen)



# if player gets 'hit'
    if pygame.sprite.groupcollide(player_group, enemy_group, False, False):
        # if there's a collision, tell the player to get hit
        player.get_hit(amount = 5)
        # pygame.draw.rect(screen, (37, 232, 92), (0, 0, health.current_health, 20))
    pygame.display.flip()
    clock.tick(60)




