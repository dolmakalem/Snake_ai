import copy
import os
import random
from collections import Counter, deque
from dataclasses import dataclass

import numpy as np
import torch
from torch import nn

from game.enum import Action, Direction
from game.game import Game
from helper import plot


@dataclass
class Metrics:
    best_train_score: float = 0.0
    best_average_score: float = 0.0
    n_games: int = 0
    steps_without_food: int = 0
    total_steps: int = 0
    total_reward: float = 0.0
    games_since_last_save: int = 0

class TrainingHistory:
    def __init__(self):
        self.recent_scores = deque(maxlen=100)
        self.recent_rewards = deque(maxlen=100)
        self.recent_losses = deque(maxlen=100)
        # --- YENİ: Son 100 ölümün sebebini tutan kayan pencere ---
        self.recent_death_reasons = deque(maxlen=100)

        self.plot_scores = []
        self.plot_mean_scores = []
        self.plot_best_scores = []
        self.plot_wall_rates = []
        self.plot_snake_rates = []
        self.plot_timeout_rates = []

class TrainConfig:
    def __init__(self, model, learning_rate):
        self.optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
        self.criterion = nn.SmoothL1Loss()

        self.scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='max', factor=0.5, patience=1000000, verbose=True
        )

class Trainer:
    GRID_COUNT = 40

    MAX_MEMORY = 100000
    BATCH_SIZE = 128
    MIN_MEMORY = 5000
    GAMMA = 0.994
    MODEL_FILE_NAME = "snake_model.pth"
    LEARNING_RATE = 0.0001

    REWARD_ATE_FOOD = 50
    REWARD_ATE_SPECIAL_FOOD = 100
    REWARD_HIT_WALL = -100
    REWARD_HIT_SNAKE = -70
    REWARD_GAME_OVER = -100
    REWARD_GETTING_CLOSER = 1
    REWARD_GETTING_FARTHER = -2
    REWARD_LENGTH_LIMIT_FOR_PENALTY = 10

    def __init__(self):
        self.game = Game(self.GRID_COUNT)

        self.metrics = Metrics()
        self.training_history = TrainingHistory()

        torch.backends.cudnn.benchmark = True
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Device: {self.device}")

        self.memory = deque(maxlen=self.MAX_MEMORY)

        self.model = self.create_model()

        self.train_config = TrainConfig(self.model, self.LEARNING_RATE)

        self.target_model = copy.deepcopy(self.model).to(self.device)
        self.target_model.eval()

        if self.load_model():
            self.target_model.load_state_dict(self.model.state_dict())
            print("Model is loaded")

    def create_model(self):
        pooled_size = self.GRID_COUNT // 2  # MaxPool2d(2) boyutu yarıya indirir
        linear_input_size = 64 * pooled_size * pooled_size

        return nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Flatten(),
            nn.Linear(linear_input_size, 512),
            nn.ReLU(),
            nn.Linear(512, 3)
        ).to(self.device)

    def load_model(self):
        if os.path.exists(self.MODEL_FILE_NAME):
            checkpoint = torch.load(
                self.MODEL_FILE_NAME,
                map_location=self.device
            )

            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.train_config.optimizer.load_state_dict(
                checkpoint["optimizer_state_dict"]
            )
            self.metrics.n_games = checkpoint.get("n_games", 0)
            self.metrics.games_since_last_save = checkpoint.get("games_since_last_save", 0)

            self.metrics.best_average_score = checkpoint.get("best_average_score", 0.0)

            return True

        return False

    def save_model(self):
        torch.save({
            "model_state_dict": self.model.state_dict(),
            "optimizer_state_dict": self.train_config.optimizer.state_dict(),
            "n_games": self.metrics.n_games,
            "games_since_last_save": self.metrics.games_since_last_save,
            "best_average_score": self.metrics.best_average_score,
        }, self.MODEL_FILE_NAME)

    def train(self):
        while True:
            state_for_training = self.game.get_state_for_training()
            state_tensor = torch.tensor(state_for_training, dtype=torch.float32).unsqueeze(0).to(self.device)

            epsilon = max(1, 100 - (self.metrics.n_games // 100))

            if random.randint(1, 100) <= epsilon:
                action = random.randint(0, 2)
            else:
                with torch.no_grad():
                    q_values = self.model(state_tensor)
                    action = torch.argmax(q_values).item()

            match self.game.direction:
                case Direction.UP:
                    directions = [Direction.UP, Direction.RIGHT, Direction.LEFT]
                case Direction.RIGHT:
                    directions = [Direction.RIGHT, Direction.DOWN, Direction.UP]
                case Direction.DOWN:
                    directions = [Direction.DOWN, Direction.LEFT, Direction.RIGHT]
                case Direction.LEFT:
                    directions = [Direction.LEFT, Direction.UP, Direction.DOWN]

            new_direction = directions[action]
            self.game.turn(new_direction)

            reward, is_gameover = self.step_and_get_rewards()

            self.metrics.total_reward += reward

            next_state_for_training = self.game.get_state_for_training()

            self.memory.append((state_for_training, action, reward, next_state_for_training, is_gameover))

            self.metrics.total_steps += 1

            if len(self.memory) > self.MIN_MEMORY and self.metrics.total_steps % 4 == 0:
                mini_batch = random.sample(self.memory, self.BATCH_SIZE)

                loss_val = self.train_step(self.model, self.target_model, self.train_config.optimizer, self.train_config.criterion, mini_batch)
                self.training_history.recent_losses.append(loss_val)

            if is_gameover:
                self.metrics.best_train_score = max(self.metrics.best_train_score, self.game.score)

                self.training_history.recent_scores.append(self.game.score)
                self.training_history.recent_rewards.append(self.metrics.total_reward)

                self.metrics.games_since_last_save += 1

                if self.metrics.n_games % 10 == 0:
                    self.target_model.load_state_dict(self.model.state_dict())

                average_score = sum(self.training_history.recent_scores) / len(self.training_history.recent_scores)
                average_reward = sum(self.training_history.recent_rewards) / len(self.training_history.recent_rewards)
                average_loss = sum(self.training_history.recent_losses) / len(self.training_history.recent_losses) if self.training_history.recent_losses else 0.0

                if self.metrics.n_games > 10000:
                    self.train_config.scheduler.step(average_score)

                if average_score > self.metrics.best_average_score and len(self.training_history.recent_scores) == 100:
                    self.metrics.best_average_score = average_score
                    self.metrics.games_since_last_save = 0
                    self.save_model()
                    print(f"New record of '{average_score:.2f}' is saved")

                current_lr = self.train_config.optimizer.param_groups[0]['lr']

                # --- SON 100 OYUNA GÖRE ÖLÜM YÜZDESİ (kayan pencere) ---
                death_counts = Counter(self.training_history.recent_death_reasons)
                total_deaths = sum(death_counts.values())
                if total_deaths > 0:
                    pct_wall = (death_counts['wall'] / total_deaths) * 100
                    pct_snake = (death_counts['snake'] / total_deaths) * 100
                    pct_timeout = (death_counts['timeout'] / total_deaths) * 100
                else:
                    pct_wall = pct_snake = pct_timeout = 0.0

                print(f"Best: {self.metrics.best_train_score} | A. Score: {average_score:.2f} | Best A. Score: {self.metrics.best_average_score:.2f} |  A. Reward: {average_reward:.2f} | A. Loss: {average_loss:.4f} | Game: {self.metrics.n_games} | Score: {self.game.score} | Epsilon: %{epsilon} | Steps: {self.metrics.total_steps} | Plato: {self.metrics.games_since_last_save} | Kaza: Duvar %{pct_wall:.1f} - Gövde %{pct_snake:.1f} - Açlık %{pct_timeout:.1f}")

                # self.update_plot(
                #     self.game.score,
                #     average_score,
                #     self.metrics.best_train_score,
                #     pct_wall,
                #     pct_snake,
                #     pct_timeout,
                #     self.metrics.n_games
                # )

                self.metrics.total_reward = 0
                self.game.reset()
                self.metrics.n_games += 1

    def train_step(self, model, target_model, optimizer, criterion, mini_batch):
        states, actions, rewards, next_states, dones = zip(*mini_batch)

        state_tensor = torch.tensor(np.array(states), dtype=torch.float32).to(self.device)
        next_state_tensor = torch.tensor(np.array(next_states), dtype=torch.float32).to(self.device)
        action_tensor = torch.tensor(actions, dtype=torch.long).to(self.device)
        reward_tensor = torch.tensor(rewards, dtype=torch.float32).to(self.device)
        done_tensor = torch.tensor(dones, dtype=torch.float32).to(self.device)

        pred_q = model(state_tensor).gather(1, action_tensor.unsqueeze(1)).squeeze(1)

        with torch.no_grad():
            next_q = target_model(next_state_tensor).max(1)[0]
            target_q = reward_tensor + self.GAMMA * next_q * (1 - done_tensor)

        loss = criterion(pred_q, target_q)

        optimizer.zero_grad()
        loss.backward()
        torch.nn.utils.clip_grad_norm_(model.parameters(), max_norm=10.0)
        optimizer.step()

        return loss.item()

    def step_and_get_rewards(self):
        current_state = self.game.get_state()

        head_x, head_y = current_state.snake[-1]
        food_x, food_y = current_state.food_position

        old_distance = abs(head_x - food_x) + abs(head_y - food_y)

        game_action = self.game.step()

        new_state = self.game.get_state()
        is_gameover = new_state.is_gameover

        reward = 0

        if game_action == Action.MOVE_ONLY:
            new_head_x, new_head_y = new_state.snake[-1]
            new_distance = abs(new_head_x - food_x) + abs(new_head_y - food_y)

            if new_distance < old_distance:
                reward = self.REWARD_GETTING_CLOSER
            else:
                reward = self.REWARD_GETTING_FARTHER

            self.metrics.steps_without_food += 1
        elif game_action == Action.ATE_FOOD:
            reward = self.REWARD_ATE_FOOD
            self.metrics.steps_without_food = 0
        elif game_action == Action.ATE_SPECIAL_FOOD:
            reward = self.REWARD_ATE_SPECIAL_FOOD
            self.metrics.steps_without_food = 0
        elif game_action == Action.HIT_SNAKE:
            reward = self.REWARD_HIT_SNAKE
            self.metrics.steps_without_food = 0
            self.training_history.recent_death_reasons.append('snake')
        elif game_action == Action.HIT_WALL:
            reward = self.REWARD_HIT_WALL
            self.metrics.steps_without_food = 0
            self.training_history.recent_death_reasons.append('wall')

        if self.metrics.steps_without_food > (self.GRID_COUNT * 6) + (len(self.game.snake) * 10):
            is_gameover = True
            reward = self.REWARD_GAME_OVER
            self.metrics.steps_without_food = 0
            self.training_history.recent_death_reasons.append('timeout')

        return reward, is_gameover

    def update_plot(self, game_score, average_score, best_score, pct_wall, pct_snake, pct_timeout, n_games):
        self.training_history.plot_scores.append(game_score)
        self.training_history.plot_mean_scores.append(average_score)
        self.training_history.plot_best_scores.append(best_score)
        self.training_history.plot_wall_rates.append(pct_wall)
        self.training_history.plot_snake_rates.append(pct_snake)
        self.training_history.plot_timeout_rates.append(pct_timeout)

        if n_games % 100 == 0:
            plot(
                self.training_history.plot_scores,
                self.training_history.plot_mean_scores,
                self.training_history.plot_best_scores,
                self.training_history.plot_wall_rates,
                self.training_history.plot_snake_rates,
                self.training_history.plot_timeout_rates,
                self.metrics.best_average_score
            )

if __name__ == "__main__":
    trainer = Trainer()
    trainer.train()