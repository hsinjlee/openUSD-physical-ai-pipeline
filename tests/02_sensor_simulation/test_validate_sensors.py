"""Integration test: generated sensor_rig.usda must pass usdchecker with zero errors."""
import sys
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "02_sensor_simulation"
sys.path.insert(0, str(MODULE_DIR))

import build_sensors as bs  # noqa: E402 — depends on sys.path.insert above


def test_validate_sensors_exits_zero(tmp_path):
    """validate_sensors.py must exit 0 when the generated sensor rig is valid."""
    out = str(tmp_path / "sensor_rig.usda")
    bs.build_sensors(out)

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_sensors.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_sensors.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
