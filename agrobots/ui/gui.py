from __future__ import annotations

import tkinter as tk
from tkinter import messagebox, ttk
from typing import Optional, Tuple

from agrobots.core.simulation import Simulation
from agrobots.models.field import CellKind
from agrobots.models.robot import RobotStatus, build_robot
from agrobots.models.task import Task, TaskKind, TaskStatus
from agrobots.scenarios import build_default_sim

CELL = 42
PAD = 18

WIN_BG = "#16171f"
PANEL_BG = "#1e1f2b"
GRID_BG = "#11121a"
CELL_FREE = "#222433"
CELL_LINE = "#2c2f44"
OBSTACLE = "#3a3d52"
CHARGE = "#caa42a"
DEPOT = "#9b5cb5"
TEXT = "#e8e8f0"
MUTED = "#8b8fa3"
ACCENT = "#22b8cf"

STATUS_COLOR = {
    RobotStatus.IDLE: "#8b8fa3",
    RobotStatus.MOVING: "#22b8cf",
    RobotStatus.WORKING: "#51cf66",
    RobotStatus.CHARGING: "#fcc419",
    RobotStatus.SERVICE: "#cc5de8",
    RobotStatus.BROKEN: "#ff6b6b",
}

TASK_COLOR = {
    TaskStatus.PENDING: "#fcc419",
    TaskStatus.ASSIGNED: "#22b8cf",
    TaskStatus.IN_PROGRESS: "#74c0fc",
    TaskStatus.DONE: "#51cf66",
    TaskStatus.FAILED: "#ff6b6b",
}

ROBOT_KINDS = [
    ("seeder", "Сеялка"),
    ("harvester", "Комбайн"),
    ("scout", "Разведчик"),
]

TASK_KINDS = [
    (TaskKind.SEED, "Посев"),
    (TaskKind.HARVEST, "Сбор"),
    (TaskKind.INSPECT, "Осмотр"),
    (TaskKind.IRRIGATE, "Полив"),
]


def _battery_color(value: float) -> str:
    if value <= 25:
        return "#ff6b6b"
    if value <= 50:
        return "#fcc419"
    return "#51cf66"


def _add_row(parent, row: int, label: str, widget) -> None:
    tk.Label(parent, text=label, bg=PANEL_BG, fg=TEXT, anchor="w").grid(
        row=row, column=0, sticky="w", padx=(0, 10), pady=4
    )
    widget.grid(row=row, column=1, sticky="ew", pady=4)


class _Modal(tk.Toplevel):
    def __init__(self, parent: tk.Misc, title: str) -> None:
        super().__init__(parent)
        self.result = None
        self.title(title)
        self.configure(bg=PANEL_BG, padx=PAD, pady=PAD)
        self.resizable(False, False)
        self.transient(parent.winfo_toplevel())
        self.body = tk.Frame(self, bg=PANEL_BG)
        self.body.pack(fill="both", expand=True)
        self.body.columnconfigure(1, weight=1)

    def add_buttons(self) -> None:
        bar = tk.Frame(self, bg=PANEL_BG)
        bar.pack(fill="x", pady=(PAD, 0))
        ttk.Button(bar, text="Отмена", command=self.destroy).pack(side="right")
        ttk.Button(bar, text="ОК", command=self._submit).pack(
            side="right", padx=(0, 8)
        )
        self.bind("<Return>", lambda _e: self._submit())
        self.bind("<Escape>", lambda _e: self.destroy())

    def show(self):
        self.grab_set()
        self.wait_window()
        return self.result

    def _submit(self) -> None:
        raise NotImplementedError


class _RobotDialog(_Modal):
    def __init__(self, parent, sim: Simulation, default: Optional[Tuple[int, int]]):
        super().__init__(parent, "Новый робот")
        self.sim = sim
        self.kind = ttk.Combobox(
            self.body, values=[label for _k, label in ROBOT_KINDS], state="readonly"
        )
        self.kind.current(0)
        self.name = ttk.Entry(self.body)
        self.x = ttk.Spinbox(self.body, from_=0, to=sim.field.width - 1)
        self.y = ttk.Spinbox(self.body, from_=0, to=sim.field.height - 1)
        if default is not None:
            self.x.set(default[0])
            self.y.set(default[1])
        else:
            self.x.set(0)
            self.y.set(0)
        _add_row(self.body, 0, "Тип", self.kind)
        _add_row(self.body, 1, "Имя", self.name)
        _add_row(self.body, 2, "Координата X", self.x)
        _add_row(self.body, 3, "Координата Y", self.y)
        self.add_buttons()
        self.name.focus_set()

    def _submit(self) -> None:
        try:
            x, y = int(self.x.get()), int(self.y.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Координаты должны быть числами.", parent=self)
            return
        if not self.sim.field.passable(x, y):
            messagebox.showwarning("Ошибка", "Клетка занята или непроходима.", parent=self)
            return
        kind_key = ROBOT_KINDS[self.kind.current()][0]
        name = self.name.get().strip() or f"{kind_key}-{len(self.sim.robots) + 1}"
        self.result = (kind_key, name, x, y)
        self.destroy()


class _TaskDialog(_Modal):
    def __init__(self, parent, sim: Simulation, default: Optional[Tuple[int, int]]):
        super().__init__(parent, "Новый наряд")
        self.sim = sim
        self.kind = ttk.Combobox(
            self.body, values=[label for _k, label in TASK_KINDS], state="readonly"
        )
        self.kind.current(0)
        self.x = ttk.Spinbox(self.body, from_=0, to=sim.field.width - 1)
        self.y = ttk.Spinbox(self.body, from_=0, to=sim.field.height - 1)
        self.priority = ttk.Spinbox(self.body, from_=1, to=5)
        self.deadline = ttk.Spinbox(self.body, from_=1, to=99)
        self.duration = ttk.Spinbox(self.body, from_=1, to=20)
        if default is not None:
            self.x.set(default[0])
            self.y.set(default[1])
        else:
            self.x.set(0)
            self.y.set(0)
        self.priority.set(3)
        self.deadline.set(sim.day + 2)
        self.duration.set(2)
        _add_row(self.body, 0, "Операция", self.kind)
        _add_row(self.body, 1, "Координата X", self.x)
        _add_row(self.body, 2, "Координата Y", self.y)
        _add_row(self.body, 3, "Приоритет (1 — срочно)", self.priority)
        _add_row(self.body, 4, "Срок (день)", self.deadline)
        _add_row(self.body, 5, "Длительность (тиков)", self.duration)
        self.add_buttons()

    def _submit(self) -> None:
        try:
            x, y = int(self.x.get()), int(self.y.get())
            priority = int(self.priority.get())
            deadline = int(self.deadline.get())
            duration = int(self.duration.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Все поля должны быть числами.", parent=self)
            return
        if not self.sim.field.passable(x, y):
            messagebox.showwarning("Ошибка", "Цель непроходима.", parent=self)
            return
        kind = TASK_KINDS[self.kind.current()][0]
        self.result = Task(
            kind, x, y, priority=priority, deadline=deadline, duration=duration
        )
        self.destroy()


class _RestockDialog(_Modal):
    def __init__(self, parent, sim: Simulation):
        super().__init__(parent, "Пополнение склада")
        self.sim = sim
        names = [name for name, _qty in sim.depot.catalog()]
        self.part = ttk.Combobox(self.body, values=names)
        if names:
            self.part.current(0)
        self.qty = ttk.Spinbox(self.body, from_=1, to=999)
        self.qty.set(1)
        _add_row(self.body, 0, "Деталь / расходник", self.part)
        _add_row(self.body, 1, "Количество", self.qty)
        self.add_buttons()

    def _submit(self) -> None:
        name = self.part.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Укажите название детали.", parent=self)
            return
        try:
            qty = int(self.qty.get())
        except ValueError:
            messagebox.showwarning("Ошибка", "Количество должно быть числом.", parent=self)
            return
        self.result = (name, qty)
        self.destroy()


class _DaysDialog(_Modal):
    def __init__(self, parent):
        super().__init__(parent, "Прожить N дней")
        self.days = ttk.Spinbox(self.body, from_=1, to=365)
        self.days.set(3)
        _add_row(self.body, 0, "Сколько дней", self.days)
        self.add_buttons()
        self.days.focus_set()

    def _submit(self) -> None:
        try:
            self.result = max(1, int(self.days.get()))
        except ValueError:
            messagebox.showwarning("Ошибка", "Введите число.", parent=self)
            return
        self.destroy()


class AgroBotsGUI:
    def __init__(self, seed: int = 42) -> None:
        self.seed = seed
        self.sim = build_default_sim(seed=seed)
        self.auto = False
        self.selected: Optional[Tuple[int, int]] = None

        self.root = tk.Tk()
        self.root.title("AgroBots — автономное роботизированное агрохозяйство")
        self.root.configure(bg=WIN_BG)
        self.root.minsize(1180, 740)

        self._init_style()
        self._build_toolbar()
        self._build_stats()
        self._build_body()
        self._build_log()
        self.refresh()

    def _init_style(self) -> None:
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure(".", background=PANEL_BG, foreground=TEXT, fieldbackground=PANEL_BG)
        style.configure("TButton", padding=6, background="#2c2f44", foreground=TEXT)
        style.map("TButton", background=[("active", "#3b3f5c")])
        style.configure("Accent.TButton", background=ACCENT, foreground="#0b0c12")
        style.map("Accent.TButton", background=[("active", "#3bc9db")])
        style.configure(
            "Treeview",
            background="#262838",
            foreground=TEXT,
            fieldbackground="#262838",
            rowheight=24,
            borderwidth=0,
        )
        style.map("Treeview", background=[("selected", "#3b5bdb")])
        style.configure(
            "Treeview.Heading",
            background="#1e1f2b",
            foreground=ACCENT,
            relief="flat",
        )
        style.configure("TNotebook", background=WIN_BG, borderwidth=0)
        style.configure(
            "TNotebook.Tab", background="#1e1f2b", foreground=MUTED, padding=(14, 6)
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", "#2c2f44")],
            foreground=[("selected", TEXT)],
        )
        style.configure("TCombobox", fieldbackground="#262838", foreground=TEXT)
        style.configure("TSpinbox", fieldbackground="#262838", foreground=TEXT)
        style.configure("TEntry", fieldbackground="#262838", foreground=TEXT)
        style.configure("Horizontal.TScale", background=PANEL_BG)

    def _build_toolbar(self) -> None:
        bar = tk.Frame(self.root, bg=PANEL_BG, padx=PAD, pady=10)
        bar.pack(fill="x")
        buttons = [
            ("▶ Тик", self.do_step),
            ("⏩ День", self.do_day),
            ("📅 N дней", self.do_days),
        ]
        for text, cmd in buttons:
            ttk.Button(bar, text=text, command=cmd).pack(side="left", padx=(0, 6))

        self.auto_btn = ttk.Button(bar, text="⟳ Автопрогон", command=self.toggle_auto,
                                   style="Accent.TButton")
        self.auto_btn.pack(side="left", padx=(0, 6))

        tk.Label(bar, text="скорость", bg=PANEL_BG, fg=MUTED).pack(side="left", padx=(10, 4))
        self.speed = tk.Scale(
            bar, from_=1, to=10, orient="horizontal", length=120, showvalue=False,
            bg=PANEL_BG, fg=TEXT, highlightthickness=0, troughcolor="#11121a",
            activebackground=ACCENT,
        )
        self.speed.set(4)
        self.speed.pack(side="left")

        for text, cmd in [
            ("➕ Робот", self.do_add_robot),
            ("📋 Наряд", self.do_add_task),
            ("📦 Склад", self.do_restock),
            ("↺ Сброс", self.do_reset),
        ]:
            ttk.Button(bar, text=text, command=cmd).pack(side="right", padx=(6, 0))

    def _build_stats(self) -> None:
        self.stats_var = tk.StringVar()
        tk.Label(
            self.root, textvariable=self.stats_var, bg="#11121a", fg=TEXT,
            font=("Consolas", 11), pady=8, anchor="w", padx=PAD,
        ).pack(fill="x")

    def _build_body(self) -> None:
        body = tk.Frame(self.root, bg=WIN_BG)
        body.pack(fill="both", expand=True, padx=PAD, pady=(10, 0))

        left = tk.Frame(body, bg=PANEL_BG)
        left.pack(side="left", fill="y")
        self.canvas = tk.Canvas(
            left,
            width=self.sim.field.width * CELL + 60,
            height=self.sim.field.height * CELL + 30,
            bg=GRID_BG, highlightthickness=0,
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind("<Button-1>", self._on_canvas_click)
        self._build_legend(left)

        right = tk.Frame(body, bg=WIN_BG)
        right.pack(side="left", fill="both", expand=True, padx=(PAD, 0))
        notebook = ttk.Notebook(right)
        notebook.pack(fill="both", expand=True)

        self.robots_tree = self._make_tree(
            notebook,
            ("id", "type", "name", "pos", "bat", "wear", "status", "task", "done"),
            ("ID", "Тип", "Имя", "Поз", "Батарея", "Износ", "Статус", "Наряд", "Готово"),
            (36, 90, 110, 60, 70, 60, 90, 60, 60),
        )
        notebook.add(self.robots_tree.master, text="Роботы")

        self.tasks_tree = self._make_tree(
            notebook,
            ("id", "op", "target", "prio", "deadline", "status"),
            ("#", "Операция", "Цель", "Приор.", "Срок", "Статус"),
            (40, 110, 80, 70, 70, 110),
        )
        notebook.add(self.tasks_tree.master, text="Наряды")

        self.depot_tree = self._make_tree(
            notebook, ("part", "qty"), ("Деталь / расходник", "Остаток"), (220, 100)
        )
        notebook.add(self.depot_tree.master, text="Склад")

    def _make_tree(self, parent, columns, headings, widths) -> ttk.Treeview:
        holder = tk.Frame(parent, bg=PANEL_BG)
        tree = ttk.Treeview(holder, columns=columns, show="headings", selectmode="none")
        for col, head, width in zip(columns, headings, widths):
            tree.heading(col, text=head)
            tree.column(col, width=width, anchor="center")
        scroll = ttk.Scrollbar(holder, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scroll.set)
        tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        for status, color in STATUS_COLOR.items():
            tree.tag_configure(status.name, foreground=color)
        for status, color in TASK_COLOR.items():
            tree.tag_configure("T_" + status.name, foreground=color)
        return tree

    def _build_legend(self, parent) -> None:
        legend = tk.Frame(parent, bg=PANEL_BG)
        legend.pack(fill="x", padx=10, pady=(0, 10))
        items = [
            ("S сеялка", STATUS_COLOR[RobotStatus.MOVING]),
            ("H комбайн", STATUS_COLOR[RobotStatus.WORKING]),
            ("E разведчик", ACCENT),
            ("C зарядка", CHARGE),
            ("D ангар", DEPOT),
            ("■ препятствие", OBSTACLE),
        ]
        for text, color in items:
            tk.Label(legend, text=text, bg=PANEL_BG, fg=color,
                     font=("Segoe UI", 9)).pack(side="left", padx=(0, 12))

    def _build_log(self) -> None:
        frame = tk.Frame(self.root, bg=PANEL_BG)
        frame.pack(fill="both", padx=PAD, pady=(10, PAD))
        tk.Label(frame, text="Журнал событий", bg=PANEL_BG, fg=ACCENT,
                 anchor="w", padx=8, pady=4).pack(fill="x")
        self.log = tk.Text(
            frame, height=8, bg="#11121a", fg=MUTED, insertbackground=TEXT,
            relief="flat", font=("Consolas", 10), wrap="none",
        )
        self.log.pack(fill="both", expand=True, padx=2, pady=(0, 2))
        self.log.configure(state="disabled")

    def _cell_at(self, px: int, py: int) -> Optional[Tuple[int, int]]:
        x = (px - 30) // CELL
        y = (py - 20) // CELL
        if self.sim.field.in_bounds(x, y):
            return (x, y)
        return None

    def _on_canvas_click(self, event) -> None:
        cell = self._cell_at(event.x, event.y)
        if cell is not None:
            self.selected = cell
            self.refresh()

    def _draw_field(self) -> None:
        c = self.canvas
        c.delete("all")
        field = self.sim.field
        for x in range(field.width):
            c.create_text(30 + x * CELL + CELL // 2, 10, text=str(x % 10),
                          fill=MUTED, font=("Consolas", 9))
        for y in range(field.height):
            c.create_text(14, 20 + y * CELL + CELL // 2, text=str(y),
                          fill=MUTED, font=("Consolas", 9))
            for x in range(field.width):
                cell = field.grid[y][x]
                fill = CELL_FREE
                if cell.kind is CellKind.OBSTACLE:
                    fill = OBSTACLE
                elif cell.kind is CellKind.CHARGE:
                    fill = CHARGE
                elif cell.kind is CellKind.DEPOT:
                    fill = DEPOT
                x0, y0 = 30 + x * CELL, 20 + y * CELL
                c.create_rectangle(x0, y0, x0 + CELL, y0 + CELL,
                                   fill=fill, outline=CELL_LINE)
                if cell.kind is CellKind.CHARGE:
                    c.create_text(x0 + CELL // 2, y0 + CELL // 2, text="C",
                                  fill="#0b0c12", font=("Segoe UI", 13, "bold"))
                elif cell.kind is CellKind.DEPOT:
                    c.create_text(x0 + CELL // 2, y0 + CELL // 2, text="D",
                                  fill="#0b0c12", font=("Segoe UI", 13, "bold"))

        if self.selected is not None:
            sx, sy = self.selected
            x0, y0 = 30 + sx * CELL, 20 + sy * CELL
            c.create_rectangle(x0 + 1, y0 + 1, x0 + CELL - 1, y0 + CELL - 1,
                               outline=ACCENT, width=2)

        for robot in self.sim.robots:
            self._draw_path(robot)
        for task in self.sim.dispatcher.pending:
            self._draw_task(task)
        for robot in self.sim.robots:
            self._draw_robot(robot)

    def _draw_path(self, robot) -> None:
        if not robot.path:
            return
        color = STATUS_COLOR.get(robot.status, MUTED)
        points = [robot.position] + list(robot.path)
        coords = []
        for x, y in points:
            coords.append(30 + x * CELL + CELL // 2)
            coords.append(20 + y * CELL + CELL // 2)
        if len(coords) >= 4:
            self.canvas.create_line(*coords, fill=color, width=2, dash=(2, 4))

    def _draw_task(self, task) -> None:
        x, y = task.target
        if not self.sim.field.in_bounds(x, y):
            return
        x0, y0 = 30 + x * CELL, 20 + y * CELL
        color = TASK_COLOR.get(task.status, "#fcc419")
        self.canvas.create_rectangle(
            x0 + 6, y0 + 6, x0 + CELL - 6, y0 + CELL - 6,
            outline=color, width=2,
        )
        self.canvas.create_text(x0 + CELL // 2, y0 + CELL // 2,
                                text=task.kind.value[0].upper(), fill=color,
                                font=("Segoe UI", 11, "bold"))

    def _draw_robot(self, robot) -> None:
        x, y = robot.position
        if not self.sim.field.in_bounds(x, y):
            return
        x0, y0 = 30 + x * CELL, 20 + y * CELL
        color = STATUS_COLOR.get(robot.status, "#8b8fa3")
        m = 7
        self.canvas.create_oval(x0 + m, y0 + m, x0 + CELL - m, y0 + CELL - m,
                                fill=color, outline="#0b0c12", width=2)
        self.canvas.create_text(x0 + CELL // 2, y0 + CELL // 2 - 2, text=robot.ICON,
                                fill="#0b0c12", font=("Segoe UI", 12, "bold"))
        bw = CELL - 10
        bx, by = x0 + 5, y0 + CELL - 6
        filled = int(bw * robot.battery / 100.0)
        self.canvas.create_rectangle(bx, by, bx + bw, by + 3, fill="#11121a", outline="")
        self.canvas.create_rectangle(bx, by, bx + filled, by + 3,
                                    fill=_battery_color(robot.battery), outline="")

    def _refresh_stats(self) -> None:
        s = self.sim.stats
        self.stats_var.set(
            f"День {self.sim.day}   тик {self.sim.tick}/{self.sim.ticks_per_day}      "
            f"выполнено: {s.tasks_done}    просрочено: {s.tasks_failed}    "
            f"поломок: {s.breakdowns}    ремонтов: {s.repairs}    "
            f"пройдено клеток: {s.distance}    "
            f"роботов: {len(self.sim.robots)}    в очереди: {len(self.sim.dispatcher)}"
        )

    def _refresh_robots(self) -> None:
        tree = self.robots_tree
        tree.delete(*tree.get_children())
        for r in self.sim.robots:
            tree.insert(
                "", "end",
                values=(
                    r.id, r.kind_name, r.name, f"({r.x},{r.y})",
                    f"{r.battery:.0f}%", f"{r.wear:.0f}%", r.status.value,
                    ("#" + str(r.task.id)) if r.task else "—", r.done_tasks,
                ),
                tags=(r.status.name,),
            )

    def _refresh_tasks(self) -> None:
        tree = self.tasks_tree
        tree.delete(*tree.get_children())
        for t in self.sim.dispatcher.day_plan():
            tree.insert(
                "", "end",
                values=(
                    t.id, t.kind.value, f"({t.x},{t.y})",
                    f"P{t.priority}", f"д{t.deadline}", t.status.value,
                ),
                tags=("T_" + t.status.name,),
            )

    def _refresh_depot(self) -> None:
        tree = self.depot_tree
        tree.delete(*tree.get_children())
        for name, qty in self.sim.depot.catalog():
            tag = "T_FAILED" if qty <= 2 else "T_DONE"
            tree.insert("", "end", values=(name, qty), tags=(tag,))

    def _refresh_log(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.insert("1.0", "\n".join(self.sim.recent_log(60)))
        self.log.see("end")
        self.log.configure(state="disabled")

    def refresh(self) -> None:
        self._draw_field()
        self._refresh_stats()
        self._refresh_robots()
        self._refresh_tasks()
        self._refresh_depot()
        self._refresh_log()

    def do_step(self) -> None:
        self.sim.step()
        self.refresh()

    def do_day(self) -> None:
        self.sim.run_day()
        self.refresh()

    def do_days(self) -> None:
        days = _DaysDialog(self.root).show()
        if days:
            self.sim.run_days(days)
            self.refresh()

    def toggle_auto(self) -> None:
        self.auto = not self.auto
        self.auto_btn.configure(text="⏸ Стоп" if self.auto else "⟳ Автопрогон")
        if self.auto:
            self._auto_tick()

    def _auto_tick(self) -> None:
        if not self.auto:
            return
        self.sim.step()
        self.refresh()
        delay = int(1100 / self.speed.get())
        self.root.after(delay, self._auto_tick)

    def do_add_robot(self) -> None:
        data = _RobotDialog(self.root, self.sim, self.selected).show()
        if data is None:
            return
        kind, name, x, y = data
        try:
            robot = build_robot(kind, name, x, y)
        except ValueError as exc:
            messagebox.showwarning("Ошибка", str(exc))
            return
        self.sim.add_robot(robot)
        self.refresh()

    def do_add_task(self) -> None:
        task = _TaskDialog(self.root, self.sim, self.selected).show()
        if task is not None:
            self.sim.add_task(task)
            self.refresh()

    def do_restock(self) -> None:
        data = _RestockDialog(self.root, self.sim).show()
        if data is not None:
            name, qty = data
            self.sim.depot.restock(name, qty)
            self.refresh()

    def do_reset(self) -> None:
        if not messagebox.askyesno("Сброс", "Перезапустить симуляцию с начала?"):
            return
        self.auto = False
        self.auto_btn.configure(text="⟳ Автопрогон")
        self.sim = build_default_sim(seed=self.seed)
        self.selected = None
        self.refresh()

    def run(self) -> None:
        self.root.mainloop()


def run_gui(seed: int = 42) -> None:
    AgroBotsGUI(seed=seed).run()
