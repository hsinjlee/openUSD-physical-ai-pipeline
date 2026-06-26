"""Tests for 01_scene_assembly/build_scene.py."""
import sys
import shutil
import pathlib

# Allow importing the module under test
sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "01_scene_assembly"))

import build_scene as bs  # noqa: E402 — depends on sys.path.insert above


def test_pxr_imports():
    """Confirm usd-core is installed and pxr modules are importable."""
    from pxr import Usd, UsdGeom, Sdf  # ImportError here = test failure


def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_ground_plane_exists(tmp_path):
    """Scene must contain a Mesh prim named GroundPlane under /World."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    prim = stage.GetPrimAtPath("/World/GroundPlane")
    assert prim.IsValid(), "/World/GroundPlane prim not found"
    assert prim.GetTypeName() == "Mesh", "GroundPlane must be a Mesh"


def test_environment_variantset(tmp_path):
    """Root prim must have an 'environment' VariantSet with 'indoor' and 'outdoor' variants."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    root = stage.GetPrimAtPath("/World")
    vsets = root.GetVariantSets()
    assert vsets.HasVariantSet("environment"), "'environment' VariantSet missing"
    vset = vsets.GetVariantSet("environment")
    names = vset.GetVariantNames()
    assert "indoor" in names, "'indoor' variant missing"
    assert "outdoor" in names, "'outdoor' variant missing"


def test_environment_default_variant(tmp_path):
    """Default selection for 'environment' VariantSet must be 'indoor'."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    root = stage.GetPrimAtPath("/World")
    vset = root.GetVariantSets().GetVariantSet("environment")
    assert vset.GetVariantSelection() == "indoor", "default 'environment' selection must be 'indoor'"


def test_robot_reference_exists(tmp_path):
    """Scene must have a /World/Robot prim populated via a reference."""
    # Copy robot_stub.usda next to the output so the reference resolves
    stub_src = pathlib.Path(__file__).parents[2] / "01_scene_assembly" / "robot_stub.usda"
    shutil.copy(stub_src, tmp_path / "robot_stub.usda")

    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out, robot_stub_path=str(tmp_path / "robot_stub.usda"))
    robot = stage.GetPrimAtPath("/World/Robot")
    assert robot.IsValid(), "/World/Robot not found"
    base = stage.GetPrimAtPath("/World/Robot/Base")
    assert base.IsValid(), "/World/Robot/Base not found (reference not composed)"
