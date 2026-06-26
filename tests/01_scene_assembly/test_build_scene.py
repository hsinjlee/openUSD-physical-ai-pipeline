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
