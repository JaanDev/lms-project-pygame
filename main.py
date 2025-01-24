import pygame
import time
import math
import random

SHIP_ACCEL = 15
SHIP_SLOWDOWN = 12
SHIP_MAX_ACCEL = 3000
SHIP_MAX_ACCEL_GROWTH = 0.5
SHIP_REALLY_MAX_ACCEL = 5000
SHIP_CAMERA_OFFSET = (500, 400)

STAR_MIN_COUNT = 75
STAR_MAX_COUNT = 175

SCREEN_W = 1000
SCREEN_H = 800


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
    
    def update(self, dt):
        mouse_pos = list(pygame.mouse.get_pos())
        mouse_pos[0] += camera_pos[0]
        mouse_pos[1] += camera_pos[1]
        if mouse_pos[0] - self.pos[0] == 0:
            self.rot = 180 if mouse_pos[1] > self.pos[1] else 0
        else:
            self.rot = -math.degrees(math.atan((mouse_pos[1] - self.pos[1]) / (mouse_pos[0] - self.pos[0]))) + (90 if mouse_pos[0] < self.pos[0] else -90)

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
    
    def draw(self):
        rotsurf = pygame.transform.rotate(self.surfaces[self.cur_frame], self.rot)
        if self.hasfire:
            firerotsurf = pygame.transform.rotate(self.fire_surfaces[self.cur_frame], self.rot)
            # firerotsurf.fill((255, 255, 255, 128), None, pygame.BLEND_RGBA_MULT)
            screen.blit(firerotsurf, (self.pos[0] - rotsurf.get_rect().w / 2 - camera_pos[0], self.pos[1] - rotsurf.get_rect().h / 2 - camera_pos[1]))
        screen.blit(rotsurf, (self.pos[0] - rotsurf.get_rect().w / 2 - camera_pos[0], self.pos[1] - rotsurf.get_rect().h / 2 - camera_pos[1]))
        
        text_surf = my_font.render(f'{self.accel}', False, (255, 255, 255))
        screen.blit(text_surf, (0, 0))
        # pygame.draw.rect(screen, 'white', (10, 20, 200 * self.accel2 / 5000, 30))
        # pygame.draw.rect(screen, 'red', (10, 20, 200, 30), 1)


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


pygame.init()

screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))

my_font = pygame.font.SysFont('Comic Sans MS', 12)

clock = pygame.time.Clock()

ship = Ship()

camera_pos = [0, 0]

stars = {(0, 0): StarChunk((0, 0))}

running = True
while running:
    dt = clock.tick(100) / 1000

    # update

    ship.update(dt)
    camera_pos = [ship.pos[0] - SHIP_CAMERA_OFFSET[0], ship.pos[1] - SHIP_CAMERA_OFFSET[1]]

    # print(camera_pos)
    # print(chunk)

    for x in range(2):
        for y in range(2):
            chunk = (int(((camera_pos[0] * 0.2 + SCREEN_W * x)) // SCREEN_W), int((camera_pos[1] * 0.2 + SCREEN_H * y) // SCREEN_H))
            if chunk not in stars.keys():
                # print(chunk)
                stars[chunk] = StarChunk(chunk)
                # print(stars)
            stars[chunk].visible = True

    # top_left = (camera_pos[0], camera_pos[1])
    # bottom_left = (camera_pos[0], camera_pos[1] + SCREEN_H)
    # top_right = (camera_pos[0] + SCREEN_W, camera_pos[1])
    # bottom_right = (camera_pos[0] + SCREEN_W, camera_pos[1] + SCREEN_H)

    # for p in (top_left, bottom_left, top_right, bottom_right):


    # draw

    screen.fill((0, 0, 0))

    # stars[0].draw()
    # for s in stars.values():
    #     pygame.draw.rect(screen, s.color, pygame.Rect(s.rect.x - camera_pos[0], s.rect.y - camera_pos[1], SCREEN_W * 0.2, SCREEN_H * 0.2))
    for s in stars.values():
        if s.visible:
            s.draw()
            s.visible = False

    ship.draw()

    pygame.draw.circle(screen, 'green', (200 - camera_pos[0], 200 - camera_pos[1]), 10)
    # pygame.draw.circle(screen, 'green', (ship.pos[0] - camera_pos[0], ship.pos[1] - camera_pos[1]), 5)

    pygame.draw.circle(screen, 'red', (-camera_pos[0], -camera_pos[1]), 15)

    pygame.display.flip()
    
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False
    
pygame.quit()
