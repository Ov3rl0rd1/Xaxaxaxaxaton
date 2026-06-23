from __future__ import annotations

import time

from colorama import Fore, Style
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agrobots.core.simulation import Simulation
from agrobots.models.robot import build_robot
from agrobots.models.task import Task, TaskKind
from agrobots.scenarios import build_default_sim
from agrobots.ui import console as view
from agrobots.ui.theme import console, init_terminal

_KIND_MAP = {
    "SEED": TaskKind.SEED,
    "HARVEST": TaskKind.HARVEST,
    "INSPECT": TaskKind.INSPECT,
    "IRRIGATE": TaskKind.IRRIGATE,
}


def _menu_panel() -> Panel:
    table = Table.grid(padding=(0, 2))
    table.add_column(style="accent", justify="right")
    table.add_column()
    rows = [
        ("1", "показать карту и дашборд"),
        ("2", "сделать 1 тик симуляции"),
        ("3", "прожить 1 день"),
        ("4", "прожить N дней"),
        ("5", "добавить робота"),
        ("6", "добавить задачу (наряд)"),
        ("7", "пополнить склад запчастей"),
        ("8", "полный журнал событий"),
        ("9", "автодемонстрация (анимация)"),
        ("h", "справка по типам и командам"),
        ("q", "выход"),
    ]
    for key, label in rows:
        table.add_row(key, label)
    return Panel(table, title="[title]AGROBOTS · меню[/]", border_style="title")


def _ask(prompt: str) -> str:
    try:
        return input(Fore.CYAN + prompt + Style.RESET_ALL).strip()
    except (EOFError, KeyboardInterrupt):
        return "q"


def _ask_int(prompt: str, default: int | None = None) -> int | None:
    raw = _ask(prompt)
    if not raw and default is not None:
        return default
    try:
        return int(raw)
    except ValueError:
        console.print("[danger]Ожидалось целое число.[/]")
        return None


def cmd_add_robot(sim: Simulation) -> None:
    console.print("[muted]Типы: seeder (сеялка), harvester (комбайн), scout (разведчик)[/]")
    kind = _ask("Тип робота: ")
    name = _ask("Имя: ") or f"{kind}-{len(sim.robots) + 1}"
    x = _ask_int("Координата X: ")
    y = _ask_int("Координата Y: ")
    if x is None or y is None:
        return
    if not sim.field.passable(x, y):
        console.print("[danger]Клетка занята/непроходима. Робот не добавлен.[/]")
        return
    try:
        robot = build_robot(kind, name, x, y)
    except ValueError as exc:
        console.print(f"[danger]{exc}[/]")
        return
    sim.add_robot(robot)
    console.print(f"[ok]Добавлен {robot.kind_name} «{robot.name}».[/]")


def cmd_add_task(sim: Simulation) -> None:
    console.print("[muted]Виды: seed (посев), harvest (сбор), inspect (осмотр), irrigate (полив)[/]")
    kind = _KIND_MAP.get(_ask("Вид задачи: ").upper())
    if kind is None:
        console.print("[danger]Неизвестный вид задачи.[/]")
        return
    x = _ask_int("Координата X: ")
    y = _ask_int("Координата Y: ")
    if x is None or y is None:
        return
    priority = _ask_int("Приоритет 1..5 (1 — срочно) [3]: ", default=3)
    deadline = _ask_int(f"Срок (день) [{sim.day + 2}]: ", default=sim.day + 2)
    duration = _ask_int("Длительность работы (тиков) [2]: ", default=2)
    if None in (priority, deadline, duration):
        return
    if not sim.field.passable(x, y):
        console.print("[danger]Цель непроходима. Задача не создана.[/]")
        return
    task = Task(kind, x, y, priority=priority, deadline=deadline, duration=duration)
    sim.add_task(task)
    console.print(f"[ok]Создан наряд {task.short()}[/]")


def cmd_restock(sim: Simulation) -> None:
    console.print(view.render_depot(sim))
    name = _ask("Деталь для пополнения: ")
    if not name:
        return
    qty = _ask_int("Количество: ")
    if qty is None:
        return
    sim.depot.restock(name, qty)
    console.print(f"[ok]Склад пополнен: {name} +{qty}[/]")


def cmd_run_days(sim: Simulation) -> None:
    n = _ask_int("Сколько дней прожить: ")
    if n is None:
        return
    sim.run_days(max(1, n))
    view.show_dashboard(sim)


def cmd_autodemo(sim: Simulation, days: int = 3) -> None:
    for _ in range(days * sim.ticks_per_day):
        sim.step()
        view.clear()
        view.show_dashboard(sim)
        time.sleep(0.35)
    console.print("[ok]Автодемонстрация завершена.[/]")


def cmd_help() -> None:
    text = Text()
    text.append("AgroBots — симуляция маршрутизации и обслуживания роботов.\n\n")
    text.append("Роботы автоматически берут наряды из очереди приоритетов, строят\n")
    text.append("маршрут (A*) по полю, выполняют работу, ездят на зарядку и в сервис.\n")
    text.append("Случайные события: погода влияет на расход, техника может ломаться.\n\n")
    text.append("Типы роботов:\n", style="title")
    text.append("  seeder    — посев и полив;\n")
    text.append("  harvester — уборка (тяжёлый, прожорливый);\n")
    text.append("  scout     — осмотр (быстрый, экономичный).\n")
    console.print(Panel(text, title="[title]Справка[/]", border_style="accent"))


def run(seed: int = 42) -> None:
    init_terminal()
    sim = build_default_sim(seed=seed)
    console.print("[ok bold]Добро пожаловать в AgroBots![/]")
    view.show_dashboard(sim)

    actions = {
        "1": lambda: view.show_dashboard(sim),
        "2": lambda: (sim.step(), view.show_dashboard(sim)),
        "3": lambda: (sim.run_day(), view.show_dashboard(sim)),
        "4": lambda: cmd_run_days(sim),
        "5": lambda: cmd_add_robot(sim),
        "6": lambda: cmd_add_task(sim),
        "7": lambda: cmd_restock(sim),
        "8": lambda: console.print(view.render_log(sim, n=40)),
        "9": lambda: cmd_autodemo(sim),
        "h": cmd_help,
    }

    while True:
        console.print(_menu_panel())
        choice = _ask("Выбор: ").lower()
        if choice in ("q", "quit", "exit", "0"):
            console.print("[warn]Завершение работы. До встречи![/]")
            break
        action = actions.get(choice)
        if action is None:
            console.print("[danger]Неизвестная команда. Нажмите h для справки.[/]")
            continue
        action()


if __name__ == "__main__":
    run()
