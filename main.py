#!/usr/bin/env python3
import copy

import pygame

from engine import Engine
import entity_factories
from procgen import generate_dungeon
from settings import TILE_SIZE, SCREEN_TILES_W, SCREEN_TILES_H


def main() -> None:
    map_width = 200
    map_height = 150
    room_max_size = 14
    room_min_size = 6
    max_rooms = 80
    max_monsters_per_room = 3

    pygame.init()
    screen = pygame.display.set_mode(
        (SCREEN_TILES_W * TILE_SIZE, SCREEN_TILES_H * TILE_SIZE),
        pygame.FULLSCREEN | pygame.SCALED,
    )
    pygame.display.set_caption("Roguelike")
    clock = pygame.time.Clock()

    player = copy.deepcopy(entity_factories.player)
    engine = Engine(player=player)

    engine.game_map = generate_dungeon(
        max_rooms=max_rooms,
        room_min_size=room_min_size,
        room_max_size=room_max_size,
        map_width=map_width,
        map_height=map_height,
        max_monsters_per_room=max_monsters_per_room,
        engine=engine,
    )
    engine.update_fov()
    engine.snap_camera()  # place camera immediately so there's no lerp-in at start

    while True:
        dt = min(clock.tick(60) / 1000.0, 0.1)  # seconds; capped to avoid spiral of death

        engine.update(dt)
        engine.event_handler.handle_events(dt)
        engine.render(screen)


if __name__ == "__main__":
    main()
