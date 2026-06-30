# 02_sensor_simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `02_sensor_simulation` — a USD stage with LiDAR and camera sensor prims that carry Physical AI–relevant custom attributes, validated clean by usdchecker.

**Architecture:** Follow the `01_scene_assembly` pattern exactly: `build_sensors.py` generates `output/sensor_rig.usda`; `validate_sensors.py` runs `usdchecker`; pytest lives in `tests/02_sensor_simulation/`. The stage has a single `/SensorRig` defaultPrim containing a `LiDAR` Xform (custom `sensor:lidar:*` attributes) and a `Camera` prim (standard `UsdGeom.Camera` attrs + custom `sensor:camera:*` attrs).

**Tech Stack:** Python 3.10+, `usd-core` (`pxr` — `Usd`, `UsdGeom`, `Sdf`), `pytest`

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `02_sensor_simulation/build_sensors.py` | Stage builder — LiDAR + Camera prims with custom attrs |
| Create | `02_sensor_simulation/validate_sensors.py` | usdchecker wrapper (exit 0 = clean) |
| Create | `tests/02_sensor_simulation/__init__.py` | Makes pytest discover this package |
| Create | `tests/02_sensor_simulation/test_build_sensors.py` | All unit tests |

---

## Task 1: Test file skeleton + pxr import smoke test

**Files:**
- Create: `tests/02_sensor_simulation/__init__.py`
- Create: `tests/02_sensor_simulation/test_build_sensors.py`

- [ ] **Step 1: Create the empty `__init__.py`**

```bash
touch /home/f042/p/openUSD-physical-ai-pipeline/tests/02_sensor_simulation/__init__.py
```

- [ ] **Step 2: Write the test file with an import smoke test**

Create `tests/02_sensor_simulation/test_build_sensors.py`:

```python
"""Tests for 02_sensor_simulation/build_sensors.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))

import build_sensors as bs  # noqa: E402


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, Sdf  # ImportError = test failure
```

- [ ] **Step 3: Run the test — expect ImportError for `build_sensors`**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_pxr_imports -v
```

Expected output: `ModuleNotFoundError: No module named 'build_sensors'`

- [ ] **Step 4: Create a stub `build_sensors.py` so the import resolves**

Create `02_sensor_simulation/build_sensors.py`:

```python
"""
build_sensors.py — generates a USD scene with LiDAR and camera sensor prims.

Physical AI purpose:
  Sensor prims with typed custom attributes let simulation runtimes (Isaac Sim,
  CARLA bridge) read sensor parameters directly from USD without side-channel
  config files. The sensor: namespace is a widely-used convention for
  Physical AI pipelines.
"""
import os
from pxr import Usd, UsdGeom, Sdf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
```

- [ ] **Step 5: Run the test — expect PASS**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_pxr_imports -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add tests/02_sensor_simulation/__init__.py \
        tests/02_sensor_simulation/test_build_sensors.py \
        02_sensor_simulation/build_sensors.py
git commit -m "test: scaffold 02_sensor_simulation test file and stub module"
```

---

## Task 2: Stage defaultPrim and metadata

**Files:**
- Modify: `tests/02_sensor_simulation/test_build_sensors.py` — add `test_stage_has_default_prim`
- Modify: `02_sensor_simulation/build_sensors.py` — add `build_sensors()` skeleton

- [ ] **Step 1: Add the failing test**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_stage_up_axis_and_units(tmp_path):
    """Stage must use Y-up and metersPerUnit=1.0 (SI robot sim convention)."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0
```

Also add the missing import at the top of the test file (after the `sys.path.insert` block):

```python
from pxr import UsdGeom
```

- [ ] **Step 2: Run — expect AttributeError (no `build_sensors` function yet)**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_stage_has_default_prim -v
```

Expected: `AttributeError: module 'build_sensors' has no attribute 'build_sensors'`

- [ ] **Step 3: Implement `build_sensors()` skeleton**

Replace `02_sensor_simulation/build_sensors.py` with:

```python
"""
build_sensors.py — generates a USD scene with LiDAR and camera sensor prims.

Physical AI purpose:
  Sensor prims with typed custom attributes let simulation runtimes (Isaac Sim,
  CARLA bridge) read sensor parameters directly from USD without side-channel
  config files. The sensor: namespace is a widely-used convention for
  Physical AI pipelines.
"""
import os
from pxr import Usd, UsdGeom, Sdf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_sensors(output_path: str) -> Usd.Stage:
    """Create and save a USD sensor-rig stage; return the open stage.

    Physical AI purpose:
      /SensorRig is the mount frame for all sensors on a robot. downstream
      consumers reference this file and bind each sensor prim to a perception
      pipeline by prim path — no string config required.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/SensorRig")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensor_rig.usda")
    build_sensors(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_stage_has_default_prim \
                 tests/02_sensor_simulation/test_build_sensors.py::test_stage_up_axis_and_units -v
```

Expected: both `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/02_sensor_simulation/test_build_sensors.py \
        02_sensor_simulation/build_sensors.py
git commit -m "feat: add build_sensors() skeleton with defaultPrim and stage metadata"
```

---

## Task 3: LiDAR prim and custom attributes

**Files:**
- Modify: `tests/02_sensor_simulation/test_build_sensors.py`
- Modify: `02_sensor_simulation/build_sensors.py`

The LiDAR prim is an `Xform` at `/SensorRig/LiDAR` with nine custom float/int attributes in the `sensor:lidar:` namespace.

- [ ] **Step 1: Add the failing tests**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_lidar_prim_exists(tmp_path):
    """LiDAR sensor prim must exist at /SensorRig/LiDAR as an Xform."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    assert prim.IsValid(), "/SensorRig/LiDAR prim not found"
    assert prim.GetTypeName() == "Xform", "LiDAR prim must be Xform"


def test_lidar_attributes_present(tmp_path):
    """LiDAR prim must carry all required sensor:lidar: custom attributes."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    expected = [
        "sensor:lidar:minRange",
        "sensor:lidar:maxRange",
        "sensor:lidar:horizontalFovStart",
        "sensor:lidar:horizontalFovEnd",
        "sensor:lidar:verticalFovLower",
        "sensor:lidar:verticalFovUpper",
        "sensor:lidar:rotationFrequency",
        "sensor:lidar:horizontalResolution",
        "sensor:lidar:numChannels",
    ]
    for name in expected:
        attr = prim.GetAttribute(name)
        assert attr.IsValid(), f"LiDAR attribute '{name}' missing"


def test_lidar_attribute_values(tmp_path):
    """LiDAR custom attributes must hold the expected default values."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    assert prim.GetAttribute("sensor:lidar:minRange").Get() == 0.1
    assert prim.GetAttribute("sensor:lidar:maxRange").Get() == 100.0
    assert prim.GetAttribute("sensor:lidar:horizontalFovStart").Get() == -180.0
    assert prim.GetAttribute("sensor:lidar:horizontalFovEnd").Get() == 180.0
    assert prim.GetAttribute("sensor:lidar:verticalFovLower").Get() == -15.0
    assert prim.GetAttribute("sensor:lidar:verticalFovUpper").Get() == 15.0
    assert prim.GetAttribute("sensor:lidar:rotationFrequency").Get() == 10.0
    assert prim.GetAttribute("sensor:lidar:horizontalResolution").Get() == 0.2
    assert prim.GetAttribute("sensor:lidar:numChannels").Get() == 16
```

- [ ] **Step 2: Run — expect FAIL (prim not yet created)**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_lidar_prim_exists -v
```

Expected: `AssertionError: /SensorRig/LiDAR prim not found`

- [ ] **Step 3: Add the LiDAR prim helper to `build_sensors.py`**

Add a private helper function and call it from `build_sensors()`. Replace `build_sensors.py` with:

```python
"""
build_sensors.py — generates a USD scene with LiDAR and camera sensor prims.

Physical AI purpose:
  Sensor prims with typed custom attributes let simulation runtimes (Isaac Sim,
  CARLA bridge) read sensor parameters directly from USD without side-channel
  config files. The sensor: namespace is a widely-used convention for
  Physical AI pipelines.
"""
import os
from pxr import Usd, UsdGeom, Sdf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def _add_lidar(stage: Usd.Stage, path: str) -> UsdGeom.Xform:
    """Define a LiDAR sensor prim with custom attributes.

    Physical AI purpose:
      These attributes map directly to Isaac Sim's RangeSensorCreateLidar
      parameters and NVIDIA's sensor extension schema, letting the same USD
      file drive both simulation and hardware-in-the-loop configs.
    """
    lidar = UsdGeom.Xform.Define(stage, path)
    prim = lidar.GetPrim()

    float_attrs = {
        "sensor:lidar:minRange":            (Sdf.ValueTypeNames.Float, 0.1),
        "sensor:lidar:maxRange":            (Sdf.ValueTypeNames.Float, 100.0),
        "sensor:lidar:horizontalFovStart":  (Sdf.ValueTypeNames.Float, -180.0),
        "sensor:lidar:horizontalFovEnd":    (Sdf.ValueTypeNames.Float, 180.0),
        "sensor:lidar:verticalFovLower":    (Sdf.ValueTypeNames.Float, -15.0),
        "sensor:lidar:verticalFovUpper":    (Sdf.ValueTypeNames.Float, 15.0),
        "sensor:lidar:rotationFrequency":   (Sdf.ValueTypeNames.Float, 10.0),
        "sensor:lidar:horizontalResolution":(Sdf.ValueTypeNames.Float, 0.2),
    }
    for name, (type_name, value) in float_attrs.items():
        prim.CreateAttribute(name, type_name).Set(value)

    prim.CreateAttribute("sensor:lidar:numChannels", Sdf.ValueTypeNames.Int).Set(16)
    return lidar


def build_sensors(output_path: str) -> Usd.Stage:
    """Create and save a USD sensor-rig stage; return the open stage.

    Physical AI purpose:
      /SensorRig is the mount frame for all sensors on a robot. Downstream
      consumers reference this file and bind each sensor prim to a perception
      pipeline by prim path — no string config required.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/SensorRig")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    _add_lidar(stage, "/SensorRig/LiDAR")

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensor_rig.usda")
    build_sensors(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run all LiDAR tests — expect PASS**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_lidar_prim_exists \
                 tests/02_sensor_simulation/test_build_sensors.py::test_lidar_attributes_present \
                 tests/02_sensor_simulation/test_build_sensors.py::test_lidar_attribute_values -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/02_sensor_simulation/test_build_sensors.py \
        02_sensor_simulation/build_sensors.py
git commit -m "feat: add LiDAR sensor prim with sensor:lidar: custom attributes"
```

---

## Task 4: Camera prim — standard UsdGeom.Camera attrs + custom sensor attrs

**Files:**
- Modify: `tests/02_sensor_simulation/test_build_sensors.py`
- Modify: `02_sensor_simulation/build_sensors.py`

The Camera prim uses `UsdGeom.Camera` (built-in USD schema) at `/SensorRig/Camera`, extended with custom `sensor:camera:imageWidth`, `sensor:camera:imageHeight`, and `sensor:camera:frameRate`.

- [ ] **Step 1: Add the failing tests**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_camera_prim_exists(tmp_path):
    """Camera sensor prim must exist at /SensorRig/Camera as a Camera type."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/Camera")
    assert prim.IsValid(), "/SensorRig/Camera prim not found"
    assert prim.GetTypeName() == "Camera", "Camera prim must be Camera type"


def test_camera_standard_attributes(tmp_path):
    """Camera prim must carry standard UsdGeom.Camera attributes with expected values."""
    from pxr import Gf
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    cam = UsdGeom.Camera(stage.GetPrimAtPath("/SensorRig/Camera"))
    assert cam.GetFocalLengthAttr().Get() == 24.0
    assert cam.GetHorizontalApertureAttr().Get() == 20.955
    assert cam.GetVerticalApertureAttr().Get() == 15.2908
    clip = cam.GetClippingRangeAttr().Get()
    assert abs(clip[0] - 0.1) < 1e-5
    assert abs(clip[1] - 1000.0) < 1e-5


def test_camera_custom_attributes(tmp_path):
    """Camera prim must carry custom sensor:camera: attributes."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/Camera")
    assert prim.GetAttribute("sensor:camera:imageWidth").Get() == 1920
    assert prim.GetAttribute("sensor:camera:imageHeight").Get() == 1080
    assert prim.GetAttribute("sensor:camera:frameRate").Get() == 30.0
```

- [ ] **Step 2: Run — expect FAIL**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_camera_prim_exists -v
```

Expected: `AssertionError: /SensorRig/Camera prim not found`

- [ ] **Step 3: Add `_add_camera()` helper and call it in `build_sensors()`**

Add to `02_sensor_simulation/build_sensors.py` (insert before `build_sensors()`, after `_add_lidar()`):

```python
def _add_camera(stage: Usd.Stage, path: str) -> UsdGeom.Camera:
    """Define a Camera sensor prim with standard and custom attributes.

    Physical AI purpose:
      UsdGeom.Camera standardises intrinsic parameters so any USD-aware
      renderer or vision pipeline can extract focal length and aperture
      without bespoke parsing. Custom sensor:camera: attrs carry
      runtime-specific config (resolution, frame rate) in the same prim.
    """
    cam = UsdGeom.Camera.Define(stage, path)
    # Standard UsdGeom.Camera intrinsics (millimetre units per USD convention)
    cam.CreateFocalLengthAttr().Set(24.0)           # 24 mm — wide-angle robot camera
    cam.CreateHorizontalApertureAttr().Set(20.955)  # APS-C sensor width
    cam.CreateVerticalApertureAttr().Set(15.2908)   # APS-C sensor height
    cam.CreateClippingRangeAttr().Set((0.1, 1000.0))

    # Custom sensor attributes for runtime config
    prim = cam.GetPrim()
    prim.CreateAttribute("sensor:camera:imageWidth",  Sdf.ValueTypeNames.Int).Set(1920)
    prim.CreateAttribute("sensor:camera:imageHeight", Sdf.ValueTypeNames.Int).Set(1080)
    prim.CreateAttribute("sensor:camera:frameRate",   Sdf.ValueTypeNames.Float).Set(30.0)
    return cam
```

Also call it inside `build_sensors()`, after the `_add_lidar` line:

```python
    _add_camera(stage, "/SensorRig/Camera")
```

- [ ] **Step 4: Run all camera tests — expect PASS**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_camera_prim_exists \
                 tests/02_sensor_simulation/test_build_sensors.py::test_camera_standard_attributes \
                 tests/02_sensor_simulation/test_build_sensors.py::test_camera_custom_attributes -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/02_sensor_simulation/test_build_sensors.py \
        02_sensor_simulation/build_sensors.py
git commit -m "feat: add Camera sensor prim with UsdGeom.Camera attrs and sensor:camera: custom attrs"
```

---

## Task 5: `validate_sensors.py` — usdchecker wrapper

**Files:**
- Create: `02_sensor_simulation/validate_sensors.py`

Pattern is identical to `01_scene_assembly/validate_scene.py`.

- [ ] **Step 1: Create `validate_sensors.py`**

```python
"""
validate_sensors.py — runs usdchecker on the sensor rig and exits non-zero on errors.

Physical AI purpose:
  usdchecker enforces USD spec compliance. A clean check guarantees the sensor
  stage will load in any USD-compliant runtime (Isaac Sim, ROS2 bridge, etc.)
  without silent degradation.

Usage:
    python validate_sensors.py [path/to/sensor_rig.usda]
    Exit code 0 = clean. Non-zero = errors found (details printed to stdout).
"""
import sys
import os
import warnings
from pxr import UsdUtils


def validate(scene_path: str) -> list[str]:
    """Run usdchecker on scene_path; return list of error strings (empty = clean)."""
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
        os.path.dirname(__file__), "output", "sensor_rig.usda"
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

- [ ] **Step 2: Add the validate integration test**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_usdchecker_passes(tmp_path):
    """Generated sensor_rig.usda must pass usdchecker with zero errors."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))
    import validate_sensors as vs
    out = str(tmp_path / "sensor_rig.usda")
    bs.build_sensors(out)
    errors = vs.validate(out)
    assert errors == [], f"usdchecker errors: {errors}"
```

- [ ] **Step 3: Run the usdchecker test**

```bash
python -m pytest tests/02_sensor_simulation/test_build_sensors.py::test_usdchecker_passes -v
```

Expected: `PASSED` (zero usdchecker errors)

- [ ] **Step 4: Generate the output file and run validate standalone**

```bash
python 02_sensor_simulation/build_sensors.py
python 02_sensor_simulation/validate_sensors.py
```

Expected:
```
Saved: 02_sensor_simulation/output/sensor_rig.usda
usdchecker PASSED: 02_sensor_simulation/output/sensor_rig.usda
```

- [ ] **Step 5: Run the full test suite**

```bash
python -m pytest tests/02_sensor_simulation/ -v
```

Expected: all tests `PASSED`, zero failures.

- [ ] **Step 6: Commit**

```bash
git add 02_sensor_simulation/validate_sensors.py \
        02_sensor_simulation/output/sensor_rig.usda \
        tests/02_sensor_simulation/test_build_sensors.py
git commit -m "feat: add validate_sensors.py; 02_sensor_simulation complete — usdchecker passes"
```

---

## Task 6: Update CLAUDE.md session handoff

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark 02_sensor_simulation complete in the handoff section**

In `CLAUDE.md`, change:

```markdown
- [ ] 02_sensor_simulation
```

to:

```markdown
- [x] 02_sensor_simulation — LiDAR + Camera sensor prims, custom sensor:* attributes, usdchecker ✓
```

And update the "Next session should start with:" line:

```markdown
### Next session should start with:
Implement 03_robot_asset_library: Xform hierarchy, MaterialBindingAPI, semantic primvars.
Reference pattern: build_sensors.py / validate_sensors.py from 02_sensor_simulation.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: mark 02_sensor_simulation complete in session handoff notes"
```

---

## Self-Review

**Spec coverage check:**
- [x] Custom attributes for LiDAR sensor prim → Task 3
- [x] Custom attributes for camera sensor prim → Task 4
- [x] `build_sensors.py` (generates USD files) → Tasks 2–4
- [x] `validate_sensors.py` (runs usdchecker) → Task 5
- [x] defaultPrim set → Task 2
- [x] `.usda` ASCII format → `Usd.Stage.CreateNew(*.usda)` throughout
- [x] `upAxis=Y`, `metersPerUnit=1.0` → Task 2
- [x] Zero usdchecker errors → Task 5
- [x] TDD (tests before implementation) → every task follows write-test-first order

**No placeholders:** all code blocks contain actual runnable code.

**Type consistency:** `build_sensors(output_path: str) -> Usd.Stage` defined in Task 2, imported and called by the same signature in all subsequent tests.
