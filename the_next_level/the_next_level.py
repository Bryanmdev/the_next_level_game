# === SESSÃO 1: IMPORTAÇÕES E CONFIGURAÇÃO INICIAL ===
import pgzrun
import random

# Definição das constantes globais para a janela do jogo.
WIDTH = 800
HEIGHT = 600
TITLE = "The Next Level"

# === SESSÃO 2: CONFIGURAÇÃO DO MAPA E GERAÇÃO ===
TILE_SIZE = 16
MAP_WIDTH = WIDTH // TILE_SIZE
MAP_HEIGHT = HEIGHT // TILE_SIZE
MAX_LEVELS = 5

# === SESSÃO 3: ESTADO DO JOGO E OBJETOS GLOBAIS ===
game_state = 'main_menu' 
music_on = True
current_level = 0
player_lives = 5
is_door_open = False

# Listas que armazenarão os objetos ativos do jogo.
tiles = []
wall_tiles = []
player = None
enemies = []
potions = []
door = None
attack_hitbox = None

# Assets visuais para a interface do utilizador.
menu_background = Actor("menu_background")
start_button = Actor("button_start", (WIDTH / 2, 250))
music_button = Actor("button_music_on", (WIDTH - 50, 50)) 
exit_button = Actor("button_exit", (WIDTH / 2, 350)) 

# Constantes de balanceamento da jogabilidade.
ANIMATION_SPEED = 0.15
ATTACK_COOLDOWN = 0.4

# === SESSÃO 4: CLASSES DOS PERSONAGENS ===

class Player:
    """Representa o herói controlado pelo utilizador."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 2
        self.state = 'idle'
        self.direction = 'down'
        
        self.animations = {
            'idle': ["player_idle_1", "player_idle_2"],
            'walk': ["player_walk_1", "player_walk_2"],
            'attack': ["player_attack_1", "player_attack_2"]
        }
        self.animations_left = {
            'idle': ["player_idle_left_1", "player_idle_left_2"],
            'walk': ["player_walk_left_1", "player_walk_left_2"],
            'attack': ["player_attack_left_1", "player_attack_left_2"]
        }
        self.current_frame = 0
        self.anim_timer = 0
        self.actor = Actor(self.animations['idle'][0], (self.x, self.y))
        
        self.invincible_timer = 0
        self.attack_cooldown_timer = 0
        self.attack_anim_timer = 0

    def move(self, dx, dy):
        """Processa o movimento e a colisão com as paredes."""
        if self.state == 'attack': 
            return

        if dx > 0: 
            self.direction = 'right'
        elif dx < 0: 
            self.direction = 'left'
        elif dy < 0 and self.direction not in ['left', 'right']: 
            self.direction = 'up'
        elif dy > 0 and self.direction not in ['left', 'right']: 
            self.direction = 'down'

        # Verificação de colisão no eixo X
        self.x += dx
        self.actor.x = self.x
        for wall in wall_tiles:
            if self.actor.colliderect(wall): 
                self.x -= dx
                break
        
        # Verificação de colisão no eixo Y
        self.y += dy
        self.actor.y = self.y
        for wall in wall_tiles:
            if self.actor.colliderect(wall): 
                self.y -= dy
                break
        
        self.actor.pos = self.x, self.y

    def attack(self):
        """Inicia a ação de ataque."""
        global attack_hitbox
        if self.attack_cooldown_timer <= 0:
            self.state = 'attack'
            self.current_frame = 0
            self.attack_cooldown_timer = ATTACK_COOLDOWN
            self.attack_anim_timer = ANIMATION_SPEED * 2
            sounds.hit.play()

            # Criar hitbox do ataque
            px, py = int(self.actor.centerx), int(self.actor.centery)
            if self.direction == 'up': 
                topleft_x, topleft_y = px - TILE_SIZE // 2, py - TILE_SIZE - TILE_SIZE // 2
            elif self.direction == 'down': 
                topleft_x, topleft_y = px - TILE_SIZE // 2, py + TILE_SIZE // 2
            elif self.direction == 'left': 
                topleft_x, topleft_y = px - TILE_SIZE - TILE_SIZE // 2, py - TILE_SIZE // 2
            elif self.direction == 'right': 
                topleft_x, topleft_y = px + TILE_SIZE // 2, py - TILE_SIZE // 2
            
            attack_hitbox = Rect((topleft_x, topleft_y), (TILE_SIZE, TILE_SIZE))

    def take_damage(self, enemy):
        """Processa a perda de vida e o efeito de recuo."""
        global player_lives
        if self.invincible_timer > 0: 
            return

        player_lives -= 1
        self.invincible_timer = 1.0

        # Calcular recuo
        dx, dy = self.x - enemy.x, self.y - enemy.y
        norm_sq = dx**2 + dy**2
        if norm_sq > 0:
            norm = norm_sq**0.5
            knock_dx, knock_dy = (dx / norm) * 4, (dy / norm) * 4
            self.move(knock_dx, knock_dy)

    def update(self, dt):
        """Lógica principal do jogador."""
        if self.invincible_timer > 0: 
            self.invincible_timer -= dt
        if self.attack_cooldown_timer > 0: 
            self.attack_cooldown_timer -= dt
        
        if self.state == 'attack':
            self.attack_anim_timer -= dt
            if self.attack_anim_timer <= 0: 
                self.state = 'idle'
            self.animate(dt)
            return

        if keyboard.space:
            self.attack()
            self.animate(dt)
            return

        # Movimento com WASD
        dx, dy = 0, 0
        if keyboard.a: 
            dx = -self.speed
        elif keyboard.d: 
            dx = self.speed
        elif keyboard.w: 
            dy = -self.speed
        elif keyboard.s: 
            dy = self.speed

        self.state = 'walk' if (dx != 0 or dy != 0) else 'idle'
        if self.state == 'walk': 
            self.move(dx, dy)
            
        self.animate(dt)

    def animate(self, dt):
        """Gere a troca de frames das animações."""
        self.anim_timer += dt
        if self.anim_timer < ANIMATION_SPEED: 
            return
        self.anim_timer = 0
        
        anim_dict = self.animations_left if self.direction == 'left' else self.animations
        current_sequence = anim_dict.get(self.state, anim_dict['idle'])
        self.current_frame = (self.current_frame + 1) % len(current_sequence)
        self.actor.image = current_sequence[self.current_frame]

    def draw(self):
        """Desenha o jogador com efeito de piscar se invencível."""
        if self.invincible_timer > 0 and int(self.invincible_timer * 10) % 2 == 0:
            return
        self.actor.draw()

class Enemy:
    """Classe base para todos os inimigos."""
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.speed = 1
        self.health = 1
        self.state = 'patrolling'
        self.vision_range = 150
        self.direction_str = 'right'
        
        self.animations = {'walk': ["enemy_walk_1", "enemy_walk_2"]}
        self.animations_left = {'walk': ["enemy_walk_left_1", "enemy_walk_left_2"]}
        
        self.current_frame, self.anim_timer = 0, 0
        self.actor = Actor(self.animations['walk'][0], (self.x, self.y))
        
        self.patrol_timer = random.uniform(1, 3)
        self.direction_vector = (0, 0)

    def take_damage(self, attacker):
        """Reduz a vida do inimigo e aplica recuo."""
        self.health -= 1
        dx, dy = self.x - attacker.x, self.y - attacker.y
        norm_sq = dx**2 + dy**2
        if norm_sq > 0:
            norm = norm_sq**0.5
            knock_dx, knock_dy = (dx / norm) * 8, (dy / norm) * 8
            self.move(knock_dx, knock_dy)

    def move(self, dx, dy):
        """Processa o movimento e a colisão com as paredes."""
        self.x += dx
        self.actor.x = self.x
        for wall in wall_tiles:
            if self.actor.colliderect(wall): 
                self.x -= dx
                break
        
        self.y += dy
        self.actor.y = self.y
        for wall in wall_tiles:
            if self.actor.colliderect(wall): 
                self.y -= dy
                break
        self.actor.pos = self.x, self.y

    def update(self, dt):
        """Implementa a IA do inimigo."""
        dx_player, dy_player = self.x - player.actor.x, self.y - player.actor.y
        dist_sq_to_player = dx_player**2 + dy_player**2

        self.state = 'chasing' if dist_sq_to_player < self.vision_range**2 else 'patrolling'

        if self.state == 'patrolling':
            self.patrol_timer -= dt
            if self.patrol_timer <= 0:
                self.patrol_timer = random.uniform(2, 5)
                self.direction_vector = random.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
        else:  # Chasing
            dx, dy = player.actor.x - self.x, player.actor.y - self.y
            norm_sq = dx**2 + dy**2
            if norm_sq > 0:
                norm = norm_sq**0.5
                self.direction_vector = (dx / norm, dy / norm)
            else:
                self.direction_vector = (0, 0)

        dx, dy = self.direction_vector[0] * self.speed, self.direction_vector[1] * self.speed
        if dx > 0: 
            self.direction_str = 'right'
        elif dx < 0: 
            self.direction_str = 'left'

        self.move(dx, dy)
        self.animate(dt)

    def animate(self, dt):
        """Gere a troca de frames da animação."""
        self.anim_timer += dt
        if self.anim_timer > ANIMATION_SPEED:
            self.anim_timer = 0
            anim_dict = self.animations_left if self.direction_str == 'left' else self.animations
            anim_sequence = anim_dict['walk']
            self.current_frame = (self.current_frame + 1) % len(anim_sequence)
            self.actor.image = anim_sequence[self.current_frame]

    def draw(self): 
        self.actor.draw()

class Ghost(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 1.5
        self.health = 1
        self.animations = {'walk': ["ghost_walk_1", "ghost_walk_2"]}
        self.animations_left = {'walk': ["ghost_walk_left_1", "ghost_walk_left_2"]}
        self.actor.image = self.animations['walk'][0]

class Cyclops(Enemy):
    def __init__(self, x, y):
        super().__init__(x, y)
        self.speed = 0.5
        self.health = 3
        self.animations = {'walk': ["cyclops_walk_1", "cyclops_walk_2"]}
        self.animations_left = {'walk': ["cyclops_walk_left_1", "cyclops_walk_left_2"]}
        self.actor.image = self.animations['walk'][0]

# === SESSÃO 5: FUNÇÕES DE GERAÇÃO E CONFIGURAÇÃO DE NÍVEL ===

def generate_random_map():
    """Gera um mapa proceduralmente."""
    grid = [['#' for _ in range(MAP_WIDTH)] for _ in range(MAP_HEIGHT)]
    rooms = []
    
    for _ in range(random.randint(5, 8)):
        w, h = random.randint(6, 12), random.randint(5, 10)
        x, y = random.randint(1, MAP_WIDTH - w - 1), random.randint(1, MAP_HEIGHT - h - 1)
        new_room = Rect((x, y), (w, h))
        
        if not any(new_room.colliderect(other) for other in rooms):
            for i in range(new_room.top, new_room.bottom):
                for j in range(new_room.left, new_room.right):
                    grid[i][j] = '.'
            rooms.append(new_room)

    # Conectar salas com corredores
    for i in range(len(rooms) - 1):
        cx1, cy1 = rooms[i].center
        cx2, cy2 = rooms[i+1].center
        
        for x in range(min(cx1, cx2), max(cx1, cx2) + 1):
            if cy1 - 1 >= 0: 
                grid[cy1-1][x] = '.'
            grid[cy1][x] = '.'
            if cy1 + 1 < MAP_HEIGHT: 
                grid[cy1+1][x] = '.'
        for y in range(min(cy1, cy2), max(cy1, cy2) + 1):
            if cx2 - 1 >= 0: 
                grid[y][cx2-1] = '.'
            grid[y][cx2] = '.'
            if cx2 + 1 < MAP_WIDTH: 
                grid[y][cx2+1] = '.'
            
    # Adicionar paredes decorativas
    for r in range(MAP_HEIGHT):
        for c in range(MAP_WIDTH):
            if grid[r][c] == '#' and random.random() < 0.2:
                grid[r][c] = 'X'

    # Adicionar porta na última sala
    if rooms:
        last_room = rooms[-1]
        grid[last_room.centery][last_room.centerx] = 'D'

    return ["".join(row) for row in grid]

def setup_level(level_map):
    """Constrói a geometria do nível."""
    global tiles, wall_tiles, door
    tiles, wall_tiles, door = [], [], None
    
    for row_index, row in enumerate(level_map):
        for col_index, char in enumerate(row):
            x, y = col_index * TILE_SIZE, row_index * TILE_SIZE
            tile_image, is_wall = None, False
            
            if char == '.': 
                tile_image = "floor"
            elif char == '#': 
                tile_image, is_wall = "wall", True
            elif char == 'X': 
                tile_image, is_wall = "wall_2", True
            elif char == 'D':
                tile_image = "closed_door"
                door = Actor(tile_image, anchor=('left', 'top'), pos=(x, y))
            
            if tile_image and char != 'D':
                tile = Actor(tile_image, anchor=('left', 'top'), pos=(x, y))
                tiles.append(tile)
                if is_wall: 
                    wall_tiles.append(tile)
    
    if door: 
        tiles.append(door)

def find_valid_spawn_points(level_map):
    """Encontra pontos válidos para spawn de entidades."""
    points = []
    for r, row in enumerate(level_map):
        for c, char in enumerate(row):
            if char == '.':
                points.append((c * TILE_SIZE + TILE_SIZE/2, r * TILE_SIZE + TILE_SIZE/2))
    return points

def open_the_door():
    """Abre a porta quando todos os inimigos são derrotados."""
    global is_door_open
    if door:
        door.image = "door"
        is_door_open = True

def next_level():
    """Prepara o próximo nível."""
    global current_level, game_state, player, enemies, potions, is_door_open
    
    current_level += 1
    if current_level > MAX_LEVELS:
        game_state = 'victory'
        music.stop()
        return

    is_door_open = False
    level_map = generate_random_map()
    setup_level(level_map)
    
    spawn_points = find_valid_spawn_points(level_map)
    
    # Spawn do jogador
    player_pos = random.choice(spawn_points)
    player = Player(player_pos[0], player_pos[1])
    spawn_points.remove(player_pos)
    
    # Spawn dos inimigos
    enemies = []
    for _ in range(current_level + 2):
        if not spawn_points: 
            break
        enemy_pos = random.choice(spawn_points)
        spawn_points.remove(enemy_pos)
        enemy_type = random.choices([Enemy, Ghost, Cyclops], weights=[10, 5, 2 + current_level], k=1)[0]
        enemies.append(enemy_type(enemy_pos[0], enemy_pos[1]))
        
    # Spawn da poção
    potions = []
    if spawn_points:
        potion_pos = random.choice(spawn_points)
        spawn_points.remove(potion_pos)
        potions.append(Actor("red_potion", pos=potion_pos))

# === SESSÃO 6: FUNÇÕES PRINCIPAIS DO PYGAME ZERO ===

def draw():
    """Função principal de desenho."""
    screen.clear()
    
    if game_state == 'main_menu':
        menu_background.draw()
        screen.draw.text("The Next Level", center=(WIDTH / 2, 100), fontsize=60, color="orange", owidth=1.5, ocolor="black")
        start_button.draw()
        music_button.draw()
        exit_button.draw()
        
    elif game_state == 'story_intro':
        menu_background.draw()
        
        # Instruções de controle
        controls_y = 50
        screen.draw.text("Controles:", center=(WIDTH / 2, controls_y), fontsize=25, color="yellow", owidth=1, ocolor="black")
        screen.draw.text("WASD - Mover", center=(WIDTH / 2, controls_y + 30), fontsize=20, color="white", owidth=1, ocolor="black")
        screen.draw.text("Espaço - Atacar", center=(WIDTH / 2, controls_y + 55), fontsize=20, color="white", owidth=1, ocolor="black")
        
        # História
        story_text = [
            "A princesa do reino adoeceu gravemente.", "A única esperança é um antídoto raro,",
            "encontrado nas profundezas da Masmorra dos Campeões.", "",
            "Como o herói mais corajoso do reino,", "você desceu até ao nível mais baixo e encontrou a cura.",
            "", "Agora, a tarefa mais difícil começa:",
            "sobreviver, derrotar todos os inimigos de cada andar", "e voltar à superfície com o antídoto."
        ]
        
        y_pos = controls_y + 100
        for line in story_text:
            screen.draw.text(line, center=(WIDTH / 2, y_pos), fontsize=30, color="white", owidth=1.5, ocolor="black")
            y_pos += 40
        
        screen.draw.text("Clique para continuar...", center=(WIDTH / 2, HEIGHT - 50), fontsize=25, color="yellow", owidth=1, ocolor="black")

    elif game_state == 'playing':
        for tile in tiles: 
            tile.draw()
        for potion in potions: 
            potion.draw()
        player.draw()
        for enemy in enemies: 
            enemy.draw()
        screen.draw.text(f"Vidas: {player_lives}", topleft=(10, 10), color="white", owidth=1, ocolor="black")
        screen.draw.text(f"Nível: {current_level}", topright=(WIDTH - 10, 10), color="white", owidth=1, ocolor="black")
        
    elif game_state in ['game_over', 'victory']:
        for tile in tiles: 
            tile.draw()
        msg, color = ("Game Over", "red") if game_state == 'game_over' else ("Você Venceu!", "green")
        screen.draw.text(msg, center=(WIDTH / 2, HEIGHT / 2), fontsize=80, color=color, owidth=1.5, ocolor="black")
        screen.draw.text("Pressione ESC para voltar ao menu", center=(WIDTH / 2, HEIGHT / 2 + 50), fontsize=30, owidth=1.5, ocolor="black")

def update(dt):
    """Função principal de lógica."""
    global game_state, player_lives, attack_hitbox
    if game_state != 'playing': 
        return

    player.update(dt)
    
    # Atualizar inimigos e verificar colisões
    for enemy in enemies[:]:
        enemy.update(dt)
        if player.actor.colliderect(enemy.actor):
            player.take_damage(enemy)
            if player_lives <= 0:
                game_state = 'game_over'
                music.stop()
            break

    # Processar ataques
    if attack_hitbox:
        for enemy in enemies[:]:
            if attack_hitbox.colliderect(enemy.actor._rect):
                enemy.take_damage(player)
                if enemy.health <= 0: 
                    enemies.remove(enemy)
        attack_hitbox = None
        
        if not enemies and not is_door_open:
            open_the_door()
    
    # Coletar poções
    for potion in potions[:]:
        if player.actor.colliderect(potion):
            if player_lives < 5: 
                player_lives += 1
            potions.remove(potion)
    
    # Verificar se chegou à porta
    if is_door_open and door and player.actor.colliderect(door):
        next_level()

# === SESSÃO 7: FUNÇÕES DE CONTROLE ===

def on_mouse_down(pos):
    """Lida com eventos de clique do mouse."""
    global game_state, music_on, current_level, player_lives
    
    if game_state == 'main_menu':
        if start_button.collidepoint(pos):
            game_state = 'story_intro'
        elif music_button.collidepoint(pos):
            music_on = not music_on
            music_button.image = "button_music_on" if music_on else "button_music_off"
        elif exit_button.collidepoint(pos):
            quit()
            
    elif game_state == 'story_intro':
        game_state = 'playing'
        current_level = 0
        player_lives = 5
        next_level()
        if music_on: 
            music.play("background_music")

def on_key_down(key):
    """Lida com eventos de teclas."""
    global game_state
    if key == keys.ESCAPE and game_state in ['game_over', 'victory']:
        game_state = 'main_menu'

# === SESSÃO 8: INICIALIZAÇÃO DO JOGO ===
pgzrun.go()