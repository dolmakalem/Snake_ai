import random
from collections import deque
from dataclasses import dataclass

from game.enum import *


class Game:
    SCORE_PER_FOOD = 10
    SCORE_PER_SPECIAL_FOOD = 30

    SPECIAL_FOOD_STEP_TIME_LIMIT = 100

    def __init__(self, grid_count):
        self.grid_count = grid_count
        self.reset()

    def reset(self):
        self.snake = deque([((self.grid_count // 2), (self.grid_count // 2) + 2),
                            (self.grid_count // 2, (self.grid_count // 2) + 1),
                            (self.grid_count // 2, (self.grid_count // 2))])
        self.is_gameover = False
        self.score = 0

        self.current_pos = self.snake[-1]
        self.direction = Direction.UP
        self.new_direction = [Direction.UP]
        self.tail_direction = Direction.UP

        self.food_position = [-1, -1]
        self.special_food_position = [-1, -1]
        self.special_food_step_elapsed_time = 0
        self.food_counter = 0
        
        self.create_food()

    def step(self):
        if len(self.new_direction) > 0:
            new_direction = self.new_direction[0]
            if self.direction == Direction.UP or self.direction == Direction.DOWN:
                if new_direction == Direction.LEFT or new_direction == Direction.RIGHT:
                    self.direction = new_direction
            elif self.direction == Direction.LEFT or self.direction == Direction.RIGHT:
                if new_direction == Direction.UP or new_direction == Direction.DOWN:
                    self.direction = new_direction

            self.new_direction.pop(0)

        self.current_pos = (self.current_pos[0] + self.direction.value[0], self.current_pos[1] + self.direction.value[1])
        self.snake.append(self.current_pos)

        self.tail_direction = Direction((self.snake[0][0] - self.snake[1][0], self.snake[0][1] - self.snake[1][1]))

        self.special_food_step_elapsed_time += 1
        if self.special_food_step_elapsed_time >= self.SPECIAL_FOOD_STEP_TIME_LIMIT:
            self.special_food_position = [-1, -1]
            self.special_food_step_elapsed_time = 0

        collision_type = self.check_for_collisions()

        if collision_type == CollisionType.NONE:
            self.snake.popleft()
        elif collision_type == CollisionType.FOOD:
            self.score += self.SCORE_PER_FOOD + (self.score // 10)
            self.create_food()
        elif collision_type == CollisionType.SPECIAL_FOOD:
            self.score += self.SCORE_PER_SPECIAL_FOOD + (self.score // 10)
            self.special_food_position = [0, 0]
        elif (collision_type == CollisionType.WALL) or (collision_type == CollisionType.SNAKE):
            self.game_over()

    def game_over(self):
        self.reset()

    def turn(self, direction):
        self.new_direction.append(direction)

    def create_food(self):
        #TODO Shouldnt be created inside the snake
        self.food_position = (random.randint(1, self.grid_count - 1), random.randint(1, self.grid_count - 1))

        self.food_counter += 1

        if self.food_counter > 4:
            self.special_food_position = (random.randint(1, self.grid_count - 1), random.randint(1, self.grid_count - 1))
            self.food_counter = 0

    def check_for_collisions(self):
        if self.snake[-1] == self.food_position:
            return CollisionType.FOOD
        elif self.snake[-1] == self.special_food_position:
            return CollisionType.SPECIAL_FOOD
        elif (self.snake[-1][0] <= 0) or (self.snake[-1][0] > self.grid_count) or (self.snake[-1][1] <= 0) or (self.snake[-1][1] > self.grid_count):
            return CollisionType.WALL
        elif self.snake.count(self.snake[-1]) > 1:
            return CollisionType.SNAKE

        return CollisionType.NONE
        
    def get_state(self):
        return GameState(
            snake = tuple(self.snake),
            food_position = self.food_position,
            special_food_position = self.special_food_position,
            score = self.score,
            direction = self.direction,
            tail_direction = self.tail_direction,
            is_gameover = self.is_gameover
        )

@dataclass(frozen=True)
class GameState:
    snake: tuple
    food_position: tuple[int, int]
    special_food_position: tuple[int, int]
    score: int
    direction: Direction
    tail_direction: Direction
    is_gameover: bool