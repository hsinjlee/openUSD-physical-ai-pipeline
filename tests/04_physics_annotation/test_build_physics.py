"""Tests for 04_physics_annotation/build_physics.py."""
import os
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "04_physics_annotation"))

import build_physics as bp  # noqa: E402
from pxr import Usd, UsdPhysics, Sdf, Gf
import pytest


@pytest.fixture(autouse=True)
def _isolated_robot_asset(tmp_path, monkeypatch):
    """Keep tests hermetic: build 03's base asset into tmp instead of
    rewriting the git-tracked 03_robot_asset_library/output/robot.usda."""
    monkeypatch.setattr(bp, "ROBOT_USDA", str(tmp_path / "robot.usda"))


def test_pxr_physics_imports():
    """Confirm usd-core ships UsdPhysics (needed by every other test here)."""
    from pxr import UsdPhysics  # ImportError = test failure


def test_overlay_sublayers_robot_asset(tmp_path):
    """The overlay's root layer must sublayer 03's robot.usda, not copy it."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    sublayers = list(stage.GetRootLayer().subLayerPaths)
    assert len(sublayers) == 1
    assert sublayers[0].endswith("robot.usda")
    assert not os.path.isabs(sublayers[0]), "sublayer path must be relative"


def test_overlay_has_default_prim(tmp_path):
    """Overlay stage metadata must declare defaultPrim=Robot (repo USD rule)."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    assert stage.GetDefaultPrim().GetPath() == Sdf.Path("/Robot")


def test_composed_stage_exposes_robot_links(tmp_path):
    """Composition must surface 03's link hierarchy through the sublayer arc."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    for path in ("/Robot", "/Robot/Base", "/Robot/Arm",
                 "/Robot/Base/Geom", "/Robot/Arm/Geom"):
        assert stage.GetPrimAtPath(path).IsValid(), f"{path} missing from composition"


def test_links_are_rigid_bodies(tmp_path):
    """Base and Arm must carry RigidBodyAPI — joints only act on rigid bodies."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    for link in ("/Robot/Base", "/Robot/Arm"):
        assert stage.GetPrimAtPath(link).HasAPI(UsdPhysics.RigidBodyAPI), link


def test_link_masses(tmp_path):
    """MassAPI must author explicit masses: Base 10 kg, Arm 2 kg."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    expected = {"/Robot/Base": 10.0, "/Robot/Arm": 2.0}
    for link, mass in expected.items():
        prim = stage.GetPrimAtPath(link)
        assert prim.HasAPI(UsdPhysics.MassAPI), link
        assert UsdPhysics.MassAPI(prim).GetMassAttr().Get() == mass
