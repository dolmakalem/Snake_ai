import pygame as pg

from game.game import Game
from game.input_manager import InputManager
from game.renderer import Renderer


def game_loop():
    pg.init()

    delta_time_limit = 100

    snake_size = 15
    grid_per_screen = 40

    screen = pg.display.set_mode([snake_size * grid_per_screen, snake_size * grid_per_screen])

    game = Game(grid_per_screen)
    input_manager = InputManager(game)
    renderer = Renderer(screen, snake_size)

    clock = pg.time.Clock()
    running = True
    last_frame = 0

    while running:
        events = pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                running = False

        input_manager.check_for_input(events)

        if pg.time.get_ticks() - last_frame > delta_time_limit:
            last_frame = pg.time.get_ticks()

            game.move()

            renderer.update_game_state(game.get_state())

        renderer.render()
        pg.display.update()

        clock.tick(60)

if __name__ == "__main__":
    game_loop()