"""Tests for 02_sensor_simulation/build_sensors.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))

import build_sensors as bs  # noqa: E402
from pxr import UsdGeom


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, Sdf  # ImportError = test failure


def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_stage_up_axis_and_units(tmp_path):
    """Stage must use Y-up and metersPerUnit=1.0 (SI robot sim convention)."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
