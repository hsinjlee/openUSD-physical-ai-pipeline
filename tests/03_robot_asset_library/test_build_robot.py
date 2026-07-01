"""Tests for 03_robot_asset_library/build_robot.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "03_robot_asset_library"))

import build_robot as br  # noqa: E402
from pxr import Usd, UsdGeom, Gf
import pytest


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Kind, Gf  # ImportError = test failure


def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_stage_up_axis_and_units(tmp_path):
    """Stage must use Y-up and metersPerUnit=1.0 (SI robot sim convention)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0


def test_robot_root_is_component_kind(tmp_path):
    """/Robot must be kind=component so downstream asset resolvers treat it as one asset."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    root = stage.GetPrimAtPath("/Robot")
    assert root.IsValid()
    assert root.GetMetadata("kind") == "component"


def test_link_hierarchy_exists(tmp_path):
    """Base and Arm links must exist as Xform prims under /Robot."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base = stage.GetPrimAtPath("/Robot/Base")
    arm = stage.GetPrimAtPath("/Robot/Arm")
    assert base.IsValid() and base.GetTypeName() == "Xform"
    assert arm.IsValid() and arm.GetTypeName() == "Xform"


def test_arm_link_is_translated_above_base(tmp_path):
    """Arm link must be offset above Base (visually distinct link positions)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    arm = UsdGeom.Xform(stage.GetPrimAtPath("/Robot/Arm"))
    translate, _, _, _, _ = UsdGeom.XformCommonAPI(arm).GetXformVectors(Usd.TimeCode.Default())
    assert translate == Gf.Vec3d(0.0, 1.0, 0.0)


def test_base_geom_exists(tmp_path):
    """Base link must have a child Cube prim named Geom."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    prim = stage.GetPrimAtPath("/Robot/Base/Geom")
    assert prim.IsValid()
    assert prim.GetTypeName() == "Cube"


def test_arm_geom_exists(tmp_path):
    """Arm link must have a child Cube prim named Geom, smaller than Base."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    prim = stage.GetPrimAtPath("/Robot/Arm/Geom")
    assert prim.IsValid()
    assert prim.GetTypeName() == "Cube"


def test_geom_sizes(tmp_path):
    """Base Cube must be larger than Arm Cube (visually distinct link scale)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base_cube = UsdGeom.Cube(stage.GetPrimAtPath("/Robot/Base/Geom"))
    arm_cube = UsdGeom.Cube(stage.GetPrimAtPath("/Robot/Arm/Geom"))
    assert base_cube.GetSizeAttr().Get() == pytest.approx(1.0)
    assert arm_cube.GetSizeAttr().Get() == pytest.approx(0.5)
