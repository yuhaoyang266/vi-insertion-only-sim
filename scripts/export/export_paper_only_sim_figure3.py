from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    delegate_path = (
        Path(__file__).resolve().parent
        / "export_paper_only_sim_high_friction_trace_figure.py"
    )
    runpy.run_path(str(delegate_path), run_name="__main__")


if __name__ == "__main__":
    main()
