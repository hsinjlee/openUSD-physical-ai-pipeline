# 04_physics_annotation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Physics-annotate module 03's robot asset (CollisionAPI, MassAPI, RigidBodyAPI, RevoluteJoint, FixedJoint, ArticulationRootAPI, PhysicsScene) as a non-destructive USD overlay layer that passes usdchecker.

**Architecture:** `build_physics.py` regenerates 03's `robot.usda` (imported builder), then creates `output/robot_physics.usda` whose root layer *sublayers* the robot asset via a relative path and authors all physics opinions as `over` prims (plus `def` prims for joints/scene) in the overlay only. `validate_physics.py` runs usdchecker on the composed result. Approach verified by prototype: usdchecker passes, robot.usda stays pristine.

**Tech Stack:** Python 3.10+, usd-core 26.5 (`pxr.UsdPhysics`, `pxr.Sdf`, `pxr.Gf`), pytest.

**Spec:** `docs/superpowers/specs/2026-07-02-04-physics-annotation-design.md`

**Conventions that apply to every task:**
- Run tests from repo root: `python -m pytest tests/04_physics_annotation/ -v`
- Every commit message ends with:
  ```
  Co-Authored-By: Claude Fable 5 <noreply@anthropic.com>
  Claude-Session: https://claude.ai/code/session_013UbBKYozfn9z1LqQMhaVaU
  ```
- All API schemas end up in `prepend apiSchemas` — `UsdPhysics.*API.Apply(prim)` does this automatically; never author apiSchemas metadata by hand.

---

### Task 1: Overlay stage scaffold — sublayer + defaultPrim

**Files:**
- Create: `tests/04_physics_annotation/__init__.py` (empty)
- Create: `tests/04_physics_annotation/test_build_physics.py`
- Create: `04_physics_annotation/build_physics.py`

- [ ] **Step 1: Write the failing tests**

Create empty `tests/04_physics_annotation/__init__.py`, then `tests/04_physics_annotation/test_build_physics.py`:

```python
"""Tests for 04_physics_annotation/build_physics.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "04_physics_annotation"))

import build_physics as bp  # noqa: E402
from pxr import Usd, UsdPhysics, Sdf, Gf
import pytest


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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: FAIL at collection with `ModuleNotFoundError: No module named 'build_physics'`

- [ ] **Step 3: Write minimal implementation**

Create `04_physics_annotation/build_physics.py`:

```python
"""
build_physics.py — annotates the module-03 robot asset with UsdPhysics schemas
in a non-destructive overlay layer.

Physical AI purpose:
  Physics annotation as a separate USD layer is how simulation teams add
  collision, mass, and joint definitions to assets they don't own (vendor
  robots, marketplace props). The original asset stays pristine; the overlay
  composes over it via the layer stack (LIVRPS), and any UsdPhysics runtime
  (Isaac Sim, PhysX) consumes the composed result.
"""
import os
import sys
from pxr import Usd, UsdPhysics, Sdf, Gf

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(MODULE_DIR, "output")
ROBOT_MODULE_DIR = os.path.normpath(
    os.path.join(MODULE_DIR, os.pardir, "03_robot_asset_library")
)
ROBOT_USDA = os.path.join(ROBOT_MODULE_DIR, "output", "robot.usda")

sys.path.insert(0, ROBOT_MODULE_DIR)
from build_robot import build_robot  # noqa: E402 — depends on sys.path.insert


def _ensure_robot_asset() -> None:
    """(Re)generate 03's robot.usda unless its layer is already open in-process.

    Physical AI purpose:
      The overlay depends on the base asset existing on disk. Regenerating it
      keeps the demo deterministic; the Sdf.Layer.Find guard avoids re-creating
      a layer that a live stage (e.g. a previous build in the same pytest
      process) still holds open.
    """
    if Sdf.Layer.Find(ROBOT_USDA) is None:
        os.makedirs(os.path.dirname(ROBOT_USDA), exist_ok=True)
        build_robot(ROBOT_USDA)


def build_physics(output_path: str) -> Usd.Stage:
    """Create and save the physics overlay stage; return the open stage.

    Physical AI purpose:
      The root layer sublayers robot.usda via a *relative* asset path, so the
      pair of files stays relocatable as a unit (no absolute paths — repo
      rule). Physics opinions authored on this stage land in the overlay
      layer, never in the base asset.
    """
    _ensure_robot_asset()
    stage = Usd.Stage.CreateNew(output_path)
    robot_rel = os.path.relpath(
        ROBOT_USDA, os.path.dirname(os.path.abspath(output_path))
    ).replace(os.sep, "/")
    stage.GetRootLayer().subLayerPaths.append(robot_rel)
    stage.SetDefaultPrim(stage.GetPrimAtPath("/Robot"))
    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "robot_physics.usda")
    build_physics(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add tests/04_physics_annotation/ 04_physics_annotation/build_physics.py
git commit -m "feat: add build_physics() overlay stage sublayering 03's robot.usda"
```

---

### Task 2: Rigid bodies and masses on the links

**Files:**
- Modify: `04_physics_annotation/build_physics.py`
- Test: `tests/04_physics_annotation/test_build_physics.py`

- [ ] **Step 1: Write the failing tests** (append to `test_build_physics.py`)

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 2 new tests FAIL with `AssertionError` (HasAPI is False); 4 previous pass

- [ ] **Step 3: Implement**

In `build_physics.py`, add after `_ensure_robot_asset`:

```python
def _add_rigid_body(stage: Usd.Stage, link_path: str, mass: float) -> None:
    """Mark a link Xform as a dynamic rigid body with an explicit mass.

    Physical AI purpose:
      RigidBodyAPI on the link Xform (not the Geom) makes the whole link one
      dynamic body; MassAPI overrides density-derived mass with the measured
      value a real robot datasheet provides — critical for sim-to-real
      transfer of dynamics.
    """
    prim = stage.GetPrimAtPath(link_path)
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass)
```

In `build_physics()`, insert between `stage.SetDefaultPrim(...)` and `stage.Save()`:

```python
    _add_rigid_body(stage, "/Robot/Base", mass=10.0)
    _add_rigid_body(stage, "/Robot/Arm", mass=2.0)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 6 passed

- [ ] **Step 5: Commit**

```bash
git add 04_physics_annotation/build_physics.py tests/04_physics_annotation/test_build_physics.py
git commit -m "feat: apply RigidBodyAPI + MassAPI to Base/Arm links in overlay"
```

---

### Task 3: Collision shapes and articulation root

**Files:**
- Modify: `04_physics_annotation/build_physics.py`
- Test: `tests/04_physics_annotation/test_build_physics.py`

- [ ] **Step 1: Write the failing tests** (append)

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 2 new FAIL (HasAPI False); 6 previous pass

- [ ] **Step 3: Implement**

Add to `build_physics.py`:

```python
def _add_collision(stage: Usd.Stage, geom_path: str) -> None:
    """Enable collision on a shape prim.

    Physical AI purpose:
      CollisionAPI on the Geom (not the link Xform) lets the physics engine
      derive the collider from the render shape while the transform hierarchy
      stays untouched — the exact separation module 03 prepared for.
    """
    UsdPhysics.CollisionAPI.Apply(stage.GetPrimAtPath(geom_path))
```

In `build_physics()`, after the `_add_rigid_body` calls:

```python
    UsdPhysics.ArticulationRootAPI.Apply(stage.GetPrimAtPath("/Robot"))
    _add_collision(stage, "/Robot/Base/Geom")
    _add_collision(stage, "/Robot/Arm/Geom")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add 04_physics_annotation/build_physics.py tests/04_physics_annotation/test_build_physics.py
git commit -m "feat: apply CollisionAPI to Geoms and ArticulationRootAPI to /Robot"
```

---

### Task 4: Joints — fixed base anchor + revolute arm joint

**Files:**
- Modify: `04_physics_annotation/build_physics.py`
- Test: `tests/04_physics_annotation/test_build_physics.py`

- [ ] **Step 1: Write the failing tests** (append)

```python
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
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 4 new FAIL (`assert joint` fails — prim invalid); 8 previous pass

- [ ] **Step 3: Implement**

Add to `build_physics.py`:

```python
def _add_fixed_base_joint(stage: Usd.Stage) -> UsdPhysics.FixedJoint:
    """Weld the Base link to the world frame.

    Physical AI purpose:
      A fixed-base articulation (arm bolted to a table) is the standard
      manipulator setup. Leaving body0 empty means "the world" in UsdPhysics
      joint semantics.
    """
    joint = UsdPhysics.FixedJoint.Define(stage, "/Robot/FixedBaseJoint")
    joint.CreateBody1Rel().SetTargets(["/Robot/Base"])
    return joint


def _add_arm_joint(stage: Usd.Stage) -> UsdPhysics.RevoluteJoint:
    """Connect Base→Arm with a limited revolute joint.

    Physical AI purpose:
      RevoluteJoint is USD's native articulated-DOF description — the same
      information a URDF <joint type="revolute"> carries, but living inside
      the asset. localPos0/1 place the hinge at the Arm cube's bottom face
      (world y=0.75) in each body's own frame; limits are authored in degrees.
    """
    joint = UsdPhysics.RevoluteJoint.Define(stage, "/Robot/ArmJoint")
    joint.CreateBody0Rel().SetTargets(["/Robot/Base"])
    joint.CreateBody1Rel().SetTargets(["/Robot/Arm"])
    joint.CreateAxisAttr(UsdPhysics.Tokens.z)
    joint.CreateLocalPos0Attr(Gf.Vec3f(0.0, 0.75, 0.0))
    joint.CreateLocalPos1Attr(Gf.Vec3f(0.0, -0.25, 0.0))
    joint.CreateLowerLimitAttr(-90.0)
    joint.CreateUpperLimitAttr(90.0)
    return joint
```

In `build_physics()`, after the `_add_collision` calls:

```python
    _add_fixed_base_joint(stage)
    _add_arm_joint(stage)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 12 passed

- [ ] **Step 5: Commit**

```bash
git add 04_physics_annotation/build_physics.py tests/04_physics_annotation/test_build_physics.py
git commit -m "feat: add FixedBaseJoint and limited RevoluteJoint ArmJoint"
```

---

### Task 5: PhysicsScene, non-destructiveness guarantee, CLI output

**Files:**
- Modify: `04_physics_annotation/build_physics.py`
- Test: `tests/04_physics_annotation/test_build_physics.py`

- [ ] **Step 1: Write the failing tests** (append)

```python
def test_physics_scene_gravity(tmp_path):
    """PhysicsScene declares standard gravity matching the Y-up, meters stage."""
    out = str(tmp_path / "robot_physics.usda")
    stage = bp.build_physics(out)
    scene = UsdPhysics.Scene(stage.GetPrimAtPath("/Robot/PhysicsScene"))
    assert scene
    assert scene.GetGravityDirectionAttr().Get() == Gf.Vec3f(0.0, -1.0, 0.0)
    assert scene.GetGravityMagnitudeAttr().Get() == pytest.approx(9.81)


def test_base_asset_stays_pristine(tmp_path):
    """THE core guarantee of this module: after building the overlay, 03's
    robot.usda layer contains zero physics opinions."""
    out = str(tmp_path / "robot_physics.usda")
    bp.build_physics(out)
    robot_layer = Sdf.Layer.FindOrOpen(bp.ROBOT_USDA)
    assert robot_layer is not None
    assert "Physics" not in robot_layer.ExportToString()
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: `test_physics_scene_gravity` FAILS (`assert scene` — prim invalid);
`test_base_asset_stays_pristine` already PASSES (overlay design guarantees it —
it's a regression guard). 12 previous pass.

- [ ] **Step 3: Implement**

Add to `build_physics.py`:

```python
def _add_physics_scene(stage: Usd.Stage) -> UsdPhysics.Scene:
    """Define the simulation context (gravity).

    Physical AI purpose:
      PhysicsScene tells any UsdPhysics runtime how to integrate the world —
      here standard Earth gravity along -Y to match the Y-up, meters stage.
      Kept under /Robot so all prims stay inside the defaultPrim hierarchy;
      production scenes usually place it at stage root instead.
    """
    scene = UsdPhysics.Scene.Define(stage, "/Robot/PhysicsScene")
    scene.CreateGravityDirectionAttr(Gf.Vec3f(0.0, -1.0, 0.0))
    scene.CreateGravityMagnitudeAttr(9.81)
    return scene
```

In `build_physics()`, after `_add_arm_joint(stage)`:

```python
    _add_physics_scene(stage)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 14 passed

- [ ] **Step 5: Generate the committed demo output and sanity-check it**

Run: `python 04_physics_annotation/build_physics.py`
Expected: `Saved: .../04_physics_annotation/output/robot_physics.usda`

Run: `git status --short 04_physics_annotation/` — if `output/` appears (not
gitignored), leave it untracked; do NOT commit output files unless earlier
modules committed theirs (check `git ls-files 03_robot_asset_library/output/`
and mirror whatever 03 does).

- [ ] **Step 6: Commit**

```bash
git add 04_physics_annotation/build_physics.py tests/04_physics_annotation/test_build_physics.py
git commit -m "feat: add PhysicsScene gravity and non-destructiveness regression test"
```

---

### Task 6: validate_physics.py — usdchecker gate

**Files:**
- Create: `04_physics_annotation/validate_physics.py`
- Create: `tests/04_physics_annotation/test_validate_physics.py`

- [ ] **Step 1: Write the failing test**

Create `tests/04_physics_annotation/test_validate_physics.py`:

```python
"""Integration test: robot_physics.usda must pass usdchecker with zero errors."""
import sys
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "04_physics_annotation"
sys.path.insert(0, str(MODULE_DIR))

import build_physics as bp  # noqa: E402 — depends on sys.path.insert above


def test_validate_physics_exits_zero(tmp_path):
    """validate_physics.py must exit 0 when the physics overlay is valid."""
    out = str(tmp_path / "robot_physics.usda")
    bp.build_physics(out)

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_physics.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_physics.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/04_physics_annotation/test_validate_physics.py -v`
Expected: FAIL — subprocess exits 2 (`No such file`) because validate_physics.py doesn't exist

- [ ] **Step 3: Implement**

Create `04_physics_annotation/validate_physics.py` (same contract as 03's validator):

```python
"""
validate_physics.py — runs usdchecker on the physics overlay and exits non-zero on errors.

Physical AI purpose:
  usdchecker validates the *composed* stage — overlay plus sublayered robot
  asset — so a clean check guarantees the physics-annotated robot loads in any
  UsdPhysics-compliant runtime (Isaac Sim, PhysX bridge) without silent
  degradation.

Usage:
    python validate_physics.py [path/to/robot_physics.usda]
    Exit code 0 = clean. Non-zero = errors found (details printed to stdout).
"""
import sys
import os
import warnings
from pxr import UsdUtils


def validate(scene_path: str) -> list[str]:
    """Run usdchecker on scene_path; return list of error strings (empty = clean)."""
    # TODO: UsdUtils.ComplianceChecker is deprecated in usd-core ≥24.x in favour of
    # the Usd Validation Framework. Migrate when usd-core drops ComplianceChecker.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        checker = UsdUtils.ComplianceChecker(
            arkit=False,
            skipARKitRootLayerCheck=False,
            rootPackageOnly=False,
            skipVariants=False,
            verbose=False,
        )
        checker.CheckCompliance(scene_path)
        errors = list(checker.GetErrors())
    return errors


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "output", "robot_physics.usda"
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

- [ ] **Step 4: Run all tests and the standalone scripts to verify**

Run: `python -m pytest tests/04_physics_annotation/ -v`
Expected: 15 passed

Run: `python 04_physics_annotation/build_physics.py && python 04_physics_annotation/validate_physics.py`
Expected: `Saved: ...robot_physics.usda` then `usdchecker PASSED: ...robot_physics.usda`

Also confirm the full suite still passes: `python -m pytest tests/ -v`
Expected: all modules green (01, 02, 03, 04)

- [ ] **Step 5: Commit**

```bash
git add 04_physics_annotation/validate_physics.py tests/04_physics_annotation/test_validate_physics.py
git commit -m "feat: add validate_physics.py; 04_physics_annotation passes usdchecker"
```

---

### Task 7: Update CLAUDE.md session handoff notes

**Files:**
- Modify: `CLAUDE.md` (Session Handoff Notes section)

- [ ] **Step 1: Edit CLAUDE.md**

In `### Completed:`, change the 04 line to:

```markdown
- [x] 04_physics_annotation — UsdPhysics overlay layer (CollisionAPI, MassAPI, RigidBodyAPI, RevoluteJoint, FixedJoint, ArticulationRootAPI, PhysicsScene), non-destructive over 03's robot.usda, usdchecker ✓
```

Replace the `### Next session should start with:` body with:

```markdown
Implement 05_tensorrt_inference_bridge: custom USD metadata → inference config dict.
Reference pattern: build_physics.py / validate_physics.py from 04_physics_annotation.
Note: 04 demonstrates the overlay-layer pattern (physics opinions sublayer 03's
robot.usda non-destructively) — 05's metadata could annotate either asset the same way.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: mark 04_physics_annotation complete in session handoff notes"
```

---

## Self-Review Notes

- **Spec coverage:** every table row in the spec maps to a task (rigid bodies/mass → T2, collision/articulation → T3, joints → T4, scene + pristine guarantee → T5, validator → T6). Overlay/sublayer/defaultPrim → T1.
- **Verified by prototype:** sublayer + `Apply()` on composed prims + usdchecker pass confirmed against usd-core 26.5 before this plan was written.
- **Type consistency:** helper names (`_add_rigid_body`, `_add_collision`, `_add_fixed_base_joint`, `_add_arm_joint`, `_add_physics_scene`) are used exactly as defined; `bp.ROBOT_USDA` referenced in T5 test is defined in T1.
