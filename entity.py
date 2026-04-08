from __future__ import annotations

import copy
import math
from typing import Optional, Tuple, Type, TypeVar, TYPE_CHECKING

from render_order import RenderOrder

if TYPE_CHECKING:
    from components.ai import BaseAI
    from components.fighter import Fighter
    from game_map import GameMap

T = TypeVar("T", bound="Entity")


class Entity:
    """
    A generic object to represent players, enemies, items, etc.
    """

    gamemap: GameMap

    def __init__(
        self,
        gamemap: Optional[GameMap] = None,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        blocks_movement: bool = False,
        render_order: RenderOrder = RenderOrder.CORPSE,
    ):
        self.x = x
        self.y = y
        self.visual_x = float(x)
        self.visual_y = float(y)
        self.movement_speed: float = 5.0  # tiles per second; overridden by Actor
        self._target_x: Optional[float] = None
        self._target_y: Optional[float] = None
        self.char = char
        self.color = color
        self.name = name
        self.blocks_movement = blocks_movement
        self.render_order = render_order
        if gamemap:
            self.gamemap = gamemap
            gamemap.entities.add(self)

    @property
    def is_moving(self) -> bool:
        return self._target_x is not None

    def update_visual(self, dt: float) -> None:
        """Smoothly move visual position toward the current movement target."""
        if self._target_x is None:
            return
        dx = self._target_x - self.visual_x
        dy = self._target_y - self.visual_y  # type: ignore[operator]
        dist = math.sqrt(dx * dx + dy * dy)
        step = self.movement_speed * dt
        if step >= dist:
            self.visual_x = self._target_x
            self.visual_y = self._target_y  # type: ignore[assignment]
            self._target_x = None
            self._target_y = None
        else:
            self.visual_x += (dx / dist) * step
            self.visual_y += (dy / dist) * step

    def spawn(self: T, gamemap: GameMap, x: int, y: int) -> T:
        """Spawn a copy of this instance at the given location."""
        clone = copy.deepcopy(self)
        clone.x = x
        clone.y = y
        clone.visual_x = float(x)
        clone.visual_y = float(y)
        clone._target_x = None
        clone._target_y = None
        clone.gamemap = gamemap
        gamemap.entities.add(clone)
        return clone

    def place(self, x: int, y: int, gamemap: Optional[GameMap] = None) -> None:
        """Place this entity at a new location. Snaps visual position instantly."""
        self.x = x
        self.y = y
        self.visual_x = float(x)
        self.visual_y = float(y)
        self._target_x = None
        self._target_y = None
        if gamemap:
            if hasattr(self, "gamemap"):
                self.gamemap.entities.remove(self)
            self.gamemap = gamemap
            gamemap.entities.add(self)

    def move(self, dx: int, dy: int) -> None:
        """Move the entity by a given amount and set a pixel target for smooth animation."""
        self.x += dx
        self.y += dy
        self._target_x = float(self.x)
        self._target_y = float(self.y)


class Actor(Entity):
    def __init__(
        self,
        *,
        x: int = 0,
        y: int = 0,
        char: str = "?",
        color: Tuple[int, int, int] = (255, 255, 255),
        name: str = "<Unnamed>",
        ai_cls: Type[BaseAI],
        fighter: Fighter,
        movement_speed: float = 8.0,
    ):
        super().__init__(
            x=x,
            y=y,
            char=char,
            color=color,
            name=name,
            blocks_movement=True,
            render_order=RenderOrder.ACTOR,
        )

        self.ai: Optional[BaseAI] = ai_cls(self)

        self.fighter = fighter
        self.fighter.entity = self

        self.movement_speed = movement_speed  # tiles per second

    @property
    def is_alive(self) -> bool:
        """Returns True as long as this actor can perform actions."""
        return bool(self.ai)
