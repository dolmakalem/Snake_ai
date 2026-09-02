import os
from collections import deque
import pygame as pg
import torch
from torch import nn
import numpy as np

from game.game import Game
from game.renderer import Renderer
from game.enum import Direction, Action

def ai_game_loop():
    pg.init()
    pg.font.init()

    # --- AYARLAR ---
    DELTA_TIME_LIMIT = 200  
    GRID_COUNT = 10        
    GRID_SIZE = 40         
    SNAKE_SIZE = 40        

    screen = pg.display.set_mode([GRID_SIZE * GRID_COUNT, GRID_SIZE * GRID_COUNT])
    pg.display.set_caption("Snake AI - İzleme ve Ödül Modu")

    font = pg.font.SysFont("Arial", 22, bold=True)

    game = Game(GRID_COUNT)
    renderer = Renderer(screen, GRID_SIZE, SNAKE_SIZE)

    # --- YAPAY ZEKA (BEYİN) HAZIRLIĞI ---
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Yapay zeka {device} üzerinde çalışıyor...")

    linear_input_size = 64 * GRID_COUNT * GRID_COUNT

    model = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1),
            nn.ReLU(),
            nn.Conv2d(32, 64, 3, padding=1),
            nn.ReLU(),
            nn.Flatten(),
            nn.Linear(linear_input_size, 512),
            nn.ReLU(),
            nn.Linear(512, 3)
    ).to(device)

    if os.path.exists("snake_model.pth"):
        checkpoint = torch.load("snake_model.pth", map_location=device)
        model.load_state_dict(checkpoint["model_state_dict"])
        print("\033[92mEğitilmiş model başarıyla yüklendi! Şov başlıyor...\033[0m")
    else:
        print("\033[91mHATA: snake_model.pth bulunamadı! Lütfen dosyanın dizinini kontrol edin.\033[0m")
        return

    model.eval()  

    clock = pg.time.Clock()
    running = True
    last_frame = pg.time.get_ticks()
    
    # --- LOG VE METRİK HAZIRLIKLARI ---
    step_logs = deque(maxlen=150) 
    action_chars = ["D", "S", "L"] 
    
    current_score = 0
    steps_without_food = 0
    
    current_step_reward = 0.0     # Anlık reward takibi
    total_episode_reward = 0.0    # O oyunun toplam reward takibi

    # Trainer konfigürasyonundaki ödül sabitleri
    REWARD_ATE_FOOD = 50
    REWARD_ATE_SPECIAL_FOOD = 100
    REWARD_HIT_WALL = -50
    REWARD_HIT_SNAKE = -50
    REWARD_GAME_OVER = -50
    REWARD_GETTING_CLOSER = 1
    REWARD_GETTING_FARTHER = -2
    REWARD_LENGTH_LIMIT_FOR_PENALTY = 10

    renderer.update_game_state(game.get_state())

    while running:
        delta_time = pg.time.get_ticks() - last_frame
        events = pg.event.get()

        for event in events:
            if event.type == pg.QUIT:
                running = False

        if delta_time > DELTA_TIME_LIMIT:
            last_frame = pg.time.get_ticks()

            # --- YAPAY ZEKA DÜŞÜNÜYOR ---
            state_for_training = game.get_state_for_training()
            state_tensor = torch.tensor(state_for_training, dtype=torch.float32).unsqueeze(0).to(device)
            
            with torch.no_grad():
                q_values = model(state_tensor)
                action = torch.argmax(q_values).item()

            if game.direction == Direction.UP:
                directions = [Direction.UP, Direction.RIGHT, Direction.LEFT]
            elif game.direction == Direction.RIGHT:
                directions = [Direction.RIGHT, Direction.DOWN, Direction.UP]
            elif game.direction == Direction.DOWN:
                directions = [Direction.DOWN, Direction.LEFT, Direction.RIGHT]
            elif game.direction == Direction.LEFT:
                directions = [Direction.LEFT, Direction.UP, Direction.DOWN]

            new_direction = directions[action]
            game.turn(new_direction)

            # --- MESAFA HESABI VE ADIM İLERLEMESİ ---
            current_state = game.get_state()
            head_x, head_y = current_state.snake[-1]
            food_x, food_y = current_state.food_position
            old_distance = abs(head_x - food_x) + abs(head_y - food_y)

            # Oyunu 1 adım ilerlet ve aksiyonu al
            game_action = game.step()

            new_state = game.get_state()
            is_gameover = new_state.is_gameover
            step_reward = 0.0

            # --- TRAINER İLE BİREBİR REWARD HESABI ---
            if game_action == Action.MOVE_ONLY:
                new_head_x, new_head_y = new_state.snake[-1]
                new_distance = abs(new_head_x - food_x) + abs(new_head_y - food_y)

                if new_distance < old_distance:
                    step_reward = REWARD_GETTING_CLOSER
                else:
                    if len(game.snake) > REWARD_LENGTH_LIMIT_FOR_PENALTY:
                        step_reward = 0
                    else:
                        step_reward = REWARD_GETTING_FARTHER
                
                steps_without_food += 1

            elif game_action == Action.ATE_FOOD:
                step_reward = REWARD_ATE_FOOD
                steps_without_food = 0
            elif game_action == Action.ATE_SPECIAL_FOOD:
                step_reward = REWARD_ATE_SPECIAL_FOOD
                steps_without_food = 0
            elif game_action == Action.HIT_SNAKE:
                step_reward = REWARD_HIT_SNAKE
                steps_without_food = 0
            elif game_action == Action.HIT_WALL:
                step_reward = REWARD_HIT_WALL
                steps_without_food = 0

            # Açlık Sınırı (Timeout) Kontrolü
            timeout_limit = (GRID_COUNT * 2) + (len(game.snake) * 10)
            is_timeout = steps_without_food > timeout_limit

            if is_timeout:
                is_gameover = True
                step_reward = REWARD_GAME_OVER
                steps_without_food = 0

            current_step_reward = step_reward
            total_episode_reward += step_reward

            # --- LOG KAYDI ---
            act_char = action_chars[action]
            step_logs.append(f"K({head_x},{head_y})-E({food_x},{food_y})-H({act_char})")

            # --- OYUN BİTTİ KONTROLÜ ---
            if is_gameover:
                # 1. Tam ölüm karesini yakala
                kaza_koordinati = new_state.snake[-1]

                # 2. Ölüm sebebini detaylandır
                if is_timeout:
                    olum_sebebi = "Sonsuz Döngü / Açlık"
                elif game_action == Action.HIT_WALL:
                    olum_sebebi = f"Duvara Çarptı! Koordinat: {kaza_koordinati}"
                elif game_action == Action.HIT_SNAKE:
                    olum_sebebi = f"Kendi Gövdesine Çarptı! Koordinat: {kaza_koordinati}"
                else:
                    olum_sebebi = "Bilinmeyen Çarpışma"

                print(f"Oyun Bitti! Sebep: {olum_sebebi} | Skor: {game.score} | Toplam Ödül: {total_episode_reward}")

                # 3. Yılanın öldüğü o son kareyi ekrana çiz ve 0.5 saniye dondur (Görebilmen için!)
                renderer.update_game_state(new_state)
                renderer.render(delta_time)
                pg.display.update()
                pg.time.wait(500) 

                # 4. Dosyaya yazdır
                with open("ai_olum_logu.txt", "a", encoding="utf-8") as f:
                    f.write(f"SKOR: {game.score}\n")
                    f.write(f"TOPLAM REWARD: {total_episode_reward}\n")
                    f.write(f"ÖLÜM SEBEBİ: {olum_sebebi}\n")
                    f.write("SON 150 ADIM:\n")
                    f.write(" -> ".join(step_logs) + "\n\n")

                # 5. Sistemi yeni oyuna hazırla
                step_logs.clear()
                game.reset()
                current_score = 0
                steps_without_food = 0
                total_episode_reward = 0.0 
                
                renderer.update_game_state(game.get_state())
            else:
                renderer.update_game_state(new_state)

        # Çizim ve Ekran Güncellemesi
        renderer.render(delta_time)

        if current_step_reward > 0:
            step_color = (0, 255, 100)
        elif current_step_reward < 0:
            step_color = (255, 60, 60)
        else:
            step_color = (200, 200, 200)

        if total_episode_reward > 0:
            total_color = (0, 255, 100)
        elif total_episode_reward < 0:
            total_color = (255, 60, 60)
        else:
            total_color = (200, 200, 200)

        step_surface = font.render(f"Step Reward: {current_step_reward:+.1f}", True, step_color)
        total_surface = font.render(f"Total Reward: {total_episode_reward:+.1f}", True, total_color)
        
        screen.blit(step_surface, (10, 10))
        screen.blit(total_surface, (10, 40)) 

        pg.display.update()
        clock.tick(60)

if __name__ == "__main__":
    try:
        ai_game_loop()
    except Exception as e:
        print("\n\033[91m=========================================\033[0m")
        print(f"\033[91mKOD ÇÖKTÜ! HATA SEBEBİ:\033[0m\n{e}")
        print("\033[91m=========================================\033[0m")
        input("Pencereyi kapatmak için Enter'a bas...")