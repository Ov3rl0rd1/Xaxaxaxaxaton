from __future__ import annotations

import argparse

from agrobots.app import run
from agrobots.scenarios import build_default_sim
from agrobots.ui import console as view
from agrobots.ui.theme import console, init_terminal


def _demo(days: int, seed: int) -> None:
    init_terminal()
    console.rule(f"[title]Демонстрация: {days} дн., seed={seed}[/]")
    sim = build_default_sim(seed=seed)
    sim.run_days(days)
    view.show_dashboard(sim)
    s = sim.stats
    console.print(
        f"\n[ok bold]ИТОГ за {days} дн.:[/] выполнено {s.tasks_done}, "
        f"просрочено {s.tasks_failed}, поломок {s.breakdowns}, "
        f"ремонтов {s.repairs}, пройдено {s.distance} клеток."
    )


def main() -> None:
    parser = argparse.ArgumentParser(prog="agrobots", description="Симулятор агророботов")
    parser.add_argument("--demo", nargs="?", const=3, type=int, default=None, metavar="N")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    if args.demo is not None:
        _demo(args.demo, args.seed)
    else:
        run(seed=args.seed)


if __name__ == "__main__":
    main()
