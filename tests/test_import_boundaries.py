from __future__ import annotations

import subprocess
import sys
import os
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_import_vi_full_is_lightweight() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "import vi_full; "
                "print(vi_full.__version__); "
                "print('stable_baselines3' in sys.modules); "
                "print('mujoco' in sys.modules)"
            ),
        ],
        check=True,
        capture_output=True,
        env={**os.environ, "PYTHONPATH": str(REPO_ROOT / "src")},
        text=True,
    )

    assert "Gym has been unmaintained" not in completed.stderr
    assert completed.stdout.splitlines() == ["0.1.0", "False", "False"]
