import asyncio
import sys
from collections import deque
import pygame
from player_classes import Player
from camera import Camera
import tower as tower_module
from tower import Tower, LOOKAHEAD, CULL_MARGIN
from background import Backdrop
from devmode import DevMode
import tiles
import save_data
from screen_mode import ScreenMode

# True when running under pygbag's in-browser Python (Emscripten). Used to
# gate behaviour that only makes sense - or only breaks things - on the web:
# dev-mode's authoring keys collide with browser shortcuts (F5 reloads the
# page, not the segments), and there's no local disk to write a save file
# to. See devmode.py's own WEB check and save_data.py's web branch.
WEB = sys.platform == 'emscripten'

PIXELS_PER_METER = 24  # purely a display unit for the altitude score

# F3 dev-warp presets (world height above ground_y) - cycles through these
# so a segment being designed way up the tower can be reached instantly
# instead of climbing there for real on every test run.
ALTITUDE_WARPS = [0, 1000, 3000, 6000, 10000, 16000, 24000]

# how many recent frames the F6 perf overlay's rolling stats cover
PERF_WINDOW = 180


'''
this is the main game loop
1)for  now a temporary image is set to use the camera
2)...
'''


async def main(max_frames=None, on_frame=None):
    """Run the game loop.

    max_frames / on_frame are optional hooks used for automated testing —
    normal play (`python main.py`) leaves both as None and behaves exactly
    like a standard infinite game loop.

    async because the pygbag/Emscripten build needs to yield to the browser
    once a frame (see the `await asyncio.sleep(0)` right after flip() below)
    - without it the tab's own event loop never gets a turn and the page
    looks hung. `asyncio.run(main())` at the bottom drives this on desktop
    exactly the same way a plain `while running:` loop would.
    """

    #general setup
    pygame.init()
    size = (640,360)
    # ScreenMode owns the display: it opens the same 640x360 window as
    # before and handles the V/F11 switch to fullscreen (see screen_mode.py)
    screen_mode = ScreenMode(size)
    screen = screen_mode.surface
    pygame.display.set_caption("rustbound")
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 36)
    hint_font = pygame.font.Font(None, 20)


    #groups

    # player
    player_group = pygame.sprite.GroupSingle()
    player = Player()
    player_group.add(player)



    # NOTE: extension case must match the file on disk exactly - Windows is
    # case-insensitive about it, Linux/macOS are not.
    background_image = pygame.image.load('random_images_not_sorted/big_pic_2.JPG').convert_alpha()

    ground_margin = 0
    player.set_ground_level(background_image.get_height() - ground_margin)

    #camera
    camera = Camera(player_reference=player,map_size=background_image.get_size(),screen_size=size)
    # start already settled on the player instead of visibly trailing in
    # from a cold (0,0) offset - same reasoning as the post-restart snap
    camera.snap_to_player()

    # wall collision: player can't be moved past the edges of the map
    player.set_world_bounds(background_image.get_width())

    # the endless tower - segments stream in above the player and get torn
    # down well below; groups are created once and mutated in place, so
    # binding them to the player here stays valid for the whole run
    tower = Tower(ground_y=player.ground_y)
    player.set_platforms(tower.groups['landable'])
    player.set_walls(tower.groups['blocking'])
    # pay for every block's first-ever render now, while the player hasn't
    # moved yet, instead of spread across the first few minutes of climbing
    tower.prewarm_render_cache()

    best_score = save_data.load_best()
    current_score = 0
    player_altitude = 0
    # True once best_score has advanced past what's on disk; flushed on
    # death and on exit so a run's result survives even if it's never
    # written mid-climb
    best_unsaved = False

    paused = False
    pause_start_time = 0
    # hitbox/camera debug overlays - off by default, toggled with F1
    debug_draw = False
    # creative mode: authoring sandbox, toggled with F4. Inert unless active.
    dev = DevMode(ground_y=player.ground_y,
                  world_width=background_image.get_width())
    # animated backdrop - sky gradient plus a per-altitude background.
    # Art lives in backgrounds/; see backgrounds/README.md.
    backdrop = Backdrop(ground_y=player.ground_y, screen_size=size)
    # segment-seam / altitude authoring overlay - off by default, F2
    level_overlay = False
    # index into ALTITUDE_WARPS the next F3 press jumps to
    warp_index = 0
    # perf readout - off by default, F6. Rolling per-frame timings (ms) plus
    # whether ensure_window streamed a segment in/out that frame, so a spike
    # can be told apart from ordinary frame-to-frame jitter.
    perf_overlay = False
    perf_samples = deque(maxlen=PERF_WINDOW)
    perf_stream_events = deque(maxlen=PERF_WINDOW)

    #event loop
    running = True
    frame_count = 0
    # ms elapsed last frame, from clock.tick() below - drives the backdrop
    # animation off real time rather than frame count, so it plays at the
    # same speed if the frame rate ever changes
    frame_ms = 16
    # How long one simulation step represents. The whole game is authored
    # against this: gravity, jump velocity, sprint speed and the dash are
    # all per-step constants, so a step is the unit the level geometry was
    # tuned in.
    STEP_MS = 1000.0 / 60.0
    # Unspent real time carried between frames on the web build (see the
    # stepping block further down). Desktop leaves it at zero.
    sim_accumulator = 0.0
    # Ceiling on how much a single slow frame may catch up. Without it, one
    # long stall (the ~1s first frame while pygbag unpacks assets, or a
    # backgrounded tab) would try to replay every missed step at once and
    # teleport the player through the level.
    MAX_CATCHUP_STEPS = 5
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # Dev/authoring tools (F1-F6, creative mode) are desktop-only:
            # F1/F3/F5/F6 collide with browser-reserved shortcuts (help,
            # find, refresh, focus-address-bar) that steal input focus from
            # the canvas, F5's hot-reload has no live segment files to
            # reload from once shipped, and creative mode is an authoring
            # sandbox with nothing for a player to do in it. `dev` still
            # exists on web (see its construction above) - it just never
            # receives the event that would turn it on, so dev.active stays
            # False and every `if dev.active:` branch below is inert.
            if not WEB and event.type == pygame.KEYDOWN and event.key == pygame.K_F4:
                dev.toggle(player, tower)
                # While authoring, show each segment only where it first
                # appears. Otherwise a level with one or two segments repeats
                # them up the whole tower and your own geometry looks like it
                # was duplicated infinitely.
                tower.hide_repeats = dev.active
                tower.ensure_window(player_altitude - CULL_MARGIN,
                                    player_altitude + LOOKAHEAD,
                                    max_build=10_000)
                continue

            # creative mode claims its own bindings first (N/J/G/F/E/X/1-4/
            # brackets/clicks). Anything it doesn't want falls through to the
            # normal game bindings below, so A/D/Space/C still work in it.
            if dev.active and dev.handle_event(event, player, camera, tower):
                continue

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
                        # dash cooldown is the other wall-clock timer, so it
                        # gets the same shift - otherwise a long pause silently
                        # refunds the cooldown and hands back a free dash.
                        player.last_dash_time += paused_duration

                # --- feature: restart after death ---
                if event.key == pygame.K_r and player.is_dead:
                    player.restart()
                    camera.snap_to_player()

                # debug helper: no enemy is wired into main.py right now,
                # so this is the only way to test damage/death by hand.
                if event.key == pygame.K_h and not player.is_dead and not paused:
                    player.get_hit(amount=10)

                # --- feature: dash ---
                if event.key == pygame.K_c and not player.is_dead and not paused:
                    player.start_dash()

                # --- feature: fullscreen / windowed toggle ---
                # V works everywhere; F11 is the conventional binding but
                # only on desktop - in a browser it belongs to the browser,
                # which takes the whole tab fullscreen before the canvas
                # ever sees the key.
                if event.key == pygame.K_v or (not WEB and event.key == pygame.K_F11):
                    # rebind: on desktop a mode switch re-runs set_mode(),
                    # which hands back a new display surface
                    screen = screen_mode.toggle()

                if not WEB and event.key == pygame.K_F1:
                    debug_draw = not debug_draw

                if not WEB and event.key == pygame.K_F2:
                    level_overlay = not level_overlay

                if not WEB and event.key == pygame.K_F6:
                    perf_overlay = not perf_overlay

                # --- dev tool: hot-reload segment files without restarting ---
                # picks up edits to segments/*.py immediately; the tower
                # regenerates from the ground up so the new geometry is
                # consistent, which means it also resets any progress this
                # run - that's expected for an authoring tool, not a bug.
                if not WEB and event.key == pygame.K_F5:
                    tower_module.reload_segments()
                    # the player is sent back to the ground below, so only
                    # the bottom of the tower needs building here - the
                    # normal per-frame extend_to takes it from there
                    tower.rebuild(target_h=LOOKAHEAD)
                    backdrop.reload()      # pick up new/changed background art
                    tiles.reload()         # ...and new/changed block sprites
                    player.restart()
                    camera.snap_to_player()

                # --- dev tool: jump straight to an altitude preset, to test
                # a segment high up the tower without climbing there first ---
                if not WEB and event.key == pygame.K_F3:
                    target_h = ALTITUDE_WARPS[warp_index % len(ALTITUDE_WARPS)]
                    warp_index += 1
                    # build the destination BEFORE moving the player, so
                    # there's always solid ground to land on the instant
                    # they arrive
                    tower.extend_to(target_h + LOOKAHEAD, max_build=10_000)
                    player.rect.bottom = player.ground_y - target_h
                    player.vertical_momentum = 0
                    player.standing_platform = None
                    player.is_dashing = False
                    camera.snap_to_player()

        # A save just happened: reload the segment files, rebuild the tower
        # against them, and drop the player into the segment they saved. A
        # new segment is placed after every existing one, so without this
        # warp it lands hundreds of metres up and saving looks like it did
        # nothing at all.
        if dev.pending_reload:
            saved_name = dev.pending_reload
            dev.pending_reload = None
            tower_module.reload_segments()
            tower.rebuild(target_h=LOOKAHEAD)
            dev.draft = []
            dev.editing = None
            dev.blank = False
            dev.preview_entities = []
            target_h = tower.find_segment_base(saved_name)
            if target_h is None:
                dev.notify(f'saved, but {saved_name} is not in the rotation')
            else:
                tower.extend_to(target_h + LOOKAHEAD, max_build=10_000)
                dev.floor_h = target_h
                player.rect.bottom = player.ground_y - target_h
                player.vertical_momentum = 0
                player.standing_platform = None
                camera.snap_to_player()
                dev.notify(f'saved - now standing in {saved_name} at h={target_h}')

        # altitude is how the tower knows how far to build/cull, and also
        # doubles as the score - the higher you've ever gotten, the higher
        # your score, independent of falling back down. Computed every
        # frame (not just while unpaused) so the F5/F3 dev tools above
        # always have a current value to work with.
        player_altitude = max(0, player.ground_y - player.rect.bottom)

        streamed = False

        # --- how many simulation steps this frame is worth ---
        #
        # Every movement constant in the game is per-step, so game speed is
        # decided purely by how often this block runs. On desktop that is
        # settled by clock.tick(60) at the bottom of the loop: one frame,
        # one step, exactly 60 a second.
        #
        # The browser gives no such guarantee. pygbag resumes this coroutine
        # from the page's animation-frame callback, so the loop runs at the
        # display's refresh rate - 120 steps a second on a 120Hz panel, and
        # none at all while the tab isn't being painted - and clock.tick(60)
        # can't rein that in, because a busy-wait on the browser's one thread
        # only pushes the next animation frame further out. Stepping once per
        # animation frame therefore ran the web build at the monitor's speed
        # rather than the game's, which is what stopped frame-tuned moves
        # like the sprint jump over a wall from landing the way they do on
        # desktop.
        #
        # So on web, take the step count from the wall clock instead: bank
        # the elapsed milliseconds and spend them in whole 60Hz steps. The
        # simulation then advances at the same rate it does on desktop
        # whatever the browser's frame rate is, and only the smoothness of
        # the drawing varies with it.
        if paused:
            # don't bank time while the game is stopped, or unpausing would
            # spend the whole pause at once
            sim_accumulator = 0.0
        elif WEB:
            sim_accumulator = min(sim_accumulator + frame_ms,
                                  STEP_MS * MAX_CATCHUP_STEPS)
        else:
            sim_accumulator = STEP_MS

        while sim_accumulator >= STEP_MS:
            sim_accumulator -= STEP_MS
            # one call streams in above AND restores below, so falling
            # back down lands on the platforms you fell past rather than
            # dropping through a void. `or streamed` so a frame that ran
            # several steps still reports a hitch to the F6 perf overlay
            # rather than only reporting its last step.
            streamed = tower.ensure_window(player_altitude - CULL_MARGIN,
                                           player_altitude + LOOKAHEAD) or streamed

            # update every entity, not just platforms - anything with its
            # own animation or motion (a bobbing marker, a future timed
            # hazard) ticks here too. Entity.update() is a no-op by default,
            # so static slabs cost nothing.
            backdrop.update(STEP_MS)
            for entity in tower.draw_list:
                entity.update()
            for entity in dev.preview_entities:
                entity.update()

            # Trapdoors (and anything else tagged "collapsible") need to
            # know whether the player is CURRENTLY standing on them, which
            # only main.py can tell them - it's the one place that knows
            # about Player. Uses last frame's standing_platform, same as
            # apply_platform_ride() below; player_group.update() recomputes
            # it fresh a few lines down, so a door that opens this frame is
            # already out of the landable group before gravity runs.
            #
            # Gated on noclip, not on dev.active: creative mode with noclip
            # OFF is exactly how you playtest real jumps/timing while
            # placing blocks, and a trapdoor placed to test needs to
            # actually spring in that mode or there's no way to try it
            # without leaving creative mode entirely. Only skip this while
            # flying, where standing_platform isn't a meaningful concept.
            if not (dev.active and dev.noclip):
                for entity in list(tower.groups.get('collapsible', ())):
                    if not player.is_dead and player.standing_platform is entity:
                        entity.on_stand()
                    else:
                        entity.on_leave()

            if dev.active and dev.noclip:
                # creative mode flight: bypass gravity and collision entirely
                dev.fly(player)
            else:
                player.apply_platform_ride()
                player_group.update()
            camera.update()

            if not player.is_dead and not dev.active:
                hit_hazard = pygame.sprite.spritecollideany(player, tower.groups['damaging'])
                if hit_hazard is not None:
                    player.get_hit(amount=hit_hazard.damage)

            # Ratchet: the best only ever goes up, so falling costs time
            # but never score. Kept in memory and flushed to disk on death
            # / exit rather than here - see save_data.save_best.
            current_score = player_altitude // PIXELS_PER_METER
            if current_score > best_score:
                best_score = current_score
                best_unsaved = True

            if player.is_dead and best_unsaved:
                save_data.save_best(best_score)
                best_unsaved = False

            # the player moved, so the value read at the top of the frame is
            # stale - refresh it for the next step and for the drawing below
            player_altitude = max(0, player.ground_y - player.rect.bottom)


        backdrop.draw(screen, camera)

        # background stuff
        # screen.blit(background_image,(0,0))
        screen.blit(background_image, camera.apply(background_image.get_rect(topleft=(0, 0))))

        # one pass over every live entity, pre-sorted by DRAW_LAYER, so a
        # new entity type renders correctly without editing this loop
        for entity in tower.draw_list:
            screen.blit(entity.image, camera.apply(entity.rect))

        if dev.active:
            for entity in dev.preview_entities:
                screen.blit(entity.image, camera.apply(entity.rect))
            dev.draw_world(screen, camera)

        # draw() aligns the sprite to the hitbox rather than blitting at it -
        # animation frames differ in size, so the two are no longer the same
        # rectangle (see Player.draw)
        player.draw(screen, camera)

        if dev.active:
            dev.draw_overlay(screen, camera, player, tower, hint_font)

        # debug boxes - hidden unless F1 is toggled on
        if debug_draw:
            camera.draw_debug_box(screen)
            player.debug(screen, camera)

        # segment-authoring overlay - hidden unless F2 is toggled on. Shows
        # where each built segment's ceiling seam is, which segment the
        # player is currently standing inside, and the world coordinates
        # under the mouse cursor - the numbers you need on hand while
        # tuning a segment file, without leaving the running game.
        if level_overlay:
            top_world_y = -camera.offset.y
            bottom_world_y = top_world_y + size[1]
            low_h = player.ground_y - bottom_world_y
            high_h = player.ground_y - top_world_y
            for seam_h, seam_name in tower.segment_seams(low_h, high_h):
                seam_screen_y = int((player.ground_y - seam_h) + camera.offset.y)
                pygame.draw.line(screen, (255, 80, 220), (0, seam_screen_y), (size[0], seam_screen_y), 1)
                label = hint_font.render(f"^ {seam_name}", True, (255, 80, 220))
                screen.blit(label, (4, seam_screen_y - 16))

            current_segment = tower.segment_at(player_altitude)
            info = hint_font.render(
                f"alt {int(player_altitude)}  seg: {current_segment}", True, (255, 255, 0))
            screen.blit(info, (8, 40))
            bg_info = hint_font.render(
                f"bg: {backdrop.describe(player_altitude)}  frame {backdrop.frame + 1}",
                True, (255, 255, 0))
            screen.blit(bg_info, (8, 56))

            mx, my = pygame.mouse.get_pos()
            world_x = mx - camera.offset.x
            world_y = my - camera.offset.y
            cursor_h = player.ground_y - world_y
            cursor_text = hint_font.render(
                f"x={int(world_x)} h={int(cursor_h)}", True, (255, 255, 0))
            screen.blit(cursor_text, (mx + 12, my + 12))

        # per-frame timing readout - hidden unless F6 is toggled on. Meant
        # for spotting streaming hitches (see tower.ensure_window's return
        # value) rather than measuring steady-state fps. Note this is the
        # *drawing* rate: on web it follows the browser's animation frames,
        # while the simulation stays at 60 steps a second either way.
        if perf_overlay and perf_samples:
            samples = sorted(perf_samples)
            n = len(samples)
            p50 = samples[n // 2]
            p99 = samples[min(n - 1, int(n * 0.99))]
            worst = samples[-1]
            stream_count = sum(1 for s in perf_stream_events if s)
            perf_text = hint_font.render(
                f"frame ms  p50={p50}  p99={p99}  max={worst}  "
                f"(over {n}f, {stream_count} streamed)",
                True, (120, 255, 160))
            screen.blit(perf_text, (8, 72))

        #drawing the health bar
        player.draw_health(screen)
        player.draw_dash_indicator(screen)

        # altitude / best-score readout, top-right
        score_text = hint_font.render(f"Height: {current_score}m", True, (255, 255, 255))
        screen.blit(score_text, score_text.get_rect(topright=(size[0] - 8, 8)))
        best_text = hint_font.render(f"Best: {best_score}m", True, (255, 210, 120))
        screen.blit(best_text, best_text.get_rect(topright=(size[0] - 8, 24)))

        # small persistent control hint - the dev/authoring keys (F1-F6)
        # don't exist on the web build (see the WEB gate above), so don't
        # advertise them there. Two lines, not one: at this font size all
        # the keys together run past the screen's 640px width and get
        # silently clipped at the edge.
        hint = hint_font.render(
            "A/D: Move  Shift: Sprint  Space: Jump  C: Dash  P: Pause  V: Screen",
            True, (255, 255, 255))
        screen.blit(hint, (8, size[1] - 22))
        if not WEB:
            dev_hint = hint_font.render(
                "F1: Hitboxes  F2: Segments  F3: Warp  F5: Reload  F6: Perf",
                True, (255, 255, 255))
            screen.blit(dev_hint, (8, size[1] - 38))

        if player.is_dead:
            overlay = pygame.Surface(size, pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 150))
            screen.blit(overlay, (0, 0))
            text = font.render("GAME OVER - Press R to Restart", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(size[0] // 2, size[1] // 2)))
        elif paused:
            text = font.render("PAUSED", True, (255, 255, 255))
            screen.blit(text, text.get_rect(center=(size[0] // 2, size[1] // 2)))

        # scales + centres the frame when we're in fullscreen; a plain
        # flip() otherwise (see screen_mode.py)
        screen_mode.present()
        # hand control back to the browser once a frame - required for the
        # pygbag/Emscripten build to render/process input at all; a no-op
        # await on desktop, so this runs identically either way
        await asyncio.sleep(0)
        # Desktop: cap at 60fps, which is also what paces the simulation.
        # Web: measure only. The browser already decides when we run again,
        # and clock.tick's wait is a busy-wait on the single thread the page
        # renders on - asking for 60 there burns the rest of the frame
        # budget and delays the next animation frame instead of hitting the
        # target. The stepping block above is what holds game speed steady.
        frame_ms = clock.tick() if WEB else clock.tick(60)
        perf_samples.append(frame_ms)
        perf_stream_events.append(streamed)

        frame_count += 1
        if on_frame is not None:
            on_frame(frame_count, screen, player, camera, paused)
        if max_frames is not None and frame_count >= max_frames:
            running = False

    # flush the run's best on the way out (quit, or the test harness's
    # max_frames cutoff) - the in-loop path only saves on death
    if best_unsaved:
        save_data.save_best(best_score)

    pygame.quit()
    # No sys.exit() here: returning lets asyncio.run(main()) finish
    # normally on both desktop and the pygbag/Emscripten build - calling
    # sys.exit() (SystemExit) from inside a coroutine running under
    # Emscripten kills the page's whole Python runtime rather than just
    # ending the game cleanly.


if __name__ == "__main__":
    asyncio.run(main())