import copy
import random
from collections import defaultdict
from collections.abc import Sequence

import pygame

RESOLUTION = 500, 900
BLOCKS_HORIZONTAL = 10
BLOCKS_VERTICAL = 20
BLOCK_WIDTH = RESOLUTION[0] / BLOCKS_HORIZONTAL
BLOCK_HEIGHT = RESOLUTION[1] / BLOCKS_VERTICAL

ADD_BLOCK = pygame.USEREVENT + 1


def main():
    pygame.init()
    screen = pygame.display.set_mode(RESOLUTION)
    pygame.display.set_caption("Tetris")
    bg = get_bg()

    player_blocks = pygame.sprite.Group()
    placed_blocks = pygame.sprite.Group()
    all_sprites = pygame.sprite.Group()

    player_blocks.add(*create_player_blocks())
    all_sprites.add(*player_blocks)

    clock = pygame.time.Clock()
    blocks_updater = BlocksUpdater()
    congratulations = Congratulations()

    score = 0
    record = 0
    dead = False
    running = True
    started = False

    while running:
        if not started:
            for event in pygame.event.get():
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        started = True
                        continue
                elif event.type == pygame.QUIT:
                    running = False

            screen.fill((0, 0, 0))
            text_lines = ['Press any key to start']
            write_text_lines(text_lines, screen)
        else:
            if dead:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                        else:
                            dead = False
                            score = 0
                            placed_blocks.empty()
                            all_sprites.empty()
                            player_blocks.empty()
                            pygame.event.clear()
                            player_blocks.add(*create_player_blocks())
                            all_sprites.add(*player_blocks)
                            continue
                    elif event.type == pygame.QUIT:
                        running = False

                screen.fill((0, 0, 0))
                text_lines = ['Game Over!', f'Score: {score}', f'Record: {record}', 'Press any key to restart']
                write_text_lines(text_lines, screen)
            else:
                for event in pygame.event.get():
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ESCAPE:
                            running = False
                    elif event.type == pygame.QUIT:
                        running = False
                    elif event.type == ADD_BLOCK:
                        placed_blocks.add(*player_blocks)
                        player_blocks.empty()
                        player_blocks.add(*create_player_blocks())
                        all_sprites.add(*player_blocks)

                        nr_connections_complete_line = BLOCKS_HORIZONTAL - 1
                        # dict where the key is the bottom and values are lefts and rights
                        left_right = defaultdict(list)

                        for block in placed_blocks:
                            left_right[block.rect.bottom].append(block.rect.left)
                            left_right[block.rect.bottom].append(block.rect.right)

                        for bottom in sorted(left_right):
                            uniq = set(left_right[bottom])
                            if len(left_right[bottom]) - len(uniq) == nr_connections_complete_line:
                                # line complete
                                for block in placed_blocks.copy():
                                    if block.rect.bottom == bottom:
                                        block.remove(placed_blocks, all_sprites)
                                for block in placed_blocks:
                                    if block.rect.bottom < bottom:
                                        block.rect.move_ip(0, RESOLUTION[1] / BLOCKS_VERTICAL)
                                congratulations.active = True
                                score += 10

                        score += 1
                        if score > record:
                            record = score

                pressed_keys = pygame.key.get_pressed()
                blocks_updater.update_player_blocks(pressed_keys, player_blocks, placed_blocks)

                if (collided := pygame.sprite.groupcollide(player_blocks, placed_blocks, False, False)) \
                        or group_has_bottom(player_blocks, RESOLUTION[1]):
                    if group_top_is_above_screen(player_blocks):
                        dead = True
                    else:
                        if collided:
                            align_collided(collided, player_blocks)
                        pygame.event.post(pygame.event.Event(ADD_BLOCK))

                screen.blit(bg, (0, 0))
                draw_grid(screen)
                draw_drop_preview(screen, player_blocks, placed_blocks)

                for entity in all_sprites:
                    screen.blit(entity.surf, entity.rect)

                write_score(score, screen)
                congratulations.display(screen)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()


def get_bg() -> pygame.Surface:
    try:
        return pygame.image.load("stars.png").convert()
    except FileNotFoundError:
        surf = pygame.Surface((RESOLUTION[0], RESOLUTION[1]))
        surf.fill((27, 49, 69))
        return surf


def group_has_bottom(group: pygame.sprite.Group, bottom: int):
    """Checks if group "group" contains a sprite with bottom "bottom" """
    for sprite in group:
        if sprite.rect.bottom == bottom:
            return True
    return False


def group_top_is_above_screen(group: pygame.sprite.Group):
    for sprite in group:
        if sprite.rect.top < 0:
            return True
    return False


def group_bottom_is_below_screen(group: pygame.sprite.Group):
    for sprite in group:
        if sprite.rect.bottom > RESOLUTION[1]:
            return True
    return False


def group_bottom(group: pygame.sprite.Group):
    """Returns the bottom of the lowest (on the screen) sprite in the group"""
    return max(map(lambda sprt: sprt.rect.bottom, group), default=0)


def group_bottom_sprites(group: pygame.sprite.Group):
    """Returns a list of the group's sprites which have the lowest (on the screen) bottom"""
    bottom = max(map(lambda sprt: sprt.rect.bottom, group), default=RESOLUTION[1])
    return list(filter(lambda sprt: sprt.rect.bottom == bottom, group))


def group_left(group: pygame.sprite.Group):
    return min(map(lambda sprt: sprt.rect.left, group), default=RESOLUTION[0])


def group_right(group: pygame.sprite.Group):
    return max(map(lambda sprt: sprt.rect.right, group), default=0)


def group_top(group: pygame.sprite.Group, rect: pygame.Rect):
    """Returns the highest (on the screen) top of the group's sprites whose rects have the same centerx as "rect.centerx"
    and lower (on the screen) centery than "rect.centery" """
    same_centerx_lower_centery = filter(lambda sprt: sprt.rect.centerx == rect.centerx
                                                     and sprt.rect.centery >= rect.centery, group)
    return min(map(lambda sprt: sprt.rect.top, same_centerx_lower_centery), default=RESOLUTION[1])


def align_collided(collided: dict[pygame.sprite.Sprite, list[pygame.sprite.Sprite]],
                   player_blocks: pygame.sprite.Group):
    diff = 0
    for block in collided:
        for block2 in collided[block]:
            diff = block2.rect.top - block.rect.bottom
            break
        if collided[block]:
            break
    for block in player_blocks:
        block.rect.move_ip(0, diff)


def write_text_lines(lines: list[str], screen: pygame.Surface, font_size=32):
    font = pygame.font.SysFont('arial', font_size)
    text_surfaces = []
    for line in lines:
        text_surfaces.append(font.render(line, True, (255, 255, 255), (0, 0, 0)))
    for i, surface in enumerate(text_surfaces):
        text_rect = surface.get_rect(center=(RESOLUTION[0] / 2, (RESOLUTION[1] / 2) + i * font_size))
        screen.blit(surface, text_rect)


def write_score(score, screen):
    font = pygame.font.SysFont('arial', 20)
    text_surface = font.render(f"Score: {score}", True, (255, 255, 255), (0, 0, 0))
    text_surface.set_alpha(150)
    text_rect = text_surface.get_rect(topleft=(25, 25))
    screen.blit(text_surface, text_rect)


def draw_grid(screen: pygame.Surface,
              block_size=(RESOLUTION[0] // BLOCKS_HORIZONTAL, RESOLUTION[1] // BLOCKS_VERTICAL)):
    for x in range(0, RESOLUTION[0], block_size[0]):
        for y in range(0, RESOLUTION[1], block_size[1]):
            rect = pygame.Rect(x, y, block_size[0], block_size[1])
            surf = pygame.Surface(rect.size)
            surf.set_alpha(50)
            surf.fill((255, 255, 255), surf.get_rect().inflate(-1, -1))
            screen.blit(surf, rect)


def draw_drop_preview(screen: pygame.Surface, player_blocks: pygame.sprite.Group, placed_blocks: pygame.sprite.Group):
    diffs = []
    for block in player_blocks:
        top_placed = group_top(placed_blocks, block.rect)
        diffs.append(top_placed - block.rect.bottom)
    min_diff = min(diffs)
    moved_rects = []
    for block in player_blocks:
        moved_rects.append(block.rect.move(0, min_diff))
    for rect in moved_rects:
        surf = pygame.Surface(rect.size)
        surf.set_alpha(50)
        surf.fill((0, 0, 0), surf.get_rect())
        screen.blit(surf, rect)


def create_player_blocks() -> list['Block']:
    player_blocks = []
    color = tuple(random.randint(90, 245) for _ in range(3))
    block_type = random.randint(1, 6)
    player_blocks.extend(get_block(block_type, color))
    return player_blocks


def get_block(block_type: int, color: tuple[int, int, int]) -> list['Block']:
    block_type = block_type if block_type in range(1, 7) else 1
    rects_topleft = []
    if block_type == 1:
        rects_topleft = [(BLOCK_WIDTH * 4, - BLOCK_HEIGHT)]
    elif block_type == 2:
        rects_topleft = [(BLOCK_WIDTH * 3, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 4, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 6, - BLOCK_HEIGHT)]
    elif block_type == 3:
        rects_topleft = [(BLOCK_WIDTH * 4, 0),
                         (BLOCK_WIDTH * 4, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, 0),
                         (BLOCK_WIDTH * 5, - BLOCK_HEIGHT)]
    elif block_type == 4:
        rects_topleft = [(BLOCK_WIDTH * 4, BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 4, 0),
                         (BLOCK_WIDTH * 4, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, BLOCK_HEIGHT)]
    elif block_type == 5:
        rects_topleft = [(BLOCK_WIDTH * 4, 0),
                         (BLOCK_WIDTH * 4, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, 0)]
    elif block_type == 6:
        rects_topleft = [(BLOCK_WIDTH * 4, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 5, 0),
                         (BLOCK_WIDTH * 5, - BLOCK_HEIGHT),
                         (BLOCK_WIDTH * 6, - BLOCK_HEIGHT)]
    return list(map(lambda rtl: Block(color, block_type, rtl), rects_topleft))


def rotate_player_blocks(player_blocks: pygame.sprite.Group, placed_blocks: pygame.sprite.Group):
    block_type = player_blocks.sprites()[0].block_type
    if block_type in [1, 3]:
        pass
    elif block_type == 2:
        new_player_blocks = pygame.sprite.Group()
        if player_blocks.sprites()[0].rect.centerx < player_blocks.sprites()[-1].rect.centerx:
            for i, block in enumerate(player_blocks):
                # rotate vertically
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 2, BLOCK_HEIGHT * 2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        else:
            for i, block in enumerate(player_blocks):
                # rotate horizontally
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -2, BLOCK_HEIGHT * -2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        move = True
        for block in new_player_blocks:
            if pygame.sprite.spritecollideany(block, placed_blocks):
                move = False
        if move:
            for i, block in enumerate(player_blocks):
                player_blocks.sprites()[i].rect = new_player_blocks.sprites()[i].rect
    elif block_type == 4:
        new_player_blocks = pygame.sprite.Group()
        if player_blocks.sprites()[0].rect.centerx < player_blocks.sprites()[-1].rect.centerx:
            for i, block in enumerate(player_blocks):
                # first left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 0)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 0, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 0, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[0].rect.centery > player_blocks.sprites()[-1].rect.centery:
            for i, block in enumerate(player_blocks):
                # second left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * -2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 0, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 0)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -2, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[0].rect.centerx > player_blocks.sprites()[-1].rect.centerx:
            for i, block in enumerate(player_blocks):
                # third left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 0, BLOCK_HEIGHT * 2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[0].rect.centery < player_blocks.sprites()[-1].rect.centery:
            for i, block in enumerate(player_blocks):
                # fourth left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 2, BLOCK_HEIGHT * 0)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        move = True
        for block in new_player_blocks:
            if pygame.sprite.spritecollideany(block, placed_blocks):
                move = False
        if move:
            for i, block in enumerate(player_blocks):
                player_blocks.sprites()[i].rect = new_player_blocks.sprites()[i].rect
    elif block_type == 5:
        new_player_blocks = pygame.sprite.Group()
        if player_blocks.sprites()[0].rect.centery > player_blocks.sprites()[1].rect.centery:
            for i, block in enumerate(player_blocks):
                # first left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 0)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[0].rect.centery < player_blocks.sprites()[1].rect.centery:
            for i, block in enumerate(player_blocks):
                # second left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * -2)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 0)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
        move = True
        for block in new_player_blocks:
            if pygame.sprite.spritecollideany(block, placed_blocks):
                move = False
        if move:
            for i, block in enumerate(player_blocks):
                player_blocks.sprites()[i].rect = new_player_blocks.sprites()[i].rect
    elif block_type == 6:
        new_player_blocks = pygame.sprite.Group()
        if player_blocks.sprites()[0].rect.centerx < player_blocks.sprites()[2].rect.centerx:
            for i, block in enumerate(player_blocks):
                # first left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[1].rect.centery > player_blocks.sprites()[2].rect.centery \
                and player_blocks.sprites()[1].rect.centerx < player_blocks.sprites()[3].rect.centerx \
                and player_blocks.sprites()[0].rect.centery < player_blocks.sprites()[3].rect.centery:
            for i, block in enumerate(player_blocks):
                # second left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[1].rect.centerx < player_blocks.sprites()[2].rect.centerx < \
                player_blocks.sprites()[3].rect.centerx \
                and player_blocks.sprites()[1].rect.centerx < player_blocks.sprites()[3].rect.centerx:
            for i, block in enumerate(player_blocks):
                # third left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        elif player_blocks.sprites()[2].rect.centery < player_blocks.sprites()[3].rect.centery:
            for i, block in enumerate(player_blocks):
                # fourth left rotation
                if i == 0:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * -1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 1:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * 1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
                if i == 2:
                    new_block = copy.copy(block)
                    new_player_blocks.add(new_block)
                if i == 3:
                    new_block = copy.copy(block)
                    new_rect = block.rect.move(BLOCK_WIDTH * 1, BLOCK_HEIGHT * -1)
                    new_block.rect = new_rect
                    new_player_blocks.add(new_block)
        move = True
        for block in new_player_blocks:
            if pygame.sprite.spritecollideany(block, placed_blocks):
                move = False
        if move:
            for i, block in enumerate(player_blocks):
                player_blocks.sprites()[i].rect = new_player_blocks.sprites()[i].rect


class BlocksUpdater:
    def __init__(self):
        self.last_sideways_movement_time = pygame.time.get_ticks()
        self.last_auto_down_movement_time = pygame.time.get_ticks()
        self.last_down_movement_time = pygame.time.get_ticks()
        self.last_down_drop_time = pygame.time.get_ticks()

    def update_player_blocks(self, pressed_keys: Sequence[bool], player_blocks: pygame.sprite.Group,
                             placed_blocks: pygame.sprite.Group):
        if pygame.time.get_ticks() - self.last_auto_down_movement_time > 700:
            for block in player_blocks:
                block.rect.move_ip(0, BLOCK_HEIGHT)
            self.last_auto_down_movement_time = pygame.time.get_ticks()

        if pressed_keys[pygame.K_DOWN] and pygame.time.get_ticks() - self.last_down_movement_time >= 70:
            for block in player_blocks:
                block.rect.move_ip(0, BLOCK_HEIGHT)
            self.last_down_movement_time = pygame.time.get_ticks()

        if pressed_keys[pygame.K_d] and pygame.time.get_ticks() - self.last_down_drop_time >= 140:
            player_bottom_sprts = group_bottom_sprites(player_blocks)
            top_placed = []
            for sprite in player_bottom_sprts:
                top_placed.append(group_top(placed_blocks, sprite.rect))
            top_placed = min(top_placed)
            diff = top_placed - group_bottom(player_blocks)
            for block in player_blocks:
                block.rect.move_ip(0, diff)
            self.last_down_drop_time = pygame.time.get_ticks()

        if group_bottom_is_below_screen(player_blocks):
            diff = group_bottom(player_blocks) - RESOLUTION[1]
            for block in player_blocks:
                block.rect.move_ip(0, -diff)

        if pressed_keys[pygame.K_LEFT] and pressed_keys[pygame.K_RIGHT]:
            return

        if pressed_keys[pygame.K_SPACE] and pygame.time.get_ticks() - self.last_sideways_movement_time >= 200:
            rotate_player_blocks(player_blocks, placed_blocks)
            self.last_sideways_movement_time = pygame.time.get_ticks()

        if pressed_keys[pygame.K_LEFT] and pygame.time.get_ticks() - self.last_sideways_movement_time >= 70:
            move = True
            for block in player_blocks:
                moved_rect = block.rect.move(-BLOCK_WIDTH, 0)
                sprt = pygame.sprite.Sprite()
                sprt.rect = moved_rect
                if pygame.sprite.spritecollideany(sprt, placed_blocks):
                    move = False
            if move:
                for block in player_blocks:
                    block.rect.move_ip(-BLOCK_WIDTH, 0)
                self.last_sideways_movement_time = pygame.time.get_ticks()
        elif pressed_keys[pygame.K_RIGHT] and pygame.time.get_ticks() - self.last_sideways_movement_time >= 70:
            move = True
            for block in player_blocks:
                moved_rect = block.rect.move(BLOCK_WIDTH, 0)
                sprt = pygame.sprite.Sprite()
                sprt.rect = moved_rect
                if pygame.sprite.spritecollideany(sprt, placed_blocks):
                    move = False
            if move:
                for block in player_blocks:
                    block.rect.move_ip(BLOCK_WIDTH, 0)
                self.last_sideways_movement_time = pygame.time.get_ticks()

        if (left := group_left(player_blocks)) < 0:
            for block in player_blocks:
                block.rect.move_ip(-left, 0)

        if (right := group_right(player_blocks)) > RESOLUTION[0]:
            diff = right - RESOLUTION[0]
            for block in player_blocks:
                block.rect.move_ip(-diff, 0)


class Congratulations:
    def __init__(self):
        self.time_start_display = None
        self.displayed = False
        self.message_list = ["Great!", "Keep it up!", "Way to go!", "I'm proud of you!",
                             "Wow!", "Excellent!", "Amazing!", "Good job!", "Excellent job!",
                             "Nice!", "Nice job!"]
        self.message = None
        self.active = False

    def _write_message(self, screen, message):
        font = pygame.font.SysFont('arial', 48)
        text_surface = font.render(message, True, (255, 255, 255), (0, 0, 0))
        text_surface.set_alpha(200)
        text_rect = text_surface.get_rect(center=(RESOLUTION[0] / 2, (RESOLUTION[1] / 2)))
        screen.blit(text_surface, text_rect)

    def display(self, screen):
        if self.active:
            time = pygame.time.get_ticks()
            if self.displayed and time - self.time_start_display < 1000:
                self._write_message(screen, self.message)
            elif self.displayed:
                self.time_start_display = None
                self.displayed = False
                self.message = None
                self.active = False
            elif not self.displayed:
                self.time_start_display = pygame.time.get_ticks()
                self.displayed = True
                self.message = random.choice(self.message_list)
                self._write_message(screen, self.message)


class Block(pygame.sprite.Sprite):
    def __init__(self, color, block_type, rect_topleft=(BLOCK_WIDTH * 4, - BLOCK_HEIGHT)):
        super().__init__()
        self.surf = pygame.Surface((BLOCK_WIDTH, BLOCK_HEIGHT))
        self.rect = self.surf.get_rect(topleft=rect_topleft)
        self.surf.fill(color, self.surf.get_rect())
        self.surf.fill((250, 250, 250), pygame.Rect(1, 1, self.rect.width - 2, 1))
        self.surf.fill((250, 250, 250), pygame.Rect(self.rect.width - 2, 1, 1, self.rect.height - 2))
        self.surf.fill((5, 5, 5), pygame.Rect(1, 1, 1, self.rect.height - 2))
        self.surf.fill((5, 5, 5), pygame.Rect(1, self.rect.height - 2, self.rect.width - 2, 1))
        self.block_type = block_type


if __name__ == '__main__':
    main()
