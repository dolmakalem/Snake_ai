import random
from collections import deque
from dataclasses import dataclass

from game.enum import *


class Game:
    SCORE_PER_FOOD = 10

    def __init__(self, grid_per_screen):
        self.grid_per_screen = grid_per_screen
        self.reset()

    def reset(self):
        self.snake = deque([((self.grid_per_screen // 2), (self.grid_per_screen // 2) + 2),
                            (self.grid_per_screen // 2, (self.grid_per_screen // 2) + 1),
                            (self.grid_per_screen // 2, (self.grid_per_screen // 2))])
        self.is_gameover = False
        self.score = 0
        self.current_pos = self.snake[-1]
        self.direction = Direction.UP
        self.new_direction = Direction.UP
        self.create_food()

    def step(self):
        if self.direction == Direction.UP or self.direction == Direction.DOWN:
            if self.new_direction == Direction.LEFT or self.new_direction == Direction.RIGHT:
                self.direction = self.new_direction
        elif self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
            if self.new_direction == Direction.UP or self.new_direction == Direction.DOWN:
                self.direction = self.new_direction

        self.current_pos = (self.current_pos[0] + self.direction.value[0], self.current_pos[1] + self.direction.value[1])
        self.snake.append(self.current_pos)

        collision_type = self.check_for_collisions()

        if collision_type == CollisionType.NONE:
            self.snake.popleft()
        elif collision_type == CollisionType.FOOD:
            self.score += self.SCORE_PER_FOOD
            self.create_food()
        elif (collision_type == CollisionType.WALL) or (collision_type == CollisionType.SNAKE):
            self.game_over()

    def game_over(self):
        self.reset()

    def turn(self, direction):
        self.new_direction = direction

    def create_food(self):
        self.food_position = (random.randint(1, self.grid_per_screen - 1), random.randint(1, self.grid_per_screen - 1))

    def check_for_collisions(self):
        if self.snake[-1] == self.food_position:
            return CollisionType.FOOD
        elif (self.snake[-1][0] <= 0) or (self.snake[-1][0] > self.grid_per_screen) or (self.snake[-1][1] <= 0) or (self.snake[-1][1] > self.grid_per_screen):
            return CollisionType.WALL
        ## TODO Others

        return CollisionType.NONE
        
    def get_state(self):
        return GameState(
            snake=tuple(self.snake),
            food=self.food_position,
            score=self.score,
            is_gameover=self.is_gameover
        )

@dataclass(frozen=True)
class GameState:
    snake: tuple
    food: tuple[int, int]
    score: int
    is_gameover: bool