from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np
import pygame

from entity import Actor
from settings import TILE_SIZE
import tile_types

if TYPE_CHECKING:
    from engine import Engine
    from entity import Entity


class GameMap:
    def __init__(
        self, engine: Engine, width: int, height: int, entities: Iterable[Entity] = ()
    ):
        self.engine = engine
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F")
        self.explored = np.full((width, height), fill_value=False, order="F")

    @property
    def actors(self) -> Iterator[Actor]:
        yield from (
            entity
            for entity in self.entities
            if isinstance(entity, Actor) and entity.is_alive
        )

    def get_blocking_entity_at_location(
        self, location_x: int, location_y: int,
    ) -> Optional[Entity]:
        for entity in self.entities:
            if (
                entity.blocks_movement
                and entity.x == location_x
                and entity.y == location_y
            ):
                return entity
        return None

    def get_actor_at_location(self, x: int, y: int) -> Optional[Actor]:
        for actor in self.actors:
            if actor.x == x and actor.y == y:
                return actor
        return None

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, surface: pygame.Surface, font: pygame.font.Font, cam_x: float, cam_y: float) -> None:
        """
        Render the map and entities. cam_x/cam_y are the top-left tile
        position of the viewport as floats for sub-tile smooth scrolling.
        """
        ts = TILE_SIZE
        sw = surface.get_width()
        sh = surface.get_height()

        # Convert float camera to integer pixel offset for 1-pixel-precise scrolling.
        cam_px = int(cam_x * ts)
        cam_py = int(cam_y * ts)

        # Tile range that could be on screen.
        tx_start = max(0, cam_px // ts)
        ty_start = max(0, cam_py // ts)
        tx_end = min(self.width,  (cam_px + sw) // ts + 2)
        ty_end = min(self.height, (cam_py + sh) // ts + 2)

        surface.fill((0, 0, 0))

        # Draw tile backgrounds.
        for ty in range(ty_start, ty_end):
            for tx in range(tx_start, tx_end):
                px = tx * ts - cam_px
                py = ty * ts - cam_py

                if self.visible[tx, ty]:
                    color = tuple(int(c) for c in self.tiles["light"]["bg"][tx, ty])
                elif self.explored[tx, ty]:
                    color = tuple(int(c) for c in self.tiles["dark"]["bg"][tx, ty])
                else:
                    continue  # black (already filled)

                pygame.draw.rect(surface, color, (px, py, ts, ts))

        # Draw entities on top.
        for entity in sorted(self.entities, key=lambda e: e.render_order.value):
            if not self.in_bounds(entity.x, entity.y):
                continue
            if not self.visible[entity.x, entity.y]:
                continue
            px = int(entity.visual_x * ts) - cam_px + 4
            py = int(entity.visual_y * ts) - cam_py - 4
            char_surf = font.render(entity.char, True, entity.color)
            surface.blit(char_surf, (px, py))
