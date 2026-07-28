import pygame as pg

from game.game import Game
from game.input_manager import InputManager
from game.renderer import Renderer


def game_loop():
    pg.init()

    DELTA_TIME_LIMIT = 100
    SNAKE_SIZE = 15
    GRID_PER_SCREEN = 40

    screen = pg.display.set_mode([SNAKE_SIZE * GRID_PER_SCREEN, SNAKE_SIZE * GRID_PER_SCREEN])

    game = Game(GRID_PER_SCREEN)
    input_manager = InputManager(game)
    renderer = Renderer(screen, SNAKE_SIZE)

    clock = pg.time.Clock()
    running = True
    last_frame = 0

    while running:
        events = pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                running = False

        input_manager.check_for_input(events)

        if pg.time.get_ticks() - last_frame > DELTA_TIME_LIMIT:
            last_frame = pg.time.get_ticks()

            game.step()

            renderer.update_game_state(game.get_state())

        renderer.render()
        pg.display.update()

        clock.tick(60)

if __name__ == "__main__":
    game_loop()