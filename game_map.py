from __future__ import annotations

from typing import Iterable, Iterator, Optional, TYPE_CHECKING

import numpy as np  # type: ignore
from tcod.console import Console

from entity import Actor
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

        self.visible = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player can currently see
        self.explored = np.full(
            (width, height), fill_value=False, order="F"
        )  # Tiles the player has seen before

    @property
    def actors(self) -> Iterator[Actor]:
        """Iterate over this maps living actors."""
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
        """Return True if x and y are inside of the bounds of this map."""
        return 0 <= x < self.width and 0 <= y < self.height

    def render(self, console: Console, cam_x: int, cam_y: int) -> None:
        """
        Renders the portion of the map visible through the camera viewport.

        cam_x, cam_y is the top-left map tile that maps to console (0, 0).
        """
        view_width = console.width
        view_height = console.height

        # Clamp camera so it never goes out of map bounds.
        cam_x = max(0, min(cam_x, self.width - view_width))
        cam_y = max(0, min(cam_y, self.height - view_height))

        # Slice the map arrays to the viewport region.
        map_slice = np.s_[cam_x : cam_x + view_width, cam_y : cam_y + view_height]

        console.tiles_rgb[0:view_width, 0:view_height] = np.select(
            condlist=[self.visible[map_slice], self.explored[map_slice]],
            choicelist=[self.tiles["light"][map_slice], self.tiles["dark"][map_slice]],
            default=tile_types.SHROUD,
        )

        entities_sorted_for_rendering = sorted(
            self.entities, key=lambda x: x.render_order.value
        )

        for entity in entities_sorted_for_rendering:
            screen_x = entity.x - cam_x
            screen_y = entity.y - cam_y
            if (
                0 <= screen_x < view_width
                and 0 <= screen_y < view_height
                and self.visible[entity.x, entity.y]
            ):
                console.print(x=screen_x, y=screen_y, string=entity.char, fg=entity.color)
