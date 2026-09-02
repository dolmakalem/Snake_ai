from enum import Enum


class Direction(Enum):
    UP = (0, -1)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    RIGHT = (1, 0)

class CollisionType(Enum):
    NONE = 0
    FOOD = 1
    WALL = 2
    SNAKE = 3
    SPECIAL_FOOD = 4

class Action(Enum):
    MOVE_ONLY = 0
    ATE_FOOD = 1
    ATE_SPECIAL_FOOD = 2
    HIT_WALL = 3
    HIT_SNAKE = 4