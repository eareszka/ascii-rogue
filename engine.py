from __future__ import annotations

from typing import TYPE_CHECKING

from tcod.context import Context
from tcod.console import Console
from tcod.map import compute_fov

from input_handlers import MainGameEventHandler

if TYPE_CHECKING:
    from entity import Actor
    from game_map import GameMap
    from input_handlers import EventHandler


class Engine:
    game_map: GameMap

    def __init__(self, player: Actor):
        self.event_handler: EventHandler = MainGameEventHandler(self)
        self.player = player
        self.enemy_timer: float = 0.0
        self.enemy_turn_interval: float = 0.5  # seconds between enemy moves

    def update(self, dt: float) -> None:
        self.enemy_timer -= dt
        if self.enemy_timer <= 0:
            self._handle_enemy_turns()
            self.enemy_timer = self.enemy_turn_interval

    def _handle_enemy_turns(self) -> None:
        for entity in set(self.game_map.actors) - {self.player}:
            if entity.ai:
                entity.ai.perform()

    def update_fov(self) -> None:
        """Recompute the visible area based on the players point of view."""
        self.game_map.visible[:] = compute_fov(
            self.game_map.tiles["transparent"],
            (self.player.x, self.player.y),
            radius=8,
        )
        # If a tile is "visible" it should be added to "explored".
        self.game_map.explored |= self.game_map.visible

    def get_camera(self, view_width: int, view_height: int) -> tuple[int, int]:
        """Return the top-left map tile for a camera centered on the player."""
        cam_x = self.player.x - view_width // 2
        cam_y = self.player.y - view_height // 2
        cam_x = max(0, min(cam_x, self.game_map.width - view_width))
        cam_y = max(0, min(cam_y, self.game_map.height - view_height))
        return cam_x, cam_y

    def render(self, console: Console, context: Context) -> None:
        cam_x, cam_y = self.get_camera(console.width, console.height)
        self.game_map.render(console, cam_x, cam_y)

        console.print(
            x=1,
            y=console.height - 3,
            string=f"HP: {self.player.fighter.hp}/{self.player.fighter.max_hp}",
        )

        context.present(console)

        console.clear()
