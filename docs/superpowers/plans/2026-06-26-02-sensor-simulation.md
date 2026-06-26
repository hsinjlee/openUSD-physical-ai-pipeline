# 02_sensor_simulation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a USD stage that demonstrates custom sensor prim attributes for LiDAR and camera sensors, following the same `build_*.py` / `validate_*.py` pattern established in `01_scene_assembly`.

**Architecture:** `build_sensors.py` creates a `.usda` stage with `/World/Sensors/LiDAR` (an `Xform` with custom `sensor:lidar:*` attributes) and `/World/Sensors/Camera` (a `UsdGeom.Camera` with standard intrinsics plus custom `sensor:camera:*` attributes). `validate_sensors.py` runs `usdchecker` and exits non-zero on any error. Tests live in `tests/02_sensor_simulation/`.

**Tech Stack:** Python 3.10+, `usd-core` (pxr — `Usd`, `UsdGeom`, `Sdf`), `pytest`, `usdchecker`

---

## File Map

| Path | Role |
|---|---|
| `02_sensor_simulation/build_sensors.py` | Generates `02_sensor_simulation/output/sensors.usda` |
| `02_sensor_simulation/validate_sensors.py` | Runs usdchecker; exits non-zero on error |
| `02_sensor_simulation/output/sensors.usda` | Generated ASCII artifact (committed for diff visibility) |
| `tests/02_sensor_simulation/__init__.py` | Empty — pytest package marker |
| `tests/02_sensor_simulation/test_build_sensors.py` | Unit tests: prim existence, attribute types & values |
| `tests/02_sensor_simulation/test_validate_sensors.py` | Integration test: usdchecker reports zero errors |

---

## Task 1: Test infrastructure

**Files:**
- Create: `tests/02_sensor_simulation/__init__.py`
- Create: `tests/02_sensor_simulation/test_build_sensors.py`

- [ ] **Step 1: Create the package marker**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
mkdir -p tests/02_sensor_simulation
touch tests/02_sensor_simulation/__init__.py
```

- [ ] **Step 2: Create test_build_sensors.py**

```python
"""Tests for 02_sensor_simulation/build_sensors.py."""
import sys
import os

import pytest
from pxr import Usd, UsdGeom, Sdf

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "02_sensor_simulation"))


def test_pxr_imports():
    """Confirm usd-core is installed and sensor-relevant pxr modules import."""
    assert Usd is not None
    assert UsdGeom is not None
    assert Sdf is not None
```

- [ ] **Step 3: Run to confirm it passes**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py::test_pxr_imports -v
```

Expected: PASS

- [ ] **Step 4: Commit**

```bash
git add tests/02_sensor_simulation/__init__.py tests/02_sensor_simulation/test_build_sensors.py
git commit -m "test: scaffold 02_sensor_simulation test package"
```

---

## Task 2: build_sensors.py skeleton with defaultPrim

**Files:**
- Create: `02_sensor_simulation/build_sensors.py`
- Create: `02_sensor_simulation/output/.gitkeep`

- [ ] **Step 1: Append a failing test**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
import build_sensors as bs


def test_stage_has_default_prim(tmp_path):
    """Stage must declare a defaultPrim."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_sensors_xform_exists(tmp_path):
    """Stage must have a /World/Sensors Xform as the sensor container."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/World/Sensors")
    assert prim.IsValid(), "/World/Sensors prim not found"
    assert prim.GetTypeName() == "Xform", "/World/Sensors must be an Xform"
```

- [ ] **Step 2: Run to confirm they fail**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py::test_stage_has_default_prim -v
```

Expected: `ModuleNotFoundError: No module named 'build_sensors'`

- [ ] **Step 3: Create 02_sensor_simulation/build_sensors.py**

```python
"""
build_sensors.py — generates a USD stage with LiDAR and camera sensor prims.

Physical AI purpose:
  Sensor prims describe the physical placement and simulation parameters of
  perception hardware (LiDAR, RGB camera) attached to a robot. Encoding these
  as USD custom attributes makes sensor configs version-controlled, diffable,
  and consumable by any USD-aware sim runtime without a separate config file.
"""
import os
from pxr import Usd, UsdGeom, Sdf


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_sensors(output_path: str) -> Usd.Stage:
    """Create and save a USD stage with sensor prims; return the open stage.

    Physical AI purpose:
      /World/Sensors acts as the sensor rig container. Individual sensor prims
      (LiDAR, Camera) hang beneath it with their simulation parameters stored
      as typed USD attributes in the 'sensor:' namespace.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Sensor container — groups all sensor prims under a single Xform
    UsdGeom.Xform.Define(stage, "/World/Sensors")

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensors.usda")
    build_sensors(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run tests**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py -v
```

Expected: all 3 tests PASS

- [ ] **Step 5: Create output placeholder**

```bash
mkdir -p 02_sensor_simulation/output
touch 02_sensor_simulation/output/.gitkeep
```

- [ ] **Step 6: Commit**

```bash
git add 02_sensor_simulation/build_sensors.py 02_sensor_simulation/output/.gitkeep tests/02_sensor_simulation/test_build_sensors.py
git commit -m "feat: add build_sensors skeleton with /World/Sensors container"
```

---

## Task 3: LiDAR sensor prim with custom attributes

**Files:**
- Modify: `02_sensor_simulation/build_sensors.py`
- Modify: `tests/02_sensor_simulation/test_build_sensors.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_lidar_prim_exists(tmp_path):
    """Stage must have /World/Sensors/LiDAR as an Xform."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/World/Sensors/LiDAR")
    assert prim.IsValid(), "/World/Sensors/LiDAR not found"
    assert prim.GetTypeName() == "Xform", "/World/Sensors/LiDAR must be Xform"


def test_lidar_attributes(tmp_path):
    """LiDAR prim must have all required sensor:lidar:* attributes with correct types."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/World/Sensors/LiDAR")

    expected = {
        "sensor:type":                 (Sdf.ValueTypeNames.Token,  "lidar"),
        "sensor:lidar:rangeMinMeters": (Sdf.ValueTypeNames.Float,  0.1),
        "sensor:lidar:rangeMaxMeters": (Sdf.ValueTypeNames.Float,  100.0),
        "sensor:lidar:horizontalFovDeg": (Sdf.ValueTypeNames.Float, 360.0),
        "sensor:lidar:verticalFovDeg":   (Sdf.ValueTypeNames.Float, 30.0),
        "sensor:lidar:numChannels":    (Sdf.ValueTypeNames.Int,    64),
        "sensor:lidar:rotationRateHz": (Sdf.ValueTypeNames.Float,  20.0),
    }
    for attr_name, (expected_type, expected_val) in expected.items():
        attr = prim.GetAttribute(attr_name)
        assert attr.IsValid(), f"attribute '{attr_name}' missing"
        assert attr.GetTypeName() == expected_type, \
            f"'{attr_name}' type: expected {expected_type}, got {attr.GetTypeName()}"
        assert attr.Get() == expected_val, \
            f"'{attr_name}' value: expected {expected_val}, got {attr.Get()}"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py::test_lidar_prim_exists -v
```

Expected: FAIL — `/World/Sensors/LiDAR not found`

- [ ] **Step 3: Add LiDAR prim to build_sensors()**

In `build_sensors.py`, replace the entire `build_sensors()` function body (keep the docstring, update the code after the Sensors Xform line):

```python
def build_sensors(output_path: str) -> Usd.Stage:
    """Create and save a USD stage with sensor prims; return the open stage.

    Physical AI purpose:
      /World/Sensors acts as the sensor rig container. Individual sensor prims
      (LiDAR, Camera) hang beneath it with their simulation parameters stored
      as typed USD attributes in the 'sensor:' namespace.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/World")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    # Sensor container — groups all sensor prims under a single Xform
    UsdGeom.Xform.Define(stage, "/World/Sensors")

    # LiDAR sensor prim — Xform with custom simulation parameters.
    # Physical AI use: these attributes drive raycasting config in sim runtimes
    # (e.g. Isaac Sim LiDAR component reads range, FOV, channel count).
    lidar = UsdGeom.Xform.Define(stage, "/World/Sensors/LiDAR")
    p = lidar.GetPrim()
    p.CreateAttribute("sensor:type", Sdf.ValueTypeNames.Token).Set("lidar")
    p.CreateAttribute("sensor:lidar:rangeMinMeters", Sdf.ValueTypeNames.Float).Set(0.1)
    p.CreateAttribute("sensor:lidar:rangeMaxMeters", Sdf.ValueTypeNames.Float).Set(100.0)
    p.CreateAttribute("sensor:lidar:horizontalFovDeg", Sdf.ValueTypeNames.Float).Set(360.0)
    p.CreateAttribute("sensor:lidar:verticalFovDeg", Sdf.ValueTypeNames.Float).Set(30.0)
    p.CreateAttribute("sensor:lidar:numChannels", Sdf.ValueTypeNames.Int).Set(64)
    p.CreateAttribute("sensor:lidar:rotationRateHz", Sdf.ValueTypeNames.Float).Set(20.0)

    stage.Save()
    return stage
```

- [ ] **Step 4: Run all tests**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py -v
```

Expected: all 5 tests PASS

- [ ] **Step 5: Commit**

```bash
git add 02_sensor_simulation/build_sensors.py tests/02_sensor_simulation/test_build_sensors.py
git commit -m "feat: add LiDAR sensor prim with custom sensor:lidar:* attributes"
```

---

## Task 4: Camera sensor prim with custom attributes

**Files:**
- Modify: `02_sensor_simulation/build_sensors.py`
- Modify: `tests/02_sensor_simulation/test_build_sensors.py`

- [ ] **Step 1: Append failing tests**

Append to `tests/02_sensor_simulation/test_build_sensors.py`:

```python
def test_camera_prim_exists(tmp_path):
    """Stage must have /World/Sensors/Camera as a UsdGeom.Camera prim."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/World/Sensors/Camera")
    assert prim.IsValid(), "/World/Sensors/Camera not found"
    assert prim.GetTypeName() == "Camera", "/World/Sensors/Camera must be a Camera prim"


def test_camera_intrinsics(tmp_path):
    """Camera prim must have standard UsdGeom.Camera intrinsic attributes set."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    cam_api = UsdGeom.Camera(stage.GetPrimAtPath("/World/Sensors/Camera"))
    assert cam_api.GetFocalLengthAttr().Get() == pytest.approx(24.0), \
        "focalLength must be 24.0 mm"
    assert cam_api.GetHorizontalApertureAttr().Get() == pytest.approx(36.0), \
        "horizontalAperture must be 36.0 mm"
    assert cam_api.GetVerticalApertureAttr().Get() == pytest.approx(20.25), \
        "verticalAperture must be 20.25 mm"


def test_camera_custom_attributes(tmp_path):
    """Camera prim must have sensor:camera:* custom resolution attributes."""
    out = str(tmp_path / "sensors.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/World/Sensors/Camera")

    expected = {
        "sensor:type":                (Sdf.ValueTypeNames.Token, "camera"),
        "sensor:camera:resolutionX":  (Sdf.ValueTypeNames.Int,   1920),
        "sensor:camera:resolutionY":  (Sdf.ValueTypeNames.Int,   1080),
    }
    for attr_name, (expected_type, expected_val) in expected.items():
        attr = prim.GetAttribute(attr_name)
        assert attr.IsValid(), f"attribute '{attr_name}' missing"
        assert attr.GetTypeName() == expected_type, \
            f"'{attr_name}' type: expected {expected_type}, got {attr.GetTypeName()}"
        assert attr.Get() == expected_val, \
            f"'{attr_name}' value: expected {expected_val}, got {attr.Get()}"
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py::test_camera_prim_exists -v
```

Expected: FAIL — `/World/Sensors/Camera not found`

- [ ] **Step 3: Add Camera prim to build_sensors()**

In `build_sensors.py`, add the Camera block inside `build_sensors()` after the LiDAR block, before `stage.Save()`:

```python
    # Camera sensor prim — uses UsdGeom.Camera for standard lens intrinsics.
    # Physical AI use: focalLength + aperture define the optical model for
    # synthetic image generation; resolutionX/Y drive the render pipeline output size.
    cam = UsdGeom.Camera.Define(stage, "/World/Sensors/Camera")
    cam.CreateFocalLengthAttr(24.0)      # mm — wide-angle for robot perception
    cam.CreateHorizontalApertureAttr(36.0)   # mm — full-frame equivalent
    cam.CreateVerticalApertureAttr(20.25)    # mm — 16:9 aspect ratio
    cam.CreateClippingRangeAttr((0.01, 1000.0))  # near/far clip in scene units
    cp = cam.GetPrim()
    cp.CreateAttribute("sensor:type", Sdf.ValueTypeNames.Token).Set("camera")
    cp.CreateAttribute("sensor:camera:resolutionX", Sdf.ValueTypeNames.Int).Set(1920)
    cp.CreateAttribute("sensor:camera:resolutionY", Sdf.ValueTypeNames.Int).Set(1080)
```

- [ ] **Step 4: Run all tests**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_build_sensors.py -v
```

Expected: all 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add 02_sensor_simulation/build_sensors.py tests/02_sensor_simulation/test_build_sensors.py
git commit -m "feat: add Camera sensor prim with UsdGeom.Camera intrinsics and custom attributes"
```

---

## Task 5: validate_sensors.py + usdchecker integration test

**Files:**
- Create: `02_sensor_simulation/validate_sensors.py`
- Create: `tests/02_sensor_simulation/test_validate_sensors.py`

- [ ] **Step 1: Create test_validate_sensors.py**

```python
"""Integration test: generated sensors.usda must pass usdchecker with zero errors."""
import sys
import shutil
import pathlib
import subprocess

import pytest

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "02_sensor_simulation"
sys.path.insert(0, str(MODULE_DIR))


def test_validate_sensors_exits_zero(tmp_path):
    """validate_sensors.py must exit 0 on a valid sensors stage."""
    import build_sensors as bs
    out = str(tmp_path / "sensors.usda")
    bs.build_sensors(out)

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_sensors.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_sensors.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
```

- [ ] **Step 2: Run to confirm failure**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_validate_sensors.py -v
```

Expected: FAIL — `validate_sensors.py` not found

- [ ] **Step 3: Create 02_sensor_simulation/validate_sensors.py**

```python
"""
validate_sensors.py — runs usdchecker on a sensors stage and exits non-zero on errors.

Physical AI purpose:
  usdchecker compliance guarantees the sensor stage loads cleanly in any USD
  runtime. Custom attributes with valid Sdf types pass usdchecker without errors,
  confirming they are spec-compliant and not runtime-specific hacks.

Usage:
    python validate_sensors.py [path/to/sensors.usda]
    Exit code 0 = clean. Non-zero = errors found (printed to stdout).
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
        os.path.dirname(__file__), "output", "sensors.usda"
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
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/test_validate_sensors.py -v
```

Expected: PASS

- [ ] **Step 5: Run full suite**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
pytest tests/02_sensor_simulation/ -v
```

Expected: all 9 tests PASS

- [ ] **Step 6: Commit**

```bash
git add 02_sensor_simulation/validate_sensors.py tests/02_sensor_simulation/test_validate_sensors.py
git commit -m "feat: add validate_sensors.py with usdchecker integration test"
```

---

## Task 6: Generate and commit output/sensors.usda

**Files:**
- Create/update: `02_sensor_simulation/output/sensors.usda`

- [ ] **Step 1: Run build_sensors.py standalone**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
python 02_sensor_simulation/build_sensors.py
```

Expected: `Saved: .../02_sensor_simulation/output/sensors.usda`

- [ ] **Step 2: Validate the file**

```bash
python 02_sensor_simulation/validate_sensors.py 02_sensor_simulation/output/sensors.usda
```

Expected: `usdchecker PASSED: .../sensors.usda`

- [ ] **Step 3: Inspect it is ASCII**

```bash
head -10 02_sensor_simulation/output/sensors.usda
```

Expected: starts with `#usda 1.0`, human-readable prims visible

- [ ] **Step 4: Run full test suite**

```bash
pytest tests/02_sensor_simulation/ -v
```

Expected: all 9 tests PASS

- [ ] **Step 5: Commit**

```bash
git add 02_sensor_simulation/output/sensors.usda
git commit -m "chore: commit generated sensors.usda for diff visibility"
```

---

## Task 7: Update CLAUDE.md session handoff

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark module 02 complete**

In `CLAUDE.md`, update the `### Completed:` section:

```markdown
### Completed:
- [x] 01_scene_assembly — LIVRPS composition, VariantSets, defaultPrim, usdchecker ✓
- [x] 02_sensor_simulation — custom sensor:lidar:* and sensor:camera:* attributes, UsdGeom.Camera ✓
- [ ] 03_robot_asset_library
- [ ] 04_physics_annotation
- [ ] 05_tensorrt_inference_bridge
- [ ] 06_ros2_usdz_export
```

Update `### Next session should start with:`:

```
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
- Custom attributes for LiDAR sensor → Task 3 ✓
- Custom attributes for camera sensor → Task 4 ✓
- `build_*.py` + `validate_*.py` convention → Tasks 2 & 5 ✓
- usdchecker zero errors → Task 5 ✓
- Runnable standalone → Task 2 (`__main__` block) ✓
- `.usda` ASCII output → Task 6 step 3 ✓
- `UsdGeom.Camera` for camera (not just Xform) → Task 4 ✓

**Placeholder scan:** No TBD, TODO, or "similar to Task N" entries found.

**Type consistency:**
- `build_sensors(output_path: str) -> Usd.Stage` — introduced Task 2, used identically in Tasks 3, 4, 5, 6 ✓
- `validate(scene_path: str) -> list[str]` — introduced Task 5, same signature as `validate_scene.py` ✓
- Attribute names: `sensor:lidar:rangeMinMeters`, `sensor:lidar:rangeMaxMeters`, etc. — defined in Task 3 and referenced identically in test assertions ✓
- `sensor:camera:resolutionX`, `sensor:camera:resolutionY` — defined Task 4, referenced in test ✓
