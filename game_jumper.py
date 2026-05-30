import pygame
import random
import sys
import os

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Constants
WIDTH = 400
HEIGHT = 600
FPS = 60
GRAVITY = 0.5
PLAYER_JUMP = -10
SCROLL_THRESH = 200

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
BLUE = (0, 0, 255)

class Player:
    def __init__(self):
        self.width = 40
        self.height = 40
        self.x = WIDTH // 2
        self.y = HEIGHT - 50
        self.vel_y = 0
        self.rect = pygame.Rect(self.x, self.y, self.width, self.height)
        
        # Load the cute cat image
        try:
            self.image = pygame.image.load(resource_path("cat.png")).convert()
            self.image.set_colorkey(WHITE)
            self.image = pygame.transform.scale(self.image, (self.width, self.height))
        except Exception as e:
            print("Could not load cat image:", e)
            self.image = pygame.Surface((self.width, self.height))
            self.image.fill(BLUE)
        
    def move(self):
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.x -= 5
        if keys[pygame.K_RIGHT]:
            self.x += 5
            
        # Screen wrap
        if self.x > WIDTH:
            self.x = -self.width
        elif self.x < -self.width:
            self.x = WIDTH
            
        # Gravity
        self.vel_y += GRAVITY
        self.y += self.vel_y
        
        self.rect.x = self.x
        self.rect.y = self.y
        
    def jump(self):
        self.vel_y = PLAYER_JUMP
        
    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class Platform:
    base_image = None
    
    def __init__(self, x, y, width=80, height=30, moving=False, index=0):
        self.rect = pygame.Rect(x, y, width, height)
        self.index = index
        self.visited = False
        self.moving = moving
        self.direction = 1 if random.random() > 0.5 else -1
        self.speed = random.randint(2, 4)
        
        if Platform.base_image is None:
            try:
                img = pygame.image.load(resource_path("grass.png")).convert()
                img.set_colorkey(WHITE)
                Platform.base_image = img
            except Exception as e:
                print("Could not load grass image:", e)
                Platform.base_image = pygame.Surface((1, 1))
                Platform.base_image.fill(GREEN)
                
        self.image = pygame.transform.scale(Platform.base_image, (width, height))
        
    def update(self):
        if self.moving:
            self.rect.x += self.speed * self.direction
            if self.rect.right > WIDTH or self.rect.left < 0:
                self.direction *= -1
        
    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

class Fish:
    base_image = None
    
    def __init__(self, x, y):
        self.width = 30
        self.height = 30
        self.rect = pygame.Rect(x, y, self.width, self.height)
        
        if Fish.base_image is None:
            try:
                img = pygame.image.load(resource_path("fish.png")).convert()
                img.set_colorkey(WHITE)
                Fish.base_image = img
            except Exception as e:
                print("Could not load fish image:", e)
                Fish.base_image = pygame.Surface((1, 1))
                Fish.base_image.fill(RED)
                
        self.image = pygame.transform.scale(Fish.base_image, (self.width, self.height))
        
    def draw(self, surface):
        surface.blit(self.image, (self.rect.x, self.rect.y))

def draw_text(surface, text, size, color, x, y):
    font = pygame.font.SysFont(None, size)
    img = font.render(text, True, color)
    surface.blit(img, (x, y))

def main(high_score=0):
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Jumper Game")
    clock = pygame.time.Clock()
    
    player = Player()
    platforms = []
    fishes = []
    
    platforms_generated = 0
    highest_visited_index = 0
    
    # Generate initial platforms
    start_plat = Platform(WIDTH // 2 - 40, HEIGHT - 20, 80, index=platforms_generated)
    start_plat.visited = True # Prevent scoring for the starting platform
    platforms.append(start_plat)
    platforms_generated += 1
    
    for i in range(1, 10):
        p_w = random.randint(70, 120)
        p_x = random.randint(0, WIDTH - p_w)
        p_y = HEIGHT - (i * 60)
        is_moving = (platforms_generated % 5 == 0)
        platforms.append(Platform(p_x, p_y, p_w, moving=is_moving, index=platforms_generated))
        
        # 18.5% chance to spawn a fish on a non-moving platform
        if random.random() < 0.185 and not is_moving:
            fishes.append(Fish(p_x + p_w//2 - 15, p_y - 30))
            
        platforms_generated += 1
        
    score = 0
    game_over = False
    
    running = True
    while running:
        clock.tick(FPS)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # Allow restarting after game over
            if game_over and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    main(high_score) # Restart the game
                    return
                
        if not game_over:
            player.move()
            for plat in platforms:
                plat.update()
            
            # Collision with platforms (only when falling)
            if player.vel_y > 0:
                for plat in platforms:
                    if player.rect.colliderect(plat.rect):
                        # Ensure player is above the platform
                        if player.rect.bottom <= plat.rect.centery + 10:
                            player.y = plat.rect.top - player.height
                            player.vel_y = 0
                            player.jump()
                            if plat.index > highest_visited_index:
                                platforms_passed = plat.index - highest_visited_index
                                score += platforms_passed * 10
                                highest_visited_index = plat.index
                                
            # Collision with fishes
            for fish in fishes[:]:
                if player.rect.colliderect(fish.rect):
                    fishes.remove(fish)
                    player.vel_y = PLAYER_JUMP * 2
                            
            # Scroll platforms down
            if player.rect.top <= SCROLL_THRESH:
                player.y += abs(player.vel_y)
                player.rect.y = player.y
                for plat in platforms:
                    plat.rect.y += abs(player.vel_y)
                for fish in fishes:
                    fish.rect.y += abs(player.vel_y)
                
            # Remove off-screen platforms and generate new ones
            for plat in platforms[:]:
                if plat.rect.top > HEIGHT:
                    platforms.remove(plat)
                    
                    p_w = random.randint(70, 120)
                    p_x = random.randint(0, WIDTH - p_w)
                    p_y = random.randint(-40, -10)
                    is_moving = (platforms_generated % 5 == 0)
                    platforms.append(Platform(p_x, p_y, p_w, moving=is_moving, index=platforms_generated))
                    
                    if random.random() < 0.185 and not is_moving:
                        fishes.append(Fish(p_x + p_w//2 - 15, p_y - 30))
                        
                    platforms_generated += 1
                        
            # Remove off-screen fishes
            for fish in fishes[:]:
                if fish.rect.top > HEIGHT:
                    fishes.remove(fish)
                    
            # Game Over condition
            if player.rect.top > HEIGHT:
                game_over = True
                if score > high_score:
                    high_score = score
                
        # Draw everything
        screen.fill(WHITE)
        
        for plat in platforms:
            plat.draw(screen)
            
        for fish in fishes:
            fish.draw(screen)
            
        player.draw(screen)
        
        # Display score
        draw_text(screen, f"Score: {score}", 30, BLACK, 10, 10)
        draw_text(screen, f"High Score: {high_score}", 30, BLACK, WIDTH - 180, 10)
        
        if game_over:
            draw_text(screen, "GAME OVER", 60, RED, WIDTH // 2 - 120, HEIGHT // 2 - 30)
            draw_text(screen, "Press SPACE to restart", 30, BLACK, WIDTH // 2 - 110, HEIGHT // 2 + 30)
            
        pygame.display.flip()
        
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
