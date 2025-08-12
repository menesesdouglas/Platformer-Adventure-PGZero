import pgzrun
from pygame import Rect

# --- Configurações da janela ---
WIDTH = 800
HEIGHT = 600
TITLE = "Platformer Adventure"
FONT_COLOR = (255, 255, 255)

# --- Estados do jogo ---
STATE_MENU = "menu"
STATE_PLAYING = "playing"
STATE_GAME_OVER = "game_over"
STATE_VICTORY = "victory"

game_state = STATE_MENU
game_over_sound_played = False

# Controle de música e som
music_on = True
sound_on = True

# --- Classe para botões do menu e telas ---
class Button:
    def __init__(self, text, center, action):
        self.text = text
        self.rect = Rect(0, 0, 200, 50)
        self.rect.center = center
        self.action = action

    def draw(self):
        screen.draw.filled_rect(self.rect, (50, 50, 50))
        screen.draw.text(self.text, center=self.rect.center, fontsize=32, color=FONT_COLOR)

    def click(self):
        self.action()

# --- Função para reiniciar o jogo ---
def reset_game():
    global player, enemies, game_over_sound_played, game_state
    player.__init__(100, HEIGHT - 100)
    enemies.clear()
    for plat in platforms[3:6]:
        enemies.append(Enemy(plat, ['slime_walk01', 'slime_walk02'], ['slime_walk01_right', 'slime_walk02_right'], speed=2))
    game_over_sound_played = False
    game_state = STATE_MENU
    sounds.game_over.stop()
    sounds.victory.stop()
    music.stop()

# Inicia o jogo, trocando estado e tocando música se ativo
def start_game():
    reset_game()
    global game_state
    game_state = STATE_PLAYING
    if music_on:
        music.play('bg_sound')

# Liga/desliga música e som
def toggle_music():
    global music_on, sound_on
    music_on = not music_on
    sound_on = not sound_on
    if music_on and game_state == STATE_PLAYING:
        music.play('bg_sound')
    else:
        music.stop()

# Sai do jogo
def quit_game():
    exit()

# Botões do menu principal
buttons = [
    Button("Start Game", (WIDTH // 2, HEIGHT // 2 - 60), start_game),
    Button("Sound On/Off", (WIDTH // 2, HEIGHT // 2), toggle_music),
    Button("Exit", (WIDTH // 2, HEIGHT // 2 + 60), quit_game)
]

# Botão para voltar ao menu a partir de Game Over ou Vitória
def back_to_menu():
    reset_game()

game_over_buttons = [Button("Back to Menu", (WIDTH // 2, HEIGHT // 2 + 80), back_to_menu)]
victory_buttons = [Button("Back to Menu", (WIDTH // 2, HEIGHT // 2 + 80), back_to_menu)]

# --- Flag animada para indicar fim do nível ---
class Flag:
    def __init__(self, x, y, frames, fps=6):
        self.frames = frames
        self.frame_index = 0
        self.actor = Actor(frames[0], (x, y))
        self.timer = 0
        self.frame_delay = 60 // fps 

    def update(self):
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.actor.image = self.frames[self.frame_index]
            self.timer = 0

    def draw(self):
        self.actor.draw()

flag = Flag(530, HEIGHT - 503, ['flag_01', 'flag_02'])

# --- Plataforma básica ---
class Platform:
    def __init__(self, x, y, image):
        self.actor = Actor(image, (x, y))

    def draw(self):
        self.actor.draw()

platforms = []

# Cria plataformas e obstáculos do cenário
def create_ground():
    platforms.extend([
        Platform(192, HEIGHT - 24, 'ground_01'),
        Platform(456, HEIGHT - 24, 'spike'),
        Platform(672, HEIGHT - 24, 'ground_02'),
        Platform(250, HEIGHT - 150, 'platform_01'),
        Platform(220, HEIGHT - 360, 'platform_01'),
        Platform(510, HEIGHT - 260, 'platform_02'),
        Platform(530, HEIGHT - 455, 'platform_03')
    ])

create_ground()

# --- Inimigos que andam nas plataformas ---
class Enemy:
    def __init__(self, platform, img_left, img_right, speed=1,
                 flat_left='slime_flat', flat_right='slime_flat_right'):
        self.actor = Actor(img_left[0])
        enemy_h = self.actor.height
        self.platform = platform
        self.actor.x = platform.actor.x
        # Posição Y ajustada para ficar sobre a plataforma
        self.actor.y = platform.actor.y - platform.actor.height / 2 - enemy_h / 2 + 5

        self.walk_frames = img_left
        self.walk_right_frames = img_right
        self.flat_left_image = flat_left
        self.flat_right_image = flat_right

        self.walk_index = 0
        self.walk_timer = 0
        self.facing_left = True
        self.speed = speed

        half_width = platform.actor.width // 2
        self.left_limit = platform.actor.x - half_width + 10
        self.right_limit = platform.actor.x + half_width - 10

        self.dead = False
        self.dead_timer = 0

    def update(self):
        if self.dead:
            self.dead_timer -= 1
            if self.dead_timer <= 0:
                enemies.remove(self)
            return

        # Movimento horizontal
        self.actor.x += -self.speed if self.facing_left else self.speed

        if self.actor.x <= self.left_limit:
            self.facing_left = False
        elif self.actor.x >= self.right_limit:
            self.facing_left = True

        # Animação andando
        self.walk_timer += 1
        if self.walk_timer >= 12:
            self.walk_index = (self.walk_index + 1) % len(self.walk_frames)
            self.walk_timer = 0

        self.actor.image = (self.walk_frames[self.walk_index] if self.facing_left else self.walk_right_frames[self.walk_index])

    def stomp(self):
        # Inimigo morto após stomp do player
        self.dead = True
        self.dead_timer = 30
        if sound_on:
            sounds.hit.play()
        self.actor.image = self.flat_left_image if self.facing_left else self.flat_right_image

    def draw(self):
        self.actor.draw()

enemies = []
for plat in platforms[3:6]:
    enemies.append(Enemy(plat, ['slime_walk01', 'slime_walk02'], ['slime_walk01_right', 'slime_walk02_right'], speed=2))

# --- Player ---
class Player:
    def __init__(self, x, y):
        self.actor = Actor('player_idle01', (x, y))
        self.vx = 0
        self.vy = 0
        self.on_ground = False
        self.life = 3
        self.knockback_timer = 0
        self.invulnerable_timer = 0

        self.idle_frames = ['player_idle01', 'player_idle02', 'player_idle03', 'player_idle02']
        self.run_frames = ['player_run01', 'player_run02']
        self.jump_frame = 'player_jump'
        self.hit_frame = 'player_hit'

        self.idle_left_frames = ['player_idle01_left', 'player_idle02_left', 'player_idle03_left', 'player_idle02_left']
        self.run_left_frames = ['player_run01_left', 'player_run02_left']
        self.jump_left_frame = 'player_jump_left'
        self.hit_left_frame = 'player_hit_left'

        self.idle_index = 0
        self.run_index = 0
        self.idle_timer = 0
        self.run_timer = 0

        self.facing_right = True

    def draw(self):
        self.actor.draw()

    def update(self):
        # Temporizadores para invulnerabilidade e knockback
        if self.invulnerable_timer > 0:
            self.invulnerable_timer -= 1

        if self.knockback_timer > 0:
            self.actor.x += self.vx
            self.actor.y += self.vy
            self.knockback_timer -= 1
            self.vy += 0.75
            return

        self.vx = 0
        moving = False

        # Movimento horizontal com teclado
        if keyboard.left or keyboard.a:
            self.vx = -5
            moving = True
            self.facing_right = False
        elif keyboard.right or keyboard.d:
            self.vx = 5
            moving = True
            self.facing_right = True

        self.actor.x += self.vx
        self.vy += 0.75  # gravidade

        # Movimento vertical fragmentado para detectar colisões com plataformas e spikes
        steps = int(abs(self.vy)) + 1
        step_y = self.vy / steps
        on_any_platform = False

        for _ in range(steps):
            self.actor.y += step_y
            for platform in platforms:
                if platform.actor.image == 'spike':
                    feet = Rect(self.actor.x - self.actor.width//4, self.actor.y + self.actor.height//2 - 8, self.actor.width//2, 8)
                    if platform.actor.colliderect(feet):
                        self.die()
                else:
                    feet = Rect(self.actor.x - self.actor.width//4, self.actor.y + self.actor.height//2, self.actor.width//2, 8)
                    top = Rect(platform.actor.x - platform.actor.width//2, platform.actor.y - platform.actor.height//2, platform.actor.width, 8)
                    if self.vy >= 0 and feet.colliderect(top) and self.actor.y < platform.actor.y:
                        # Corrige posição Y e zera velocidade vertical ao pousar
                        self.actor.y = platform.actor.y - platform.actor.height//2 - self.actor.height//2
                        self.vy = 0
                        on_any_platform = True
                        break
            if on_any_platform:
                break

        self.on_ground = on_any_platform

        # Restrições para não sair da tela
        if self.actor.left < 0:
            self.actor.left = 0
        if self.actor.right > WIDTH:
            self.actor.right = WIDTH
        if self.actor.top < 0:
            self.actor.top = 0
            self.vy = 0
        if self.actor.bottom > HEIGHT:
            self.actor.bottom = HEIGHT
            self.vy = 0

        # Atualiza animação conforme estado e direção
        if not self.on_ground:
            self.actor.image = self.jump_frame if self.facing_right else self.jump_left_frame
        elif moving:
            self.run_timer += 1
            if self.run_timer >= 8:
                self.run_index = (self.run_index + 1) % len(self.run_frames)
                self.run_timer = 0
            self.actor.image = self.run_frames[self.run_index] if self.facing_right else self.run_left_frames[self.run_index]
        else:
            self.idle_timer += 1
            if self.idle_timer >= 18:
                self.idle_index = (self.idle_index + 1) % len(self.idle_frames)
                self.idle_timer = 0
            self.actor.image = self.idle_frames[self.idle_index] if self.facing_right else self.idle_left_frames[self.idle_index]

        # Colisão com inimigos
        for enemy in enemies[:]:
            if self.actor.colliderect(enemy.actor) and not enemy.dead and self.invulnerable_timer <= 0:
                player_bottom = self.actor.y + self.actor.height / 2
                enemy_top = enemy.actor.y - enemy.actor.height / 2 + 5
                if self.vy > 0 and player_bottom <= enemy_top + 15:
                    enemy.stomp()
                    self.vy = -10
                    self.on_ground = False
                else:
                    self.take_damage()

    def jump(self):
        if self.on_ground:
            self.vy = -15
            self.on_ground = False
            if sound_on:
                sounds.jump.play()

    def take_damage(self):
        self.life -= 1
        if sound_on:
            sounds.hit.play()
        self.actor.image = self.hit_frame if self.facing_right else self.hit_left_frame
        self.vy = -8
        self.vx = -8 if self.facing_right else 8
        self.knockback_timer = 15
        self.invulnerable_timer = 30
        if self.life <= 0:
            self.die()

    def die(self):
        global game_state
        self.life = 0
        game_state = STATE_GAME_OVER

player = Player(100, HEIGHT - 100)

# --- Funções de desenho para cada estado ---
def draw_menu():
    screen.draw.text("PLATFORMER ADVENTURE", center=(WIDTH // 2, 150), fontsize=48, color=FONT_COLOR)
    for button in buttons:
        button.draw()

def draw_game():
    screen.blit('background', (0, 0))
    for platform in platforms:
        platform.draw()
    for enemy in enemies:
        enemy.draw()
    flag.draw()
    player.draw()
    screen.draw.text(f"Life: {player.life}", (20, 20), fontsize=32, color=(255, 0, 0))

def draw_game_over():
    screen.draw.text("GAME OVER", center=(WIDTH // 2, HEIGHT // 2), fontsize=64, color=FONT_COLOR)
    for button in game_over_buttons:
        button.draw()

def draw_victory():
    screen.draw.text("YOU WIN!", center=(WIDTH // 2, HEIGHT // 2), fontsize=64, color=FONT_COLOR)
    for button in victory_buttons:
        button.draw()

def draw():
    screen.clear()
    if game_state == STATE_MENU:
        draw_menu()
    elif game_state == STATE_PLAYING:
        draw_game()
    elif game_state == STATE_GAME_OVER:
        draw_game_over()
    elif game_state == STATE_VICTORY:
        draw_victory()

# --- Atualização do jogo por frame ---
def update():
    global game_over_sound_played, game_state
    if game_state == STATE_PLAYING:
        player.update()
        flag.update()
        for enemy in enemies:
            enemy.update()
        # Checa colisão com a flag para vitória
        if player.actor.colliderect(flag.actor):
            game_state = STATE_VICTORY
            music.stop()
            if sound_on:
                sounds.victory.play()
        game_over_sound_played = False
    elif game_state == STATE_GAME_OVER:
        # Toca som de game over uma vez
        if not game_over_sound_played:
            music.stop()
            if sound_on:
                sounds.game_over.play()
            game_over_sound_played = True

# --- Eventos de input ---
def on_mouse_down(pos):
    if game_state == STATE_MENU:
        for button in buttons:
            if button.rect.collidepoint(pos):
                button.click()
    elif game_state == STATE_GAME_OVER:
        for button in game_over_buttons:
            if button.rect.collidepoint(pos):
                button.click()
    elif game_state == STATE_VICTORY:
        for button in victory_buttons:
            if button.rect.collidepoint(pos):
                button.click()

def on_key_down(key):
    if key == keys.SPACE:
        player.jump()

# --- Configurações de volume ---
music.set_volume(0.3)
sounds.jump.set_volume(0.3)
sounds.hit.set_volume(0.3)
sounds.game_over.set_volume(0.3)
sounds.victory.set_volume(0.3)

pgzrun.go()
