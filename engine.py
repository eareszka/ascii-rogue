from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import pygame
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler
from settings import TILE_SIZE, SCREEN_TILES_W, SCREEN_TILES_H, CAMERA_LERP_SPEED, PLAYER_HITBOX

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler


class Engine:
    game_map: GameMap

    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.player = player
        self.dt: float = 0.0
        self.cam_x: float = 0.0
        self.cam_y: float = 0.0
        self._font: Optional[pygame.font.Font] = None

    def snap_camera(self) -> None:
        """Instantly place the camera on the player with no lerp."""
        tx = self.player.visual_x - SCREEN_TILES_W / 2
        ty = self.player.visual_y - SCREEN_TILES_H / 2
        self.cam_x = max(0.0, min(tx, self.game_map.width - SCREEN_TILES_W))
        self.cam_y = max(0.0, min(ty, self.game_map.height - SCREEN_TILES_H))

    def update(self, dt: float) -> None:
        self.dt = dt
        self._handle_enemy_turns()

        # Smooth visual positions for all entities.
        for entity in self.game_map.entities:
            entity.update_visual(dt)

        # Lerp camera toward player.
        tx = self.player.visual_x - SCREEN_TILES_W / 2
        ty = self.player.visual_y - SCREEN_TILES_H / 2
        tx = max(0.0, min(tx, self.game_map.width - SCREEN_TILES_W))
        ty = max(0.0, min(ty, self.game_map.height - SCREEN_TILES_H))
        t = min(1.0, CAMERA_LERP_SPEED * dt)
        self.cam_x += (tx - self.cam_x) * t
        self.cam_y += (ty - self.cam_y) * t

    def _handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.ai.perform()

    def update_fov(self) -> None:
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        self.game_map.explored |= self.game_map.visible

    def _get_font(self) -> pygame.font.Font:
        if self._font is None:
            self._font = pygame.font.SysFont("courier new", TILE_SIZE, bold=True)
        return self._font

    def _draw_hitboxes(self, surface: pygame.Surface) -> None:
        ts = TILE_SIZE
        cam_px = int(self.cam_x * ts)
        cam_py = int(self.cam_y * ts)
        half = PLAYER_HITBOX * ts
        for actor in self.game_map.actors:
            if not self.game_map.visible[actor.x, actor.y]:
                continue
            cx = (actor.visual_x + 0.5) * ts - cam_px
            cy = (actor.visual_y + 0.5) * ts - cam_py
            color = (0, 255, 0) if actor is self.player else (255, 0, 0)
            pygame.draw.rect(surface, color, pygame.Rect(cx - half, cy - half, half * 2, half * 2), 1)

    def render(self, surface: pygame.Surface) -> None:
        font = self._get_font()
        self.game_map.render(surface, font, self.cam_x, self.cam_y)
        self._draw_hitboxes(surface)

        hp_surf = font.render(
            f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
            True, (255, 255, 255),
        )
        surface.blit(hp_surf, (4, surface.get_height() - TILE_SIZE - 4))

        pygame.display.flip()
