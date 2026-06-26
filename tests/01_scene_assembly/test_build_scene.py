"""Tests for 01_scene_assembly/build_scene.py."""
import sys
import os

import pytest
from pxr import Usd, UsdGeom, Sdf

# Allow importing the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "01_scene_assembly"))

import build_scene as bs   # relies on sys.path.insert above


def test_pxr_imports():
    """Confirm usd-core is installed and pxr is importable."""
    assert Usd is not None
    assert UsdGeom is not None
    assert Sdf is not None


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
