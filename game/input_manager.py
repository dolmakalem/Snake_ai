import pygame as pg

from game.enum import *


class InputManager:
    def __init__(self, game):
        self.game = game
        
    def check_for_input(self, events):
        for event in events:
            if event.type == pg.KEYDOWN:
                if event.key == pg.K_UP:
                    self.game.turn(Direction.UP)
                elif event.key == pg.K_DOWN:
                    self.game.turn(Direction.DOWN)
                elif event.key == pg.K_LEFT:
                    self.game.turn(Direction.LEFT)
                elif event.key == pg.K_RIGHT:
                    self.game.turn(Direction.RIGHT)
