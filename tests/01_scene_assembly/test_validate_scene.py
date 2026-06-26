"""Integration test: generated scene.usda must pass usdchecker with zero errors."""
import os
import sys
import shutil
import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "01_scene_assembly"
sys.path.insert(0, str(MODULE_DIR))


def test_validate_scene_exits_zero(tmp_path):
    """validate_scene.py must exit 0 when the generated scene is valid."""
    # Build the scene into tmp_path
    import build_scene as bs
    stub_src = MODULE_DIR / "robot_stub.usda"
    shutil.copy(stub_src, tmp_path / "robot_stub.usda")
    out = str(tmp_path / "scene.usda")
    bs.build_scene(out, robot_stub_path=str(tmp_path / "robot_stub.usda"))

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_scene.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_scene.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
