import pygame as pg


class Renderer:
    def __init__(self, screen: pg.Surface, snake_size):
        self.screen = screen
        self.snake_color = pg.Color(255, 255, 255)
        self.snake_size = snake_size

    def update_game_state(self, gamestate):
        self.gamestate = gamestate

    def render(self):
        self.screen.fill(pg.Color(0, 0, 0))

        for s in self.gamestate.snake:
            pg.draw.rect(self.screen, self.snake_color, 
                            (
                            ((self.snake_size * s[0]) - (self.snake_size / 2)), 
                            ((self.snake_size * s[1]) - (self.snake_size / 2)), 
                            self.snake_size , 
                            self.snake_size
                            )
                        )