import pygame as pg

from game.game import Game
from game.input_manager import InputManager
from game.renderer import Renderer


def game_loop():
    pg.init()

    DELTA_TIME_LIMIT = 60
    SNAKE_SIZE = 20
    GRID_COUNT = 40
    GRID_SIZE = 20

    screen = pg.display.set_mode([GRID_SIZE * GRID_COUNT, GRID_SIZE * GRID_COUNT])

    game = Game(GRID_COUNT)
    input_manager = InputManager(game)
    renderer = Renderer(screen, GRID_SIZE, SNAKE_SIZE)

    clock = pg.time.Clock()
    running = True
    last_frame = 0

    while running:
        delta_time  = pg.time.get_ticks() - last_frame

        events = pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                running = False

        input_manager.check_for_input(events)

        if (delta_time) > DELTA_TIME_LIMIT:
            last_frame = pg.time.get_ticks()

            game.step()

            renderer.update_game_state(game.get_state())

        renderer.render(delta_time)
        pg.display.update()

        clock.tick(60)

if __name__ == "__main__":
    game_loop()