from __future__ import annotations

from typing import Iterable, TYPE_CHECKING, Optional

import numpy as np  # type: ignore
from tcod.console import Console

import tile_types

if TYPE_CHECKING:
    from entity import Entity

class GameMap:
    def __init__(self, width: int, height: int, entities: Iterable[Entity] = ()):
        self.width, self.height = width, height
        self.entities = set(entities)
        self.tiles = np.full((width, height), fill_value=tile_types.wall, order="F")

        self.visible = np.full((width, height), fill_value=False, order="F") #tiles player can currently see
        self.explored = np.full((width, height), fill_value=False, order="F") #tiles the player has been through

    
    def get_blocking_entity_at_location(self, location_x: int, location_y: int) -> Optional[Entity]:
        for entity in self.entities:
            if entity.blocks_movement and entity.x == location_x and entity.y == location_y:
                return entity

        return None


    def in_bounds(self, x: int, y: int) -> bool:
        """Return true if x and y are inside of the bounds of the map"""
        return 0 <= x < self.width and 0 <= y < self.height


    def render(self, console: Console) -> None:
        console.tiles_rgb[0:self.width, 0:self.height] = np.select(
                condlist=[self.visible, self.explored],
                choicelist=[self.tiles["light"], self.tiles["dark"]],
                default=tile_types.SHROUD #default state for tiles
        )

        for entity in self.entities: #iterates through all entities draws to screen
            if self.visible[entity.x, entity.y]:
                console.print(x=entity.x, y=entity.y, string=entity.char, fg=entity.color)
