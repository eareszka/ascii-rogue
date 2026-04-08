from __future__ import annotations

import math
from typing import List, Tuple, TYPE_CHECKING

import numpy as np  # type: ignore
import tcod

from actions import Action
from components.base_component import BaseComponent
from settings import PLAYER_HITBOX

if TYPE_CHECKING:
    from entity import Actor


class BaseAI(Action, BaseComponent):
    entity: Actor

    def perform(self) -> None:
        raise NotImplementedError()

    def get_path_to(self, dest_x: int, dest_y: int) -> List[Tuple[int, int]]:
        cost = np.array(self.entity.gamemap.tiles["walkable"], dtype=np.int8)

        for entity in self.entity.gamemap.entities:
            if entity.blocks_movement and cost[entity.x, entity.y]:
                cost[entity.x, entity.y] += 10

        graph = tcod.path.SimpleGraph(cost=cost, cardinal=2, diagonal=3)
        pathfinder = tcod.path.Pathfinder(graph)
        pathfinder.add_root((self.entity.x, self.entity.y))
        path: List[List[int]] = pathfinder.path_to((dest_x, dest_y))[1:].tolist()
        return [(index[0], index[1]) for index in path]


class HostileEnemy(BaseAI):
    def __init__(self, entity: Actor):
        super().__init__(entity)
        self.path: List[Tuple[int, int]] = []

    def _can_place_at(self, fx: float, fy: float) -> bool:
        """Return True if this entity's hitbox fits at (fx, fy) without overlapping walls or the player."""
        game_map = self.entity.gamemap
        h = PLAYER_HITBOX
        cx, cy = fx + 0.5, fy + 0.5

        for corner_x, corner_y in [(cx - h, cy - h), (cx + h, cy - h),
                                    (cx - h, cy + h), (cx + h, cy + h)]:
            tx, ty = int(corner_x), int(corner_y)
            if not game_map.in_bounds(tx, ty) or not game_map.tiles["walkable"][tx, ty]:
                return False

        player = self.engine.player
        pcx = player.visual_x + 0.5
        pcy = player.visual_y + 0.5
        if abs(cx - pcx) < h * 2 and abs(cy - pcy) < h * 2:
            return False

        return True

    def perform(self) -> None:
        entity = self.entity
        target = self.engine.player
        dt = self.engine.dt

        if not self.engine.game_map.visible[entity.x, entity.y]:
            return

        ecx = entity.visual_x + 0.5
        ecy = entity.visual_y + 0.5
        pcx = target.visual_x + 0.5
        pcy = target.visual_y + 0.5

        dist_to_player = math.sqrt((pcx - ecx) ** 2 + (pcy - ecy) ** 2)
        if dist_to_player <= PLAYER_HITBOX * 2:
            return  # Hitboxes touching, stop here

        if not self.path:
            self.path = self.get_path_to(target.x, target.y)
        if not self.path:
            return

        # Move toward the center of the next waypoint tile.
        wp_cx = self.path[0][0] + 0.5
        wp_cy = self.path[0][1] + 0.5
        wdx = wp_cx - ecx
        wdy = wp_cy - ecy
        wdist = math.sqrt(wdx ** 2 + wdy ** 2)

        if wdist < 0.05:
            self.path.pop(0)
            return

        step = entity.movement_speed * dt
        vx = (wdx / wdist) * step
        vy = (wdy / wdist) * step

        new_fx = entity.visual_x + vx
        new_fy = entity.visual_y + vy

        if self._can_place_at(new_fx, new_fy):
            entity.visual_x = new_fx
            entity.visual_y = new_fy
        elif self._can_place_at(new_fx, entity.visual_y):
            entity.visual_x = new_fx
        elif self._can_place_at(entity.visual_x, new_fy):
            entity.visual_y = new_fy
        else:
            self.path = []  # Stuck against something, recompute next frame

        # Keep integer tile position in sync for pathfinding and FOV.
        entity.x = int(entity.visual_x + 0.5)
        entity.y = int(entity.visual_y + 0.5)
