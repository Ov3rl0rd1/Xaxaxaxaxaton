from __future__ import annotations

import sys

import colorama
from rich.console import Console
from rich.theme import Theme

from agrobots.models.robot import RobotStatus
from agrobots.models.task import TaskStatus

AGRO_THEME = Theme(
    {
        "idle": "grey58",
        "moving": "bright_cyan",
        "working": "bright_green",
        "charging": "bright_yellow",
        "service": "magenta",
        "broken": "bold bright_red",
        "ok": "bright_green",
        "warn": "bright_yellow",
        "danger": "bold bright_red",
        "muted": "grey42",
        "title": "bold bright_blue",
        "accent": "bright_cyan",
        "station": "bright_yellow",
        "depot": "magenta",
        "obstacle": "grey37",
    }
)

console = Console(theme=AGRO_THEME, highlight=False, legacy_windows=False)

STATUS_STYLE = {
    RobotStatus.IDLE: "idle",
    RobotStatus.MOVING: "moving",
    RobotStatus.WORKING: "working",
    RobotStatus.CHARGING: "charging",
    RobotStatus.SERVICE: "service",
    RobotStatus.BROKEN: "broken",
}

TASK_STYLE = {
    TaskStatus.PENDING: "warn",
    TaskStatus.ASSIGNED: "accent",
    TaskStatus.IN_PROGRESS: "moving",
    TaskStatus.DONE: "ok",
    TaskStatus.FAILED: "danger",
}


def init_terminal() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except (AttributeError, ValueError):
        pass
    colorama.just_fix_windows_console()
