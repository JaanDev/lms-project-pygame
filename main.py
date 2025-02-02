import pygame
from pygame import gfxdraw
import time
import math
import random
import pickle

# Размер окна
SCREEN_W = 1000
SCREEN_H = 1000

# константы для физики корабля
SHIP_ACCEL = 15
SHIP_SLOWDOWN = 12
SHIP_MAX_ACCEL = 3000
SHIP_MAX_ACCEL_GROWTH = 0.5
SHIP_REALLY_MAX_ACCEL = 5000
SHIP_CAMERA_OFFSET = (SCREEN_W // 2, SCREEN_H // 2)
SHIP_INVINCIBILITY_TIME = 1  # s
BULLET_SPEED = 500

# генерация звезд
STAR_MIN_COUNT = 75
STAR_MAX_COUNT = 175

# константы для метеоритов
METEOR_INV_TIME = 0.5

# режим отладки
IS_DBG_MODE = False


# конвертация игровой позиции в позицию экрана
def world_to_camera(p):
    return [p[0] - camera_pos[0], p[1] - camera_pos[1]]


# отрисовка плавного круга
def draw_aa_full_circle(p, color, radius):
    gfxdraw.aacircle(screen, int(p[0]), int(p[1]), radius, color)
    gfxdraw.filled_circle(screen, int(p[0]), int(p[1]), radius, color)


# угол между 2 точками
def angle_between(p1, p2):
    return -math.degrees(math.atan((p1[1] - p2[1]) / (p1[0] - p2[0]))) + (90 if p1[0] < p2[0] else -90)


# снаряд
class Bullet():
    def __init__(self, rot, pos):
        self.rot = -rot - 90
        self.tex = pygame.transform.rotate(pygame.transform.scale(pygame.image.load('bullet.png').convert_alpha(), (12, 24)), rot)
        self.pos = pos.copy()
        self.size = self.tex.get_rect()
        self.hitbox = pygame.Rect(self.pos[0] - self.size.w // 2, self.pos[1] - self.size.h // 2, self.size.w, self.size.h)
    
    def update(self, dt):
        self.pos[0] += BULLET_SPEED * dt * math.cos(math.radians(self.rot))
        self.pos[1] += BULLET_SPEED * dt * math.sin(math.radians(self.rot))

        self.hitbox = pygame.Rect(self.pos[0] - self.size.w // 2, self.pos[1] - self.size.h // 2, self.size.w, self.size.h)
    
    def draw(self):
        screen.blit(self.tex, world_to_camera((self.pos[0] - self.size.w // 2, self.pos[1] - self.size.h // 2)))


# корабль
class Ship(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()

        self.surfaces = [pygame.transform.scale(pygame.image.load(f'ship{i}.png'), (68, 80)) for i in range(1, 5)]
        self.fire_surfaces = [pygame.transform.scale(pygame.image.load(f'shipfire{i}.png'), (68, 80)) for i in range(1, 5)]
        self.anim_time = 0
        self.anim_frametime = 1 / 10
        self.cur_frame = 0

        self.pos = [400, 400]
        self.rot = 0
        self.accel = [0, 0]
        self.hasfire = False

        self.hitbox = self.surfaces[0].get_rect()

        self.invincibility_time = SHIP_INVINCIBILITY_TIME
        self.invincible = True

        self.lifes = 5

        self.points = 0

        self.bullets_left = 3
        self.bullets = []

    def update(self, dt):
        mouse_pos = list(pygame.mouse.get_pos())
        mouse_pos[0] += camera_pos[0]
        mouse_pos[1] += camera_pos[1]
        if mouse_pos[0] - self.pos[0] == 0:
            self.rot = 180 if mouse_pos[1] > self.pos[1] else 0
        else:
            # self.rot = -math.degrees(math.atan((mouse_pos[1] - self.pos[1]) / (mouse_pos[0] - self.pos[0]))) + (90 if mouse_pos[0] < self.pos[0] else -90)
            self.rot = angle_between(mouse_pos, self.pos)

        if self.invincibility_time < SHIP_INVINCIBILITY_TIME * 0.8:
            mouse_pressed_now = pygame.mouse.get_pressed(3)[0]
            self.hasfire = mouse_pressed_now
            if mouse_pressed_now:
                self.anim_frametime = 1 / 10
                self.accel[0] += SHIP_ACCEL * math.sin(math.radians(self.rot)) * dt
                self.accel[1] += SHIP_ACCEL * math.cos(math.radians(self.rot)) * dt
            else:
                self.anim_frametime = 1 / 5
                self.accel[0] *= 0.97
                self.accel[1] *= 0.97
        if abs(self.accel[0]) < 0.001:
            self.accel[0] = 0
        if abs(self.accel[1]) < 0.001:
            self.accel[1] = 0

        acx = abs(self.accel[0])
        acy = abs(self.accel[1])

        if acx > 20:
            acx = (acx / 20) ** 0.06 * 20
        else:
            acx **= 0.9
        if acy > 20:
            acy = (acy / 20) ** 0.06 * 20
        else:
            acy **= 0.9
        
        self.pos[0] -= acx * (-1 if self.accel[0] < 0 else 1)
        self.pos[1] -= acy * (-1 if self.accel[1] < 0 else 1)

        self.anim_time += dt
        if self.anim_time >= self.anim_frametime:
            self.anim_time -= self.anim_frametime
            self.cur_frame = (self.cur_frame + 1) % 4
        
        if self.invincibility_time > 0:
            self.invincibility_time -= dt
            self.invincible = True
        else:
            self.invincible = False
        
        j = 0
        while j < len(self.bullets):
            b = self.bullets[j]
            b.update(dt)
            coll = False
            for i in range(len(meteors)):
                if meteors[i].collide_rect(b.hitbox):
                    meteors.pop(i)
                    coll = True
                    break
            if coll:
                self.bullets.pop(j)
                continue
            j += 1

    def draw(self):
        rotsurf = pygame.transform.rotate(self.surfaces[self.cur_frame], self.rot)
        
        world_pos = (self.pos[0] - rotsurf.get_rect().w / 2, self.pos[1] - rotsurf.get_rect().h / 2)
        pos = world_to_camera(world_pos)
        self.hitbox = pygame.Rect(self.pos[0] - rotsurf.get_rect().w * 0.4, self.pos[1] - rotsurf.get_rect().h * 0.4, rotsurf.get_rect().w * 0.8, rotsurf.get_rect().h * 0.8)
        
        if self.invincible and self.invincibility_time > 0.6:
            if int(self.invincibility_time / 0.05) % 2 == 0:
                return

        if self.hasfire:
            firerotsurf = pygame.transform.rotate(self.fire_surfaces[self.cur_frame], self.rot)
            # firerotsurf.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
            screen.blit(firerotsurf, pos)
        screen.blit(rotsurf, pos)

        for b in self.bullets:
            b.draw()
        
        # text_surf = my_font.render(f'{self.accel}', False, (255, 255, 255))
        # screen.blit(text_surf, (0, 0))
        # pygame.draw.rect(screen, 'white', (10, 20, 200 * self.accel2 / 5000, 30))
        # pygame.draw.rect(screen, 'red', (10, 20, 200, 30), 1)
    
    def damage(self):
        self.invincibility_time = SHIP_INVINCIBILITY_TIME
        if not IS_DBG_MODE:
            self.lifes -= 1
    
    def shoot(self):
        if self.bullets_left > 0:
            if not IS_DBG_MODE:
                self.bullets_left -= 1
            self.bullets.append(Bullet(self.rot, self.pos))


# звёзды
class StarChunk():
    def __init__(self, chunk):
        self.textures = [pygame.transform.scale2x(pygame.image.load(f'star{i}.png')) for i in range(1, 4)]

        self.visible = False

        # self.rect = pygame.Rect(chunk[0] * SCREEN_W, chunk[1] * SCREEN_H, SCREEN_W, SCREEN_H)

        # self.color = (random.randint(0, 150), random.randint(0, 150), random.randint(0, 150))

        self.elements = [(random.randint(0, SCREEN_W) + chunk[0] * SCREEN_W, random.randint(0, SCREEN_H) + chunk[1] * SCREEN_H, random.randint(0, 2), random.randint(19, 20) / 100) for _ in range(random.randint(STAR_MIN_COUNT, STAR_MAX_COUNT))]
    
    def draw(self):
        for x, y, tex, parallax in self.elements:
            screen.blit(self.textures[tex], (x - camera_pos[0] * parallax, y - camera_pos[1] * parallax))
        # pygame.draw.line(screen, 'blue', (self.rect.x - camera_pos[0] * 0.2, self.rect.y - camera_pos[1] * 0.2), (self.rect.x + SCREEN_W - camera_pos[0] * 0.2, self.rect.y - camera_pos[1] * 0.2))
        # pygame.draw.line(screen, 'blue', (self.rect.x - camera_pos[0] * 0.2, self.rect.y + SCREEN_H - camera_pos[1] * 0.2), (self.rect.x + SCREEN_W - camera_pos[0] * 0.2, self.rect.y + SCREEN_H - camera_pos[1] * 0.2))
        # pygame.draw.line(screen, 'blue', (self.rect.x - camera_pos[0] * 0.2, self.rect.y - camera_pos[1] * 0.2), (self.rect.x - camera_pos[0] * 0.2, self.rect.y + SCREEN_H - camera_pos[1] * 0.2))
        # pygame.draw.line(screen, 'blue', (self.rect.x - camera_pos[0] * 0.2, self.rect.y + SCREEN_H - camera_pos[1] * 0.2), (self.rect.x - camera_pos[0] * 0.2, self.rect.y + SCREEN_H - camera_pos[1] * 0.2))


# звезда в уровне
class Star:
    def __init__(self, pos):
        self.sprites = [pygame.transform.scale2x(pygame.image.load(f'bigstar{i}.png')) for i in range(1, 9)]
        self.anim_frametime = 1 / 10
        self.anim_time = 0
        self.pos = pos
        self.hitbox = pygame.Rect(self.pos[0], self.pos[1], 64, 64)
    
    def update(self, dt):
        self.anim_time += dt
    
    def draw(self):
        screen.blit(self.sprites[int(self.anim_time / self.anim_frametime) % 8], world_to_camera(self.pos))


# уровень
class Level():
    def __init__(self, points, bounds, stars):
        self.bounds = bounds
        self.stars = [Star(x) for x in stars]

        mx, my = min(bounds, key=lambda x: x[0])[0], min(bounds, key=lambda x: x[1])[1]
        self.bounding_box = pygame.Rect(
            mx,
            my,
            max(bounds, key=lambda x: x[0])[0] - mx,
            max(bounds, key=lambda x: x[1])[1] - my
        )

        POINTS_SPACING = 50

        cnt = 0

        self.points = [[points[0], 0, True, pygame.Rect(points[0][0] - 10, points[0][1] - 10, 20, 20)]]

        self.middle_points = []
        for i in range(1, len(points)):
            p = points[i]
            prev_p = points[i - 1]

            diffx = p[0] - prev_p[0]
            diffy = p[1] - prev_p[1]
            diff = math.sqrt(diffx ** 2 + diffy ** 2)
            count = int(diff / POINTS_SPACING)
            new_spacing = diff / count

            for j in range(0, count):
                self.middle_points.append((prev_p[0] + diffx * (new_spacing * j / diff), prev_p[1] + diffy * (new_spacing * j / diff)))
            
            cnt += count
            self.points.append([p, cnt, False, pygame.Rect(p[0] - 10, p[1] - 10, 20, 20)])
        
    def update(self, dt):
        pass

    def draw(self):
        for i, p in enumerate(self.middle_points):
            is_active = list(filter(lambda x: x[1] > i, self.points))[0][2]
            radius = 4 if is_active else int(6 + math.sin(i * (2 * math.pi / 10) - game_time * 6) * 2)
            draw_aa_full_circle(world_to_camera(p), (168, 170, 255) if not is_active else (150, 150, 150), radius)

        for ii, (p, i, activated, _) in enumerate(self.points):
            radius = int((30 if ii == len(self.points) - 1 else 17) + math.sin(i * (2 * math.pi / 10) - game_time * 6) * 2) if not activated else 18
            col = (122, 73, 255) if not activated else (150, 150, 150)

            draw_aa_full_circle(world_to_camera(p), col, radius)
            gfxdraw.aacircle(screen, int(world_to_camera(p)[0]), int(world_to_camera(p)[1]), radius + 4, col)
            gfxdraw.aacircle(screen, int(world_to_camera(p)[0]), int(world_to_camera(p)[1]), radius + 5, col)

        pygame.draw.aalines(screen, 'red', True, list(map(lambda x: world_to_camera(x), self.bounds)))
        pygame.draw.aalines(screen, 'red', True, list(map(lambda x: world_to_camera(x), self.bounds)))

        for s in self.stars:
            s.draw()


# метеорит
class Meteor():
    def __init__(self, level):
        new_size = int(random.randint(50, 60) / 10 * 25)
        self.size = new_size
        self.sprite = pygame.transform.rotate(pygame.transform.scale(pygame.image.load('meteor.png'), (new_size, new_size)), random.randint(0, 360))
        self.rot = 0
        self.pos = [random.randint(level.bounding_box.x - 100, level.bounding_box.x + level.bounding_box.w + 100), random.randint(level.bounding_box.y - 100, level.bounding_box.y + level.bounding_box.h + 100)]
        level_center = (level.bounding_box.x + level.bounding_box.w // 2, level.bounding_box.y + level.bounding_box.h // 2)
        if self.pos[0] - level_center[0] == 0:
            angle = 90  # ??
        else:
            angle = math.degrees(math.atan((self.pos[1] - level_center[1]) / (self.pos[0] - level_center[0]))) + random.randint(-45, 45)
        accel_force = random.randint(100, 200) * (-1 if self.pos[0] > level_center[0] else 1)
        self.accel = [accel_force * math.cos(math.radians(angle)), accel_force * math.sin(math.radians(angle))]
        radius = new_size / 2 * 0.95
        self.points = [(radius * math.cos(math.radians(x)), radius * math.sin(math.radians(x))) for x in range(0, 360, 45)] + [(0, 0)]
        self.accel2 = (random.randint(-5, 5), random.randint(-5, 5))
        
        self.inv_time = 0
        self.inv = True
    
    def collide_rect(self, rect: pygame.Rect):
        if self.inv:
            return False
        for p in self.points:
            if rect.collidepoint((p[0] + self.pos[0], p[1] + self.pos[1])):
                return True
        return False
    
    def update(self, dt):
        if self.inv:
            self.inv_time += dt
            if self.inv_time >= METEOR_INV_TIME:
                self.inv = False
        self.accel[0] += self.accel2[0] * dt
        self.accel[1] += self.accel2[1] * dt
        self.pos[0] += self.accel[0] * dt
        self.pos[1] += self.accel[1] * dt

    def draw(self):
        if self.inv:
            if int(self.inv_time / 0.05) % 2 == 0:
                return
        screen.blit(self.sprite, world_to_camera((self.pos[0] - self.sprite.get_rect().w // 2, self.pos[1] - self.sprite.get_rect().h // 2)))
        # pygame.draw.line(screen, 'blue', world_to_camera((self.pos[0] - self.accel[0] * 1000, self.pos[1] - self.accel[1] * 1000)), world_to_camera((self.pos[0] + self.accel[0] * 1000, self.pos[1] + self.accel[1] * 1000)))
    

pygame.init()

# создание окна
screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

# шрифты
my_font = pygame.font.SysFont('Comic Sans MS', 22)
my_font2 = pygame.font.SysFont('Comic Sans MS', 40)
big_font = pygame.font.SysFont('Comic Sans MS', 72)

clock = pygame.time.Clock()

ship = Ship()

camera_pos = [0, 0]

stars = {}

with open('lvls.pkl', 'rb') as f:
    data = pickle.load(f)
    
    levels = [Level(x[0], x[1], x[2]) for x in data]

cur_level = 0
level = levels[0]

ship.pos = list(level.points[0][0])

game_time = 0

heart_tex = pygame.transform.scale2x(pygame.image.load('heart.png'))

last_frame_clipping = False
last_frame_clipping_m = False

meteors = [Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level)]

meteor_time = 1.5
cur_meteor_time = 0

won = False

is_start_window = True

running = True
while running:
    dt = clock.tick(100) / 1000

    game_time += dt

    # update

    if ship.lifes != 0 and not won and not is_start_window:
        cur_meteor_time += dt
        if cur_meteor_time >= meteor_time:
            meteors.append(Meteor(level))
            cur_meteor_time *= 0.9
            cur_meteor_time = 0
        
        is_clipping = False
        for m in meteors:
            m.update(dt)
            if m.collide_rect(ship.hitbox):
                is_clipping = True
                if not last_frame_clipping_m:
                    if not ship.invincible:
                        ship.damage()
                    ship.accel[0] *= -0.3
                    ship.accel[1] *= -0.3
                    if abs(ship.accel[0]) < 2:
                        ship.accel[0] = 2 if ship.accel[0] > 0 else -2
                    if abs(ship.accel[1]) < 2:
                        ship.accel[1] = 2 if ship.accel[1] > 0 else -2
                    last_frame_clipping_m = True
        if not is_clipping:
            last_frame_clipping_m = False
        
        ship.update(dt)

        is_clipping = False
        for i in range(1, len(level.bounds) + 1):
            i2 = i % len(level.bounds)
            if ship.hitbox.clipline(level.bounds[i2 - 1][0], level.bounds[i2 - 1][1], level.bounds[i2][0], level.bounds[i2][1]):
                is_clipping = True
                if not last_frame_clipping:
                    if not ship.invincible:
                        ship.damage()
                    ship.accel[0] *= -0.4
                    ship.accel[1] *= -0.4
                    if abs(ship.accel[0]) < 3:
                        ship.accel[0] = 3 if ship.accel[0] > 0 else -3
                    if abs(ship.accel[1]) < 3:
                        ship.accel[1] = 3 if ship.accel[1] > 0 else -3

                    last_frame_clipping = True
                break
        if not is_clipping:
            last_frame_clipping = False
        
        i = 0
        while i < len(level.stars):
            star = level.stars[i]
            if star.hitbox.colliderect(ship.hitbox):
                level.stars.pop(i)
                ship.points += 50
                continue
            i += 1
        
        for s in level.stars:
            s.update(dt)
        
        for i, p in enumerate(level.points):
            if i == 0:
                continue
            if p[3].colliderect(ship.hitbox) and not p[2] and level.points[i - 1][2]:
                level.points[i][2] = True
                ship.points += 10
                if i == len(level.points) - 1:
                    cur_level += 1
                    if cur_level == len(levels):
                        won = True
                    else:
                        level = levels[cur_level]
                        ship.lifes = 5
                        meteors = [Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level), Meteor(level)]
                        ship.accel = [0, 0]
                        ship.pos = list(level.points[0][0])
                        game_time = 0
                        last_frame_clipping = False
                        last_frame_clipping_m = False
                        meteor_time = 1.2
                        cur_meteor_time = 0
                        ship.bullets_left = 3
                        ship.invincibility_time = SHIP_INVINCIBILITY_TIME
                        ship.invincible = True
    if is_start_window:
        pass

    camera_pos = [ship.pos[0] - SHIP_CAMERA_OFFSET[0], ship.pos[1] - SHIP_CAMERA_OFFSET[1]]

    for x in range(2):
        for y in range(2):
            chunk = (int(((camera_pos[0] * 0.2 + SCREEN_W * x)) // SCREEN_W), int((camera_pos[1] * 0.2 + SCREEN_H * y) // SCREEN_H))
            if chunk not in stars.keys():
                stars[chunk] = StarChunk(chunk)
            stars[chunk].visible = True

    # draw

    screen.fill((2, 2, 5))

    for s in stars.values():
        if s.visible:
            s.draw()
            s.visible = False
    
    if is_start_window:
        text_surf = big_font.render('Asteroids', False, (255, 255, 255))
        screen.blit(text_surf, (320, 100))

        btn_rect = pygame.Rect(200, 300, 600, 70)
        pygame.draw.rect(screen, (96, 157, 255) if btn_rect.collidepoint(pygame.mouse.get_pos()) else (37, 99, 198), btn_rect)
        text_surf = my_font2.render('Играть', False, (255, 255, 255))
        screen.blit(text_surf, (420, 300))
    else:
        if ship.lifes == 0:
            text_surf = big_font.render('You lost', False, (255, 255, 255))
            screen.blit(text_surf, (350, 400))
        elif won:
            text_surf = big_font.render(f'You won. Score: {ship.points}', False, (255, 255, 255))
            screen.blit(text_surf, (150, 400))
        else:
            level.draw()
            
            ship.draw()

            for m in meteors:
                m.draw()

            if IS_DBG_MODE:
                pygame.draw.rect(screen, 'red', (ship.hitbox.x - camera_pos[0], ship.hitbox.y - camera_pos[1], ship.hitbox.w, ship.hitbox.h), 1)
                text_surf = my_font.render(f'{int(pygame.mouse.get_pos()[0] + camera_pos[0])}, {int(pygame.mouse.get_pos()[1] + camera_pos[1])}', False, (255, 255, 255))
                screen.blit(text_surf, (0, 60))
            
            text_surf = my_font.render(f'{ship.bullets_left}', False, (255, 255, 255))
            screen.blit(text_surf, (5, 60))

            for i in range(ship.lifes):
                screen.blit(heart_tex, (5 + 33 * i, 5))
            
            text_surf = my_font.render(f'{ship.points} очков', False, (255, 255, 255))
            screen.blit(text_surf, (5, 30))

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
            elif event.key == pygame.K_SPACE:
                ship.shoot()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3 and IS_DBG_MODE:
                print(f'({int(pygame.mouse.get_pos()[0] + camera_pos[0])}, {int(pygame.mouse.get_pos()[1] + camera_pos[1])}), ')
            elif event.button == 1 and is_start_window and pygame.Rect(200, 300, 600, 70).collidepoint(pygame.mouse.get_pos()):
                is_start_window = False

pygame.quit()
