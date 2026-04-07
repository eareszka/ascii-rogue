from __future__ import annotations

from typing import Optional, Set, TYPE_CHECKING

import tcod.event

from actions import Action, BumpAction, EscapeAction, WaitAction

if TYPE_CHECKING:
    from engine import Engine


MOVE_KEYS = {
    # Arrow keys.
    tcod.event.K_UP: (0, -1),
    tcod.event.K_DOWN: (0, 1),
    tcod.event.K_LEFT: (-1, 0),
    tcod.event.K_RIGHT: (1, 0),
    # Numpad keys.
    tcod.event.K_KP_1: (-1, 1),
    tcod.event.K_KP_2: (0, 1),
    tcod.event.K_KP_3: (1, 1),
    tcod.event.K_KP_4: (-1, 0),
    tcod.event.K_KP_6: (1, 0),
    tcod.event.K_KP_7: (-1, -1),
    tcod.event.K_KP_8: (0, -1),
    tcod.event.K_KP_9: (1, -1),
    # WASD keys.
    tcod.event.K_w: (0, -1),
    tcod.event.K_s: (0, 1),
    tcod.event.K_a: (-1, 0),
    tcod.event.K_d: (1, 0),
}

WAIT_KEYS = {
    tcod.event.K_PERIOD,
    tcod.event.K_KP_5,
    tcod.event.K_CLEAR,
}


class EventHandler(tcod.event.EventDispatch[Action]):
    def __init__(self, engine: Engine):
        self.engine = engine

    def handle_events(self, dt: float) -> None:
        raise NotImplementedError()

    def ev_quit(self, event: tcod.event.Quit) -> Optional[Action]:
        raise SystemExit()


class MainGameEventHandler(EventHandler):
    def __init__(self, engine: Engine):
        super().__init__(engine)
        self.held_keys: Set[int] = set()
        self.player_move_timer: float = 0.0

    def handle_events(self, dt: float) -> None:
        for event in tcod.event.get():
            self.dispatch(event)

        player = self.engine.player

        self.player_move_timer -= dt
        if self.player_move_timer <= 0:
            for key, (dx, dy) in MOVE_KEYS.items():
                if key in self.held_keys:
                    BumpAction(player, dx, dy).perform()
                    self.engine.update_fov()
                    self.player_move_timer = 1.0 / player.movement_speed
                    break

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        self.held_keys.add(event.sym)

        if event.sym == tcod.event.K_ESCAPE:
            EscapeAction(self.engine.player).perform()

        return None

    def ev_keyup(self, event: tcod.event.KeyUp) -> Optional[Action]:
        self.held_keys.discard(event.sym)
        return None


class GameOverEventHandler(EventHandler):
    def handle_events(self, dt: float) -> None:
        for event in tcod.event.get():
            self.dispatch(event)

    def ev_keydown(self, event: tcod.event.KeyDown) -> Optional[Action]:
        if event.sym == tcod.event.K_ESCAPE:
            EscapeAction(self.engine.player).perform()
        return None
