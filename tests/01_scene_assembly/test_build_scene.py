"""Tests for 01_scene_assembly/build_scene.py."""
import importlib
import sys
import os

import pytest
from pxr import Usd, UsdGeom, Sdf

# Allow importing the module under test
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


def test_pxr_imports():
    """Confirm usd-core is installed and pxr is importable."""
    assert Usd is not None
    assert UsdGeom is not None
    assert Sdf is not None
