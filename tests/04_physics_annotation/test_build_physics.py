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


def test_geoms_have_collision(tmp_path):
    """CollisionAPI goes on the Geom shape prims — 03 separated Geom from the
    link Xform precisely so collision attaches without touching transforms."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    for geom in ("/Robot/Base/Geom", "/Robot/Arm/Geom"):
        assert stage.GetPrimAtPath(geom).HasAPI(UsdPhysics.CollisionAPI), geom


def test_robot_is_articulation_root(tmp_path):
    """/Robot must carry ArticulationRootAPI so the joint chain solves as one
    articulation (how Isaac Sim ingests robots)."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    assert stage.GetPrimAtPath("/Robot").HasAPI(UsdPhysics.ArticulationRootAPI)


def test_fixed_base_joint_anchors_robot_to_world(tmp_path):
    """FixedJoint with body1=Base and no body0 welds the robot to the world
    frame so it doesn't fall under gravity."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    joint = UsdPhysics.FixedJoint(stage.GetPrimAtPath("/Robot/FixedBaseJoint"))
    assert joint
    assert joint.GetBody1Rel().GetTargets() == [Sdf.Path("/Robot/Base")]
    assert joint.GetBody0Rel().GetTargets() == []


def test_arm_joint_connects_base_to_arm(tmp_path):
    """RevoluteJoint body0/body1 define the parent→child kinematic pair —
    the USD equivalent of a URDF <joint><parent/><child/>."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/Robot/ArmJoint"))
    assert joint
    assert joint.GetBody0Rel().GetTargets() == [Sdf.Path("/Robot/Base")]
    assert joint.GetBody1Rel().GetTargets() == [Sdf.Path("/Robot/Arm")]


def test_arm_joint_axis_and_limits(tmp_path):
    """Z-axis revolute with ±90° limits (UsdPhysics limits are degrees)."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/Robot/ArmJoint"))
    assert joint.GetAxisAttr().Get() == "Z"
    assert joint.GetLowerLimitAttr().Get() == -90.0
    assert joint.GetUpperLimitAttr().Get() == 90.0


def test_arm_joint_local_anchors(tmp_path):
    """Anchor at the Arm cube's bottom face (world y=0.75), expressed in each
    body's local frame: Base at origin → (0, 0.75, 0); Arm at y=1 → (0, -0.25, 0)."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    joint = UsdPhysics.RevoluteJoint(stage.GetPrimAtPath("/Robot/ArmJoint"))
    assert joint.GetLocalPos0Attr().Get() == Gf.Vec3f(0.0, 0.75, 0.0)
    assert joint.GetLocalPos1Attr().Get() == Gf.Vec3f(0.0, -0.25, 0.0)
