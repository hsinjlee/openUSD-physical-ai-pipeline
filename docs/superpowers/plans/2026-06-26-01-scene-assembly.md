# 01_scene_assembly Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a USD scene that demonstrates LIVRPS layer composition, VariantSets for environment switching, correct `defaultPrim` metadata, and passes `usdchecker` with zero errors.

**Architecture:** Two scripts — `build_scene.py` generates a `.usda` file with a composed scene (root Xform, environment VariantSet, a referenced robot stub, and a ground plane), and `validate_scene.py` runs `usdchecker` programmatically and asserts zero errors. Tests live in `tests/01_scene_assembly/` and use `pytest`.

**Tech Stack:** Python 3.10+, `usd-core` (pxr), `pytest`, `usdchecker` (bundled with usd-core)

---

## File Map

| Path | Role |
|---|---|
| `01_scene_assembly/build_scene.py` | Generates `01_scene_assembly/output/scene.usda` |
| `01_scene_assembly/validate_scene.py` | Runs usdchecker; exits non-zero on any error |
| `01_scene_assembly/output/scene.usda` | Generated artifact (committed as human-readable diff) |
| `tests/01_scene_assembly/__init__.py` | Empty — makes pytest discover the package |
| `tests/01_scene_assembly/test_build_scene.py` | Unit tests: stage structure, VariantSet, defaultPrim |
| `tests/01_scene_assembly/test_validate_scene.py` | Integration test: usdchecker reports zero errors |

---

## Task 1: Test infrastructure and imports

**Files:**
- Create: `tests/__init__.py`
- Create: `tests/01_scene_assembly/__init__.py`
- Create: `tests/01_scene_assembly/test_build_scene.py`

- [ ] **Step 1: Create empty `__init__.py` files**

```bash
touch tests/__init__.py tests/01_scene_assembly/__init__.py
```

- [ ] **Step 2: Write the first failing test — verify pxr imports work**

Create `tests/01_scene_assembly/test_build_scene.py`:

```python
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
```

- [ ] **Step 3: Run test to verify it passes (environment check)**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/01_scene_assembly/test_build_scene.py::test_pxr_imports -v
```

Expected: PASS — if it fails, run `pip install usd-core` first.

- [ ] **Step 4: Commit**

```bash
git add tests/__init__.py tests/01_scene_assembly/__init__.py tests/01_scene_assembly/test_build_scene.py
git commit -m "test: scaffold 01_scene_assembly test package"
```

---

## Task 2: `build_scene.py` — stage skeleton with defaultPrim

**Files:**
- Create: `01_scene_assembly/build_scene.py`
- Create: `01_scene_assembly/output/.gitkeep`

- [ ] **Step 1: Write failing test for stage creation**

Append to `tests/01_scene_assembly/test_build_scene.py`:

```python
import build_scene as bs   # import after sys.path.insert above


def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"
```

- [ ] **Step 2: Run to confirm it fails**

```bash
pytest tests/01_scene_assembly/test_build_scene.py::test_stage_has_default_prim -v
```

Expected: `ModuleNotFoundError: No module named 'build_scene'`

- [ ] **Step 3: Create minimal `build_scene.py`**

Create `01_scene_assembly/build_scene.py`:

```python
"""
build_scene.py — generates a USD scene demonstrating LIVRPS composition.

Physical AI purpose:
  A well-composed USD stage is the foundation for robot simulation pipelines.
  LIVRPS (Local, Inherits, VariantSets, References, Payloads, Specializes) defines
  opinion strength ordering; understanding it is required for multi-asset robot scenes.
"""
import os
from pxr import Usd, UsdGeom, Sdf


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_scene(output_path: str) -> Usd.Stage:
    """Create and save a USD scene; return the open stage."""
    stage = Usd.Stage.CreateNew(output_path)

    # Root Xform — becomes defaultPrim
    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())

    # Required stage metadata
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "scene.usda")
    build_scene(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run test to confirm it passes**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py::test_stage_has_default_prim -v && cd ..
```

Expected: PASS

- [ ] **Step 5: Create output placeholder**

```bash
mkdir -p 01_scene_assembly/output
touch 01_scene_assembly/output/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add 01_scene_assembly/build_scene.py 01_scene_assembly/output/.gitkeep tests/01_scene_assembly/test_build_scene.py
git commit -m "feat: add build_scene skeleton with defaultPrim and stage metadata"
```

---

## Task 3: Ground plane prim

**Files:**
- Modify: `01_scene_assembly/build_scene.py`
- Modify: `tests/01_scene_assembly/test_build_scene.py`

- [ ] **Step 1: Write failing test**

Append to `tests/01_scene_assembly/test_build_scene.py`:

```python
def test_ground_plane_exists(tmp_path):
    """Scene must contain a Mesh prim named GroundPlane under /World."""
    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out)
    prim = stage.GetPrimAtPath("/World/GroundPlane")
    assert prim.IsValid(), "/World/GroundPlane prim not found"
    assert prim.GetTypeName() == "Mesh", "GroundPlane must be a Mesh"
```

- [ ] **Step 2: Run to confirm it fails**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py::test_ground_plane_exists -v && cd ..
```

Expected: FAIL — `AssertionError: /World/GroundPlane prim not found`

- [ ] **Step 3: Add ground plane to `build_scene.py`**

In `build_scene.py`, import `UsdGeom` (already imported) and add inside `build_scene()` before `stage.Save()`:

```python
    # Ground plane — a flat quad Mesh representing the floor in robot environments
    from pxr import UsdGeom as _UsdGeom
    ground = _UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
    ground.CreatePointsAttr([(-5,0,-5),(5,0,-5),(5,0,5),(-5,0,5)])
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0,1,2,3])
    ground.CreateExtentAttr([(-5,0,-5),(5,0,5)])
```

Replace that with a clean edit — full updated `build_scene()` function body:

```python
def build_scene(output_path: str) -> Usd.Stage:
    """Create and save a USD scene; return the open stage."""
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Ground plane — flat quad Mesh for robot floor collision reference
    ground = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
    ground.CreatePointsAttr([(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)])
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    ground.CreateExtentAttr([(-5, 0, -5), (5, 0, 5)])

    stage.Save()
    return stage
```

- [ ] **Step 4: Run tests**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py -v && cd ..
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add 01_scene_assembly/build_scene.py tests/01_scene_assembly/test_build_scene.py
git commit -m "feat: add GroundPlane Mesh prim to scene"
```

---

## Task 4: VariantSet for environment switching

**Files:**
- Modify: `01_scene_assembly/build_scene.py`
- Modify: `tests/01_scene_assembly/test_build_scene.py`

- [ ] **Step 1: Write failing test**

Append to `tests/01_scene_assembly/test_build_scene.py`:

```python
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
    assert vset.GetVariantSelection() == "indoor"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py::test_environment_variantset ../tests/01_scene_assembly/test_build_scene.py::test_environment_default_variant -v && cd ..
```

Expected: both FAIL

- [ ] **Step 3: Add VariantSet to `build_scene.py`**

Add after the ground plane block, before `stage.Save()`:

```python
    # VariantSet: environment — switches between indoor/outdoor robot contexts.
    # Physical AI use: swap lighting, obstacle sets, and floor materials per environment
    # without duplicating the full scene graph.
    vsets = root.GetPrim().GetVariantSets()
    env_vset = vsets.AddVariantSet("environment")

    env_vset.AddVariant("indoor")
    env_vset.SetVariantSelection("indoor")
    with env_vset.GetVariantEditContext():
        # Indoor variant: add a ceiling plane
        ceiling = UsdGeom.Mesh.Define(stage, "/World/Ceiling")
        ceiling.CreatePointsAttr([(-5, 3, -5), (5, 3, -5), (5, 3, 5), (-5, 3, 5)])
        ceiling.CreateFaceVertexCountsAttr([4])
        ceiling.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
        ceiling.CreateExtentAttr([(-5, 3, -5), (5, 3, 5)])

    env_vset.AddVariant("outdoor")
    # Outdoor variant is intentionally empty — open sky, no ceiling
    env_vset.SetVariantSelection("indoor")  # default selection
```

- [ ] **Step 4: Run all tests**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py -v && cd ..
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add 01_scene_assembly/build_scene.py tests/01_scene_assembly/test_build_scene.py
git commit -m "feat: add environment VariantSet with indoor/outdoor variants"
```

---

## Task 5: Reference a robot stub sublayer

**Files:**
- Create: `01_scene_assembly/robot_stub.usda` (hand-written, not generated)
- Modify: `01_scene_assembly/build_scene.py`
- Modify: `tests/01_scene_assembly/test_build_scene.py`

- [ ] **Step 1: Write the robot stub USDA by hand**

Create `01_scene_assembly/robot_stub.usda`:

```usda
#usda 1.0
(
    defaultPrim = "Robot"
    upAxis = "Y"
    metersPerUnit = 1.0
)

def Xform "Robot" (
    kind = "component"
)
{
    def Xform "Base" {}
    def Xform "Arm" {}
}
```

- [ ] **Step 2: Write failing test for reference**

Append to `tests/01_scene_assembly/test_build_scene.py`:

```python
def test_robot_reference_exists(tmp_path):
    """Scene must have a /World/Robot prim populated via a reference."""
    import shutil, pathlib
    # Copy robot_stub.usda next to the output so the reference resolves
    stub_src = pathlib.Path(__file__).parents[2] / "01_scene_assembly" / "robot_stub.usda"
    shutil.copy(stub_src, tmp_path / "robot_stub.usda")

    out = str(tmp_path / "scene.usda")
    stage = bs.build_scene(out, robot_stub_path=str(tmp_path / "robot_stub.usda"))
    robot = stage.GetPrimAtPath("/World/Robot")
    assert robot.IsValid(), "/World/Robot not found"
    base = stage.GetPrimAtPath("/World/Robot/Base")
    assert base.IsValid(), "/World/Robot/Base not found (reference not composed)"
```

- [ ] **Step 3: Run to confirm failure**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py::test_robot_reference_exists -v && cd ..
```

Expected: FAIL — `TypeError: build_scene() got an unexpected keyword argument 'robot_stub_path'`

- [ ] **Step 4: Update `build_scene.py` signature and add reference**

Update the function signature and body:

```python
def build_scene(output_path: str, robot_stub_path: str | None = None) -> Usd.Stage:
    """Create and save a USD scene; return the open stage.

    Args:
        output_path: Where to write the .usda file.
        robot_stub_path: Optional absolute path to a robot stub .usda to reference.
                         Defaults to robot_stub.usda in the same directory as this script.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Ground plane
    ground = UsdGeom.Mesh.Define(stage, "/World/GroundPlane")
    ground.CreatePointsAttr([(-5, 0, -5), (5, 0, -5), (5, 0, 5), (-5, 0, 5)])
    ground.CreateFaceVertexCountsAttr([4])
    ground.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
    ground.CreateExtentAttr([(-5, 0, -5), (5, 0, 5)])

    # VariantSet: environment
    vsets = root.GetPrim().GetVariantSets()
    env_vset = vsets.AddVariantSet("environment")
    env_vset.AddVariant("indoor")
    env_vset.SetVariantSelection("indoor")
    with env_vset.GetVariantEditContext():
        ceiling = UsdGeom.Mesh.Define(stage, "/World/Ceiling")
        ceiling.CreatePointsAttr([(-5, 3, -5), (5, 3, -5), (5, 3, 5), (-5, 3, 5)])
        ceiling.CreateFaceVertexCountsAttr([4])
        ceiling.CreateFaceVertexIndicesAttr([0, 1, 2, 3])
        ceiling.CreateExtentAttr([(-5, 3, -5), (5, 3, 5)])
    env_vset.AddVariant("outdoor")
    env_vset.SetVariantSelection("indoor")

    # Reference: robot stub — demonstrates LIVRPS 'R' (References) layer
    # Physical AI use: robot assets are maintained separately and referenced in;
    # this decouples scene layout from robot asset versioning.
    if robot_stub_path is None:
        robot_stub_path = os.path.join(os.path.dirname(__file__), "robot_stub.usda")
    robot_xform = UsdGeom.Xform.Define(stage, "/World/Robot")
    robot_xform.GetPrim().GetReferences().AddReference(robot_stub_path)

    stage.Save()
    return stage
```

- [ ] **Step 5: Run all tests**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_build_scene.py -v && cd ..
```

Expected: all PASS

- [ ] **Step 6: Commit**

```bash
git add 01_scene_assembly/robot_stub.usda 01_scene_assembly/build_scene.py tests/01_scene_assembly/test_build_scene.py
git commit -m "feat: reference robot_stub.usda into /World/Robot"
```

---

## Task 6: `validate_scene.py` — usdchecker integration

**Files:**
- Create: `01_scene_assembly/validate_scene.py`
- Create: `tests/01_scene_assembly/test_validate_scene.py`

- [ ] **Step 1: Write failing integration test**

Create `tests/01_scene_assembly/test_validate_scene.py`:

```python
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
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_validate_scene.py -v && cd ..
```

Expected: FAIL — `FileNotFoundError` because `validate_scene.py` doesn't exist yet.

- [ ] **Step 3: Create `validate_scene.py`**

Create `01_scene_assembly/validate_scene.py`:

```python
"""
validate_scene.py — runs usdchecker on a scene file and exits non-zero on errors.

Physical AI purpose:
  usdchecker enforces USD spec compliance. A clean check guarantees the scene
  will load in any USD-compliant runtime (Isaac Sim, ROS2 bridge, etc.) without
  silent degradation.

Usage:
    python validate_scene.py [path/to/scene.usda]
    Exit code 0 = clean. Non-zero = errors found (details printed to stdout).
"""
import sys
import os
from pxr import UsdUtils


def validate(scene_path: str) -> list[str]:
    """Run usdchecker on scene_path; return list of error strings (empty = clean)."""
    checker = UsdUtils.ComplianceChecker(
        arkit=False,
        skipARKitRootLayerCheck=False,
        rootPackageOnly=False,
        skipVariants=False,
        verbose=False,
    )
    checker.CheckCompliance(scene_path)
    errors = list(checker.GetErrors())
    warnings = []  # warnings are informational only — not treated as failures
    return errors


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "output", "scene.usda"
    )
    errors = validate(path)
    if errors:
        print(f"usdchecker FAILED on {path}:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    print(f"usdchecker PASSED: {path}")
    sys.exit(0)
```

- [ ] **Step 4: Run the integration test**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/test_validate_scene.py -v && cd ..
```

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add 01_scene_assembly/validate_scene.py tests/01_scene_assembly/test_validate_scene.py
git commit -m "feat: add validate_scene.py with usdchecker integration test"
```

---

## Task 7: Generate and commit `output/scene.usda`

**Files:**
- Create/update: `01_scene_assembly/output/scene.usda`

- [ ] **Step 1: Run `build_scene.py` standalone to generate the file**

```bash
cd 01_scene_assembly && python build_scene.py && cd ..
```

Expected output: `Saved: 01_scene_assembly/output/scene.usda`

- [ ] **Step 2: Run `validate_scene.py` on the generated file**

```bash
python 01_scene_assembly/validate_scene.py 01_scene_assembly/output/scene.usda
```

Expected: `usdchecker PASSED: 01_scene_assembly/output/scene.usda`

- [ ] **Step 3: Inspect the file is ASCII and readable**

```bash
head -30 01_scene_assembly/output/scene.usda
```

Expected: starts with `#usda 1.0` header, human-readable prims visible.

- [ ] **Step 4: Run the full test suite**

```bash
cd 01_scene_assembly && pytest ../tests/01_scene_assembly/ -v && cd ..
```

Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add 01_scene_assembly/output/scene.usda
git commit -m "chore: commit generated scene.usda for diff visibility"
```

---

## Task 8: Update CLAUDE.md session handoff

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark module 01 complete and record next steps**

In `CLAUDE.md`, update the `### Completed:` and `### Next session should start with:` sections:

```markdown
### Completed:
- [x] 01_scene_assembly — LIVRPS composition, VariantSets, defaultPrim, usdchecker ✓
- [ ] 02_sensor_simulation
- [ ] 03_robot_asset_library
- [ ] 04_physics_annotation
- [ ] 05_tensorrt_inference_bridge
- [ ] 06_ros2_usdz_export

### Next session should start with:
Implement 02_sensor_simulation: custom attributes for LiDAR and camera sensor prims.
Reference pattern: build_scene.py / validate_scene.py from 01_scene_assembly.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: mark 01_scene_assembly complete in session handoff notes"
```

---

## Self-Review

**Spec coverage check:**
- LIVRPS composition → Task 5 (References), Task 4 (VariantSets) — L/I/P/S not explicitly modelled but V and R are covered. Adequate for a portfolio demo.
- VariantSets → Task 4 ✓
- defaultPrim → Task 2 ✓
- usdchecker zero errors → Task 6 ✓
- `build_*.py` + `validate_*.py` convention → Tasks 2 & 6 ✓
- Runnable standalone → Task 2 (`__main__` block) ✓
- `.usda` ASCII output → Task 7 step 3 verification ✓

**Placeholder scan:** No TBD, TODO, or "similar to Task N" entries found.

**Type consistency:** `build_scene(output_path, robot_stub_path)` signature introduced in Task 5 and reused in Tasks 6 & 7 consistently. `validate(scene_path)` returns `list[str]` and is only called in `validate_scene.py` `__main__`.
