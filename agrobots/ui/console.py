from __future__ import annotations

from rich.align import Align
from rich.columns import Columns
from rich.console import Group, RenderableType
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from agrobots.core.simulation import Simulation
from agrobots.models.field import CellKind
from agrobots.ui.theme import STATUS_STYLE, TASK_STYLE, console


def _bar(value: float, total: float, style: str, width: int = 10) -> Text:
    filled = max(0, min(width, int(round((value / total) * width)))) if total else 0
    text = Text()
    text.append("█" * filled, style=style)
    text.append("·" * (width - filled), style="muted")
    text.append(f" {value:>3.0f}%")
    return text


def render_map(sim: Simulation) -> Panel:
    field = sim.field
    glyphs = [[("·", "muted") for _ in range(field.width)] for _ in range(field.height)]
    for row in field.grid:
        for cell in row:
            if cell.kind is CellKind.OBSTACLE:
                glyphs[cell.y][cell.x] = ("█", "obstacle")
            elif cell.kind is CellKind.CHARGE:
                glyphs[cell.y][cell.x] = ("C", "station")
            elif cell.kind is CellKind.DEPOT:
                glyphs[cell.y][cell.x] = ("D", "depot")

    for task in sim.dispatcher.pending:
        x, y = task.target
        if field.in_bounds(x, y):
            glyphs[y][x] = (task.kind.value[0].lower(), "warn")

    for robot in sim.robots:
        x, y = robot.position
        if field.in_bounds(x, y):
            glyphs[y][x] = (robot.ICON, STATUS_STYLE.get(robot.status, "white") + " bold")

    body = Text()
    body.append("    " + "".join(str(x % 10) for x in range(field.width)) + "\n", style="muted")
    for y, line in enumerate(glyphs):
        body.append(f"{y:>3} ", style="muted")
        for char, style in line:
            body.append(char, style=style)
        body.append("\n")

    legend = Text()
    legend.append("S", style="accent"); legend.append("сеялка  ")
    legend.append("H", style="accent"); legend.append("комбайн  ")
    legend.append("E", style="accent"); legend.append("разведчик  ")
    legend.append("C", style="station"); legend.append("зарядка  ")
    legend.append("D", style="depot"); legend.append("ангар  ")
    legend.append("█", style="obstacle"); legend.append("препятствие")
    body.append(legend)
    return Panel(body, title="[title]Поле[/]", border_style="accent")


def render_robots(sim: Simulation) -> Panel:
    table = Table(expand=True, border_style="muted", header_style="title")
    table.add_column("ID", justify="right")
    table.add_column("Тип")
    table.add_column("Имя")
    table.add_column("Поз")
    table.add_column("Батарея")
    table.add_column("Износ")
    table.add_column("Статус")
    table.add_column("Задача", justify="center")
    table.add_column("Готово", justify="right")
    for r in sim.robots:
        table.add_row(
            str(r.id),
            r.kind_name,
            r.name,
            f"({r.x},{r.y})",
            _bar(r.battery, 100, "charging"),
            _bar(r.wear, 100, "danger"),
            Text(r.status.value, style=STATUS_STYLE.get(r.status, "white")),
            ("#" + str(r.task.id)) if r.task else "—",
            str(r.done_tasks),
        )
    return Panel(table, title="[title]Парк роботов[/]", border_style="accent")


def render_tasks(sim: Simulation, limit: int = 10) -> Panel:
    plan = sim.dispatcher.day_plan()
    if not plan:
        return Panel(Text("Очередь задач пуста.", style="muted"),
                     title="[title]План задач[/]", border_style="accent")
    table = Table(expand=True, border_style="muted", header_style="title")
    table.add_column("#", justify="right")
    table.add_column("Операция")
    table.add_column("Цель")
    table.add_column("Приор.", justify="center")
    table.add_column("Срок", justify="center")
    table.add_column("Статус")
    for t in plan[:limit]:
        style = TASK_STYLE.get(t.status, "white")
        table.add_row(
            str(t.id), t.kind.value, f"({t.x},{t.y})",
            f"P{t.priority}", f"д{t.deadline}",
            Text(t.status.value, style=style),
        )
    title = f"[title]План задач на день[/] [muted](всего {len(plan)})[/]"
    return Panel(table, title=title, border_style="accent")


def render_depot(sim: Simulation) -> Panel:
    table = Table(expand=True, border_style="muted", header_style="title")
    table.add_column("Деталь / расходник")
    table.add_column("Остаток", justify="right")
    for name, qty in sim.depot.catalog():
        style = "danger" if qty <= 2 else "ok"
        table.add_row(name, Text(str(qty), style=style))
    footer = Text(f"Ремонтов выполнено: {sim.depot.repairs_done}", style="muted")
    return Panel(Group(table, footer), title="[title]Склад (хэш-таблица)[/]",
                 border_style="accent")


def render_stats(sim: Simulation) -> Panel:
    s = sim.stats
    text = Text(justify="center")
    text.append(f"День {sim.day}  ·  тик {sim.tick}/{sim.ticks_per_day}", style="title")
    text.append("    выполнено: ", style="muted"); text.append(str(s.tasks_done), style="ok")
    text.append("   просрочено: ", style="muted"); text.append(str(s.tasks_failed), style="warn")
    text.append("   поломок: ", style="muted"); text.append(str(s.breakdowns), style="danger")
    text.append("   ремонтов: ", style="muted"); text.append(str(s.repairs), style="accent")
    text.append("   клеток пройдено: ", style="muted"); text.append(str(s.distance), style="moving")
    return Panel(text, border_style="title")


def render_log(sim: Simulation, n: int = 12) -> Panel:
    lines = sim.recent_log(n)
    text = Text("\n".join(lines) if lines else "—", style="muted")
    return Panel(text, title="[title]Журнал событий[/]", border_style="accent")


def render_dashboard(sim: Simulation) -> RenderableType:
    top = Columns([render_map(sim), render_tasks(sim)], expand=True, equal=True)
    return Group(
        Panel(Align.center(Text("AGROBOTS — автономное роботизированное агрохозяйство",
                                style="title")), border_style="title"),
        render_stats(sim),
        top,
        render_robots(sim),
        Columns([render_depot(sim), render_log(sim)], expand=True, equal=True),
    )


def show_dashboard(sim: Simulation) -> None:
    console.print(render_dashboard(sim))


def clear() -> None:
    console.clear()
