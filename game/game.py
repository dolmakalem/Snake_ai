from collections import deque
from dataclasses import dataclass

from game.enum import *

class Game:
    def __init__(self, grid_per_screen):
        self.snake = deque([((grid_per_screen // 2), (grid_per_screen // 2) + 2),
                            (grid_per_screen // 2, (grid_per_screen // 2) + 1),
                            (grid_per_screen // 2, (grid_per_screen // 2))])
        self.is_gameover = False
        self.score = 0
        self.food = (10, 10)
        self.current_pos = self.snake[-1]
        self.direction = Direction.UP
        self.new_direction = Direction.UP

    def move(self):
        if self.direction == Direction.UP or self.direction == Direction.DOWN:
            if self.new_direction == Direction.LEFT or self.new_direction == Direction.RIGHT:
                self.direction = self.new_direction
        elif self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
            if self.new_direction == Direction.UP or self.new_direction == Direction.DOWN:
                self.direction = self.new_direction

        self.current_pos = (self.current_pos[0] + self.direction.value[0], self.current_pos[1] + self.direction.value[1])
        self.snake.append(self.current_pos)
        self.snake.popleft()

    def turn(self, direction):
        self.new_direction = direction

    def get_state(self):
        return GameState(
            snake=tuple(self.snake),
            food=self.food,
            score=self.score,
            is_gameover=self.is_gameover
        )

@dataclass(frozen=True)
class GameState:
    snake: tuple
    food: tuple[int, int]
    score: int
    is_gameover: bool