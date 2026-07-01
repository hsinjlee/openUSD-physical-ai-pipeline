"""Tests for 03_robot_asset_library/build_robot.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "03_robot_asset_library"))

import build_robot as br  # noqa: E402


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Kind, Gf  # ImportError = test failure
