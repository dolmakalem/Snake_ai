import pygame as pg


class Renderer:
    def __init__(self, screen: pg.Surface, snake_size):
        self.score_font = pg.font.SysFont("Arial", 20)
        self.score_font_color = pg.Color(255, 0, 0)

        self.screen = screen

        self.snake_color = pg.Color(255, 255, 255)
        self.snake_size = snake_size

        self.food_color = pg.Color(0, 255, 0)


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

        pg.draw.circle(self.screen, self.food_color, 
                        (self.snake_size * self.gamestate.food[0], self.snake_size * self.gamestate.food[1]),
                        self.snake_size / 3)

        text_surface = self.score_font.render(f"Score: {self.gamestate.score}", True, self.score_font_color)
        self.screen.blit(text_surface, (10, 10))

            