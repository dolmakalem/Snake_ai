import random
from collections import deque
from dataclasses import dataclass

import numpy as np

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
        # --- YENİ: O(1) çarpışma kontrolü için set, deque ile senkron tutulur ---
        self.snake_set = set(self.snake)

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
        action = Action.MOVE_ONLY

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

        # --- DEĞİŞTİ: Çarpışma kontrolü, head deque/set'e eklenmeden ÖNCE yapılıyor ---
        # (Eskiden: önce ekle, sonra snake.count(head) > 1 ile kontrol et -> O(n))
        # (Şimdi: eklemeden önce set'te var mı diye bak -> O(1))
        collision_type = self.check_for_collisions()

        self.snake.append(self.current_pos)
        self.snake_set.add(self.current_pos)

        self.tail_direction = Direction((self.snake[0][0] - self.snake[1][0], self.snake[0][1] - self.snake[1][1]))

        self.special_food_step_elapsed_time += 1
        if self.special_food_step_elapsed_time >= self.SPECIAL_FOOD_STEP_TIME_LIMIT:
            self.special_food_position = [-1, -1]
            self.special_food_step_elapsed_time = 0

        if collision_type == CollisionType.NONE:
            old_tail = self.snake.popleft()
            self.snake_set.discard(old_tail)
            action = Action.MOVE_ONLY
        elif collision_type == CollisionType.FOOD:
            self.score += self.SCORE_PER_FOOD + (self.score // 10)
            self.create_food()
            action = Action.ATE_FOOD
        elif collision_type == CollisionType.SPECIAL_FOOD:
            self.score += self.SCORE_PER_SPECIAL_FOOD + (self.score // 10)
            self.special_food_position = [0, 0]
            action = Action.ATE_SPECIAL_FOOD
        elif (collision_type == CollisionType.WALL):
            self.is_gameover = True
            action = Action.HIT_WALL
        elif (collision_type == CollisionType.SNAKE):
            self.is_gameover = True
            action = Action.HIT_SNAKE

        return action

    def game_over(self):
        self.reset()

    def turn(self, direction):
        self.new_direction.append(direction)

    def create_food(self):
        #TODO Shouldnt be created inside the snake
        self.food_position = (random.randint(0, self.grid_count - 1), random.randint(0, self.grid_count - 1))

        self.food_counter += 1
        if self.food_counter > 4:
            self.food_counter = 0

    def check_for_collisions(self):
        """
        DİKKAT: Bu fonksiyon artık current_pos, deque/set'e eklenmeden ÖNCE çağrılıyor.
        Bu yüzden self.snake[-1] yerine self.current_pos kullanılıyor,
        ve self-çarpışma kontrolü "current_pos zaten set'te var mı" ile yapılıyor (O(1)).
        """
        if self.current_pos == self.food_position:
            return CollisionType.FOOD
        elif self.current_pos == self.special_food_position:
            return CollisionType.SPECIAL_FOOD
        elif (self.current_pos[0] < 0) or (self.current_pos[0] >= self.grid_count) or (self.current_pos[1] < 0) or (self.current_pos[1] >= self.grid_count):
            return CollisionType.WALL
        elif self.current_pos in self.snake_set:
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

    def get_state_for_training(self):
        """
        DEĞİŞTİ: Python for-loop yerine numpy fancy indexing kullanıyor.
        Eskiden: for s in self.snake: snake_layer[s[0], s[1]] = 1  (yılan uzadıkça yavaşlıyordu)
        Şimdi: tüm koordinatlar tek seferde numpy array'e çevrilip toplu atanıyor.
        """
        food_layer = np.zeros((self.grid_count, self.grid_count), dtype=np.float32)
        snake_layer = np.zeros((self.grid_count, self.grid_count), dtype=np.float32)
        snake_head_layer = np.zeros((self.grid_count, self.grid_count), dtype=np.float32)

        food_layer[self.food_position[0], self.food_position[1]] = 1

        if len(self.snake) > 0:
            snake_array = np.array(self.snake, dtype=np.int32)  # şekil: (n, 2)
            xs = snake_array[:, 0]
            ys = snake_array[:, 1]

            # Sınır içindeki hücreleri filtrele (eski kod da bunu tek tek kontrol ediyordu)
            valid = (xs >= 0) & (xs < self.grid_count) & (ys >= 0) & (ys < self.grid_count)
            snake_layer[xs[valid], ys[valid]] = 1

        head_x, head_y = self.snake[-1][0], self.snake[-1][1]
        if 0 <= head_x < self.grid_count and 0 <= head_y < self.grid_count:
            snake_head_layer[head_x, head_y] = 1

        return np.stack([food_layer, snake_layer, snake_head_layer])


@dataclass(frozen=True)
class GameState:
    snake: tuple
    food_position: tuple[int, int]
    special_food_position: tuple[int, int]
    score: int
    direction: Direction
    tail_direction: Direction
    is_gameover: bool