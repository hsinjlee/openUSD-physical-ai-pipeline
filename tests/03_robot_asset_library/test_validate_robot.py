"""Integration test: generated robot.usda must pass usdchecker with zero errors."""
import sys
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "03_robot_asset_library"
sys.path.insert(0, str(MODULE_DIR))

import build_robot as br  # noqa: E402 — depends on sys.path.insert above


def test_validate_robot_exits_zero(tmp_path):
    """validate_robot.py must exit 0 when the generated robot asset is valid."""
    out = str(tmp_path / "robot.usda")
    br.build_robot(out)

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_robot.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_robot.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
