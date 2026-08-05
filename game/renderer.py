import random

import pygame as pg
import pygame.gfxdraw as gfx

from game.enum import *


class Renderer:
    SCORE_FONT_COLOR = pg.Color(255, 0, 0)
    SNAKE_COLOR = pg.Color(255, 255, 255)
    FOOD_COLOR = pg.Color(0, 255, 0)
    SPECIAL_FOOD_COLOR = pg.Color(155, 155, 0)

    RAIN_DROP_COLOR = pg.Color(80, 80, 80)
    RAIN_DROP_DELTA_DELAY = 10
    RAIN_DROP_ANIM_LENGTH = 20

    def __init__(self, screen: pg.Surface, grid_size, snake_size):
        self.screen = screen
        self.grid_size = grid_size
        self.snake_size = snake_size

        self.rain_drops = [[10, 10, 0]]
        self.rain_drop_delta = 0

        self.score_font = pg.font.SysFont("Arial", 20)

    def update_game_state(self, gamestate):
        self.gamestate = gamestate

    def render(self, delta_time):
        self.screen.fill(pg.Color(0, 0, 0))

        self.rain_drop_delta += delta_time

        for s in self.gamestate.snake:
            pg.draw.rect(self.screen, self.SNAKE_COLOR, 
                            (((self.grid_size * s[0]) - (self.grid_size / 2)), 
                            ((self.grid_size * s[1]) - (self.grid_size / 2)), 
                            self.snake_size , 
                            self.snake_size))

        s = self.gamestate.snake[-1]

        snake_head_x = (self.grid_size * s[0]) + (self.gamestate.direction.value[0] * (self.grid_size // 2))
        snake_head_y = (self.grid_size * s[1]) + (self.gamestate.direction.value[1] * (self.grid_size // 2))
        
        s = self.gamestate.snake[0]

        snake_tail_x = (self.grid_size * s[0]) + (self.gamestate.tail_direction.value[0] * (self.grid_size // 2))
        snake_tail_y = (self.grid_size * s[1]) + (self.gamestate.tail_direction.value[1] * (self.grid_size // 2))

        gfx.filled_circle(self.screen, snake_head_x, snake_head_y, int(self.snake_size / 2) - 1, self.SNAKE_COLOR)
        gfx.aacircle(self.screen, snake_head_x, snake_head_y, int(self.snake_size / 2) - 1, self.SNAKE_COLOR)

        gfx.filled_circle(self.screen, snake_tail_x, snake_tail_y, int(self.snake_size / 2) - 1, self.SNAKE_COLOR)
        gfx.aacircle(self.screen, snake_tail_x, snake_tail_y, int(self.snake_size / 2) - 1, self.SNAKE_COLOR)

        gfx.filled_circle(self.screen, self.grid_size * self.gamestate.food_position[0], 
                          self.grid_size * self.gamestate.food_position[1],
                          int(self.snake_size / 3) - 1, self.FOOD_COLOR)
        gfx.aacircle(self.screen, self.grid_size * self.gamestate.food_position[0], 
                          self.grid_size * self.gamestate.food_position[1],
                          int(self.snake_size / 3) - 1, self.FOOD_COLOR)

        gfx.filled_circle(self.screen, self.grid_size * self.gamestate.special_food_position[0], 
                          self.grid_size * self.gamestate.special_food_position[1],
                          int(self.snake_size / 2) - 1, self.SPECIAL_FOOD_COLOR)
        gfx.aacircle(self.screen, self.grid_size * self.gamestate.special_food_position[0], 
                          self.grid_size * self.gamestate.special_food_position[1],
                          int(self.snake_size / 2) - 1, self.SPECIAL_FOOD_COLOR)

        for rain_drop in self.rain_drops:
            rain_drop[2] += (self.rain_drop_delta / 10)
            if rain_drop[2] <= self.RAIN_DROP_ANIM_LENGTH:
                gfx.aacircle(self.screen,
                                rain_drop[0], 
                                rain_drop[1],
                                int(rain_drop[2]), self.RAIN_DROP_COLOR) 

        for rain_drop in self.rain_drops:
            if rain_drop[2] >= self.RAIN_DROP_ANIM_LENGTH:
                del rain_drop

        if self.rain_drop_delta >= self.RAIN_DROP_DELTA_DELAY:
            self.rain_drops.append([random.randint(0, self.screen.get_size()[0]), random.randint(0, self.screen.get_size()[1]), 0])
            self.rain_drop_delta = 0

        text_surface = self.score_font.render(f"Score: {self.gamestate.score}", True, self.SCORE_FONT_COLOR)
        self.screen.blit(text_surface, (10, 10))

            