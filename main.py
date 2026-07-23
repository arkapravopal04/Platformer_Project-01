import pygame
import sys
from player_classes import Player
from camera import Camera


'''
this is the main game loop
1)for  now a temporary image is set to use the camera
2)...
'''


def main(max_frames=None, on_frame=None):
    """Run the game loop.

    max_frames / on_frame are optional hooks used for automated testing —
    normal play (`python main.py`) leaves both as None and behaves exactly
    like a standard infinite game loop.
    """

    #general setup
    pygame.init()
    size = (640,360)
    screen = pygame.display.set_mode(size)
    pygame.display.set_caption("rustbound")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    hint_font = pygame.font.Font(None, 20)


    #groups

    # player
    player_group = pygame.sprite.GroupSingle()
    player = Player()
    player_group.add(player)


    #surfaces and texts
    # background_image = pygame.image.load('random_images_not_sorted/big_pic.jpg').convert_alpha()
    background_image = pygame.image.load('random_images_not_sorted/big_pic_2.jpg').convert_alpha()

    #camera
    camera = Camera(player_reference=player,map_size=background_image.get_size(),screen_size=size)

    # wall collision: player can't be moved past the edges of the map
    player.set_world_bounds(background_image.get_width())


    #random sprites

    paused = False
    pause_start_time = 0

    #event loop
    running = True
    frame_count = 0
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = not paused
                    if paused:
                        pause_start_time = pygame.time.get_ticks()
                    else:
                        # Real time keeps ticking during a pause, but game
                        # time shouldn't. Shift the invincibility timer
                        # forward by however long we were paused, so
                        # resuming doesn't silently burn through (or beyond)
                        # the invincibility window. Any future timer-based
                        # system should get the same treatment here.
                        paused_duration = pygame.time.get_ticks() - pause_start_time
                        if player.is_invincible:
                            player.invincibility_timer += paused_duration

                #restart after death 
                if event.key == pygame.K_r and player.is_dead:
                    player.restart()
                    camera.snap_to_player()

                #no enemy is wired into main.py right now,
                # so this is the only way to test damage/death by hand.
                if event.key == pygame.K_h and not player.is_dead and not paused:
                    player.get_hit(amount=10)

                if event.key == pygame.K_c and not player.is_dead and not paused:
                    player.start_dash()

        if not paused:
            player_group.update()
            camera.update()

        #     so background, sprite, and hitbox all stay in sync ---
        screen.fill('#4c76a5')

        # background stuff
        # screen.blit(background_image,(0,0))
        screen.blit(background_image, camera.apply(background_image.get_rect(topleft=(0, 0))))

        screen.blit(player.image, camera.apply(player.rect))

        # debug boxes
        camera.draw_debug_box(screen)
        player.debug(screen, camera)

        #drawing the health bar
        player.draw_health(screen)
        player.draw_dash_indicator(screen)

        # small persistent control hint
        hint = hint_font.render("P: Pause   C: Dash   H: Take damage (debug)", True, (255, 255, 255))
        screen.blit(hint, (8, size[1] - 22))

        if player.is_dead:
            overlay = pygame.Surface(size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            text = font.render("GAME OVER - Press R to Restart", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(size[0] // 2, size[1] // 2)))
        elif paused:
            text = font.render("PAUSED", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(size[0] // 2, size[1] // 2)))

        pygame.display.flip()
        clock.tick(60)

        frame_count += 1
        if on_frame is not None:
            on_frame(frame_count, screen, player, camera, paused)
        if max_frames is not None and frame_count >= max_frames:
            running = False

    pygame.quit()
    if max_frames is None:
        sys.exit()


if __name__ == "__main__":
    main()