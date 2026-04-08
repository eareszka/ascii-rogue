from __future__ import annotations

import math
from typing import Set, Tuple, TYPE_CHECKING

import pygame

from settings import PLAYER_SPEED, PLAYER_HITBOX

if TYPE_CHECKING:
    from engine import Engine


MOVE_KEYS = {
    # Arrow keys
    pygame.K_UP:    (0, -1),
    pygame.K_DOWN:  (0,  1),
    pygame.K_LEFT:  (-1, 0),
    pygame.K_RIGHT: ( 1, 0),
    # WASD
    pygame.K_w: (0, -1),
    pygame.K_s: (0,  1),
    pygame.K_a: (-1, 0),
    pygame.K_d: ( 1, 0),
    # Numpad
    pygame.K_KP1: (-1,  1),
    pygame.K_KP2: ( 0,  1),
    pygame.K_KP3: ( 1,  1),
    pygame.K_KP4: (-1,  0),
    pygame.K_KP6: ( 1,  0),
    pygame.K_KP7: (-1, -1),
    pygame.K_KP8: ( 0, -1),
    pygame.K_KP9: ( 1, -1),
}


class EventHandler:
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, dt: float) -> None:
        raise NotImplementedError()


class MainGameEventHandler(EventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.held_keys: Set[int] = set()
        self._prev_tile: Tuple[int, int] = (-1, -1)  # triggers FOV sync on first move

    def _can_place_at(self, fx: float, fy: float) -> bool:
        """Return True if the player hitbox fits at tile-float position (fx, fy).
        fx/fy are the top-left of the character tile, so center the hitbox at +0.5."""
        game_map = self.engine.game_map
        h = PLAYER_HITBOX
        cx, cy = fx + 0.5, fy + 0.5

        # Tile walkability check.
        for corner_x, corner_y in [(cx - h, cy - h), (cx + h, cy - h),
                                    (cx - h, cy + h), (cx + h, cy + h)]:
            tx, ty = int(corner_x), int(corner_y)
            if not game_map.in_bounds(tx, ty):
                return False
            if not game_map.tiles["walkable"][tx, ty]:
                return False

        # Entity hitbox overlap check.
        player = self.engine.player
        for actor in game_map.actors:
            if actor is player:
                continue
            ecx = actor.visual_x + 0.5
            ecy = actor.visual_y + 0.5
            if abs(cx - ecx) < h + PLAYER_HITBOX and abs(cy - ecy) < h + PLAYER_HITBOX:
                return False

        return True

    def handle_events(self, dt: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit()
            elif event.type == pygame.KEYDOWN:
                self.held_keys.add(event.key)
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit()
            elif event.type == pygame.KEYUP:
                self.held_keys.discard(event.key)

        player = self.engine.player

        # Accumulate direction from all held movement keys.
        dx, dy = 0.0, 0.0
        for key, (kx, ky) in MOVE_KEYS.items():
            if key in self.held_keys:
                dx += kx
                dy += ky
        dx = max(-1.0, min(1.0, dx))
        dy = max(-1.0, min(1.0, dy))

        # Normalize diagonal movement so speed is consistent.
        if dx != 0.0 and dy != 0.0:
            length = math.sqrt(dx * dx + dy * dy)
            dx /= length
            dy /= length

        if dx != 0.0 or dy != 0.0:
            step = PLAYER_SPEED * dt
            vx = dx * step
            vy = dy * step

            new_fx = player.visual_x + vx
            new_fy = player.visual_y + vy

            # Try full movement, then axis-aligned fallbacks for smooth wall sliding.
            if self._can_place_at(new_fx, new_fy):
                player.visual_x = new_fx
                player.visual_y = new_fy
            elif self._can_place_at(new_fx, player.visual_y):
                player.visual_x = new_fx
            elif self._can_place_at(player.visual_x, new_fy):
                player.visual_y = new_fy

            # Sync integer tile to nearest center; update FOV on boundary cross.
            new_tx = int(player.visual_x + 0.5)
            new_ty = int(player.visual_y + 0.5)
            if (new_tx, new_ty) != self._prev_tile:
                player.x = new_tx
                player.y = new_ty
                self._prev_tile = (new_tx, new_ty)
                self.engine.update_fov()


class GameOverEventHandler(EventHandler):
    def handle_events(self, dt: float) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                raise SystemExit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    raise SystemExit()
