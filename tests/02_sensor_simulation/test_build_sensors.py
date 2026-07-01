"""Tests for 02_sensor_simulation/build_sensors.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))

import build_sensors as bs  # noqa: E402


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, Sdf  # ImportError = test failure
