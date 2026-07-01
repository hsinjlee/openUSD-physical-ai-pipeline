# 03_robot_asset_library Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `03_robot_asset_library` — a USD robot asset with an Xform link hierarchy, geometry bound to materials via `MaterialBindingAPI`, and semantic-class primvars for downstream perception/segmentation pipelines.

**Architecture:** Follow the `01_scene_assembly` / `02_sensor_simulation` pattern exactly: `build_robot.py` generates `output/robot.usda`; `validate_robot.py` runs `usdchecker`; pytest lives in `tests/03_robot_asset_library/`. The stage has a single `/Robot` defaultPrim (`kind = component`) containing two links — `Base` and `Arm` — each an `Xform` with a child `Geom` (`UsdGeom.Cube`). Two `UsdShade.Material` prims (`Metal`, `Plastic`) live under `/Robot/Materials` and are bound to the two `Geom` prims via `MaterialBindingAPI`. Each `Geom` prim also carries a constant `primvars:semantic:class` string primvar (`"robot_base"` / `"robot_arm"`) for semantic segmentation ground truth.

**Tech Stack:** Python 3.10+, `usd-core` (`pxr` — `Usd`, `UsdGeom`, `UsdShade`, `Sdf`, `Kind`, `Gf`), `pytest`

**Lesson carried over from 02_sensor_simulation:** any custom numeric attribute with no schema constraint must use `Sdf.ValueTypeNames.Double` (not `Float`), so tests can use exact `==` instead of `pytest.approx`. This plan applies that rule throughout. `UsdGeom.Cube`'s `size` attribute and `UsdShade.Shader` PBR inputs (`diffuseColor`, `metallic`, `roughness`) ARE schema-constrained to `Float`/`Color3f` — those legitimately need `pytest.approx` where the literal isn't float32-exact.

All API calls in this plan (`Usd.ModelAPI(...).SetKind`, `UsdGeom.XformCommonAPI(...).SetTranslate`, `UsdShade.MaterialBindingAPI.Apply(...).Bind(...)`, `UsdGeom.PrimvarsAPI(...).CreatePrimvar(...)`) were verified interactively against the installed `usd-core` before writing this plan, including a full `usdchecker` pass on the assembled stage — zero errors.

---

## File Map

| Action | Path | Responsibility |
|--------|------|----------------|
| Create | `03_robot_asset_library/build_robot.py` | Stage builder — Base/Arm link hierarchy, materials, bindings, semantic primvars |
| Create | `03_robot_asset_library/validate_robot.py` | usdchecker wrapper (exit 0 = clean) |
| Create | `tests/03_robot_asset_library/__init__.py` | Makes pytest discover this package |
| Create | `tests/03_robot_asset_library/test_build_robot.py` | Unit tests for build_robot.py |
| Create | `tests/03_robot_asset_library/test_validate_robot.py` | CLI subprocess test for validate_robot.py |

---

## Task 1: Test file skeleton + pxr import smoke test

**Files:**
- Create: `tests/03_robot_asset_library/__init__.py`
- Create: `tests/03_robot_asset_library/test_build_robot.py`
- Create: `03_robot_asset_library/build_robot.py` (stub)

- [ ] **Step 1: Create the empty `__init__.py`**

```bash
touch /home/f042/p/openUSD-physical-ai-pipeline/tests/03_robot_asset_library/__init__.py
```

- [ ] **Step 2: Write the test file with an import smoke test**

Create `tests/03_robot_asset_library/test_build_robot.py`:

```python
"""Tests for 03_robot_asset_library/build_robot.py."""
import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "03_robot_asset_library"))

import build_robot as br  # noqa: E402


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, UsdShade, Sdf, Kind, Gf  # ImportError = test failure
```

- [ ] **Step 3: Run the test — expect ImportError for `build_robot`**

```bash
cd /home/f042/p/openUSD-physical-ai-pipeline
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_pxr_imports -v
```

Expected output: `ModuleNotFoundError: No module named 'build_robot'`

- [ ] **Step 4: Create a stub `build_robot.py` so the import resolves**

Create `03_robot_asset_library/build_robot.py`:

```python
"""
build_robot.py — generates a USD robot asset with a link hierarchy, materials,
and semantic-class primvars.

Physical AI purpose:
  A robot asset built from an Xform hierarchy with bound materials and semantic
  primvars is directly consumable by simulation (Isaac Sim), rendering, and
  synthetic-data pipelines that need per-link semantic segmentation labels —
  all from one USD file, no side-channel metadata.
"""
import os
from pxr import Usd, UsdGeom, UsdShade, Sdf, Kind, Gf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
```

- [ ] **Step 5: Run the test — expect PASS**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_pxr_imports -v
```

Expected: `PASSED`

- [ ] **Step 6: Commit**

```bash
git add tests/03_robot_asset_library/__init__.py \
        tests/03_robot_asset_library/test_build_robot.py \
        03_robot_asset_library/build_robot.py
git commit -m "test: scaffold 03_robot_asset_library test file and stub module"
```

---

## Task 2: Stage defaultPrim, metadata, and Base/Arm Xform hierarchy

**Files:**
- Modify: `tests/03_robot_asset_library/test_build_robot.py`
- Modify: `03_robot_asset_library/build_robot.py`

- [ ] **Step 1: Add the failing tests**

Append to `tests/03_robot_asset_library/test_build_robot.py`:

```python
def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_stage_up_axis_and_units(tmp_path):
    """Stage must use Y-up and metersPerUnit=1.0 (SI robot sim convention)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0


def test_robot_root_is_component_kind(tmp_path):
    """/Robot must be kind=component so downstream asset resolvers treat it as one asset."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    root = stage.GetPrimAtPath("/Robot")
    assert root.IsValid()
    assert root.GetMetadata("kind") == "component"


def test_link_hierarchy_exists(tmp_path):
    """Base and Arm links must exist as Xform prims under /Robot."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base = stage.GetPrimAtPath("/Robot/Base")
    arm = stage.GetPrimAtPath("/Robot/Arm")
    assert base.IsValid() and base.GetTypeName() == "Xform"
    assert arm.IsValid() and arm.GetTypeName() == "Xform"


def test_arm_link_is_translated_above_base(tmp_path):
    """Arm link must be offset above Base (visually distinct link positions)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    arm = UsdGeom.Xform(stage.GetPrimAtPath("/Robot/Arm"))
    translate, _, _, _, _ = UsdGeom.XformCommonAPI(arm).GetXformVectors(Usd.TimeCode.Default())
    assert translate == Gf.Vec3d(0.0, 1.0, 0.0)
```

Also add the missing imports at the top of the test file (after the `sys.path.insert` block):

```python
from pxr import Usd, UsdGeom, Gf
```

- [ ] **Step 2: Run — expect AttributeError (no `build_robot` function yet)**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_stage_has_default_prim -v
```

Expected: `AttributeError: module 'build_robot' has no attribute 'build_robot'`

- [ ] **Step 3: Implement `build_robot()` with the link hierarchy**

Replace `03_robot_asset_library/build_robot.py` with:

```python
"""
build_robot.py — generates a USD robot asset with a link hierarchy, materials,
and semantic-class primvars.

Physical AI purpose:
  A robot asset built from an Xform hierarchy with bound materials and semantic
  primvars is directly consumable by simulation (Isaac Sim), rendering, and
  synthetic-data pipelines that need per-link semantic segmentation labels —
  all from one USD file, no side-channel metadata.
"""
import os
from pxr import Usd, UsdGeom, UsdShade, Sdf, Kind, Gf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_robot(output_path: str) -> Usd.Stage:
    """Create and save a USD robot asset stage; return the open stage.

    Physical AI purpose:
      /Robot is the single entry point for the whole asset (kind=component),
      so downstream tools (asset resolvers, USD composition arcs) can reference
      or instance the entire robot by one prim path.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/Robot")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    Usd.ModelAPI(root.GetPrim()).SetKind(Kind.Tokens.component)

    # Base link — the robot's fixed-frame root link, at the origin.
    UsdGeom.Xform.Define(stage, "/Robot/Base")

    # Arm link — offset above Base. Physical AI use: link-local transforms are
    # what UsdPhysics.RevoluteJoint (module 04) will connect between parent and
    # child frames; establishing them now keeps the hierarchy joint-ready.
    arm = UsdGeom.Xform.Define(stage, "/Robot/Arm")
    UsdGeom.XformCommonAPI(arm).SetTranslate(Gf.Vec3d(0.0, 1.0, 0.0))

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "robot.usda")
    build_robot(out)
    print(f"Saved: {out}")
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_stage_has_default_prim \
                 tests/03_robot_asset_library/test_build_robot.py::test_stage_up_axis_and_units \
                 tests/03_robot_asset_library/test_build_robot.py::test_robot_root_is_component_kind \
                 tests/03_robot_asset_library/test_build_robot.py::test_link_hierarchy_exists \
                 tests/03_robot_asset_library/test_build_robot.py::test_arm_link_is_translated_above_base -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/03_robot_asset_library/test_build_robot.py \
        03_robot_asset_library/build_robot.py
git commit -m "feat: add build_robot() with defaultPrim, Base/Arm Xform link hierarchy"
```

---

## Task 3: Cube geometry under each link

**Files:**
- Modify: `tests/03_robot_asset_library/test_build_robot.py`
- Modify: `03_robot_asset_library/build_robot.py`

Each link gets a child `Geom` prim (`UsdGeom.Cube`) — the actual renderable/collidable shape. Keeping `Geom` separate from the link `Xform` matches USD convention (transform vs. shape) and gives module 04 a stable prim to attach `UsdPhysics.CollisionAPI` to later.

- [ ] **Step 1: Add the failing tests**

Append to `tests/03_robot_asset_library/test_build_robot.py`:

```python
def test_base_geom_exists(tmp_path):
    """Base link must have a child Cube prim named Geom."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    prim = stage.GetPrimAtPath("/Robot/Base/Geom")
    assert prim.IsValid()
    assert prim.GetTypeName() == "Cube"


def test_arm_geom_exists(tmp_path):
    """Arm link must have a child Cube prim named Geom, smaller than Base."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    prim = stage.GetPrimAtPath("/Robot/Arm/Geom")
    assert prim.IsValid()
    assert prim.GetTypeName() == "Cube"


def test_geom_sizes(tmp_path):
    """Base Cube must be larger than Arm Cube (visually distinct link scale)."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base_cube = UsdGeom.Cube(stage.GetPrimAtPath("/Robot/Base/Geom"))
    arm_cube = UsdGeom.Cube(stage.GetPrimAtPath("/Robot/Arm/Geom"))
    assert base_cube.GetSizeAttr().Get() == pytest.approx(1.0)
    assert arm_cube.GetSizeAttr().Get() == pytest.approx(0.5)
```

Also add `import pytest` at the top of the test file (`UsdGeom.Cube`'s `size` attribute is schema-defined as `Float` — a 32-bit round-trip, so `pytest.approx` applies here even though the literals happen to be exact; using `approx` consistently avoids re-litigating this per attribute):

```python
import pytest
```

- [ ] **Step 2: Run — expect FAIL (Geom prims don't exist yet)**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_base_geom_exists -v
```

Expected: `AssertionError` (prim invalid)

- [ ] **Step 3: Add the Cube geometry to `build_robot.py`**

Add a private helper and call it for each link. Insert into `03_robot_asset_library/build_robot.py`, after the `_` import block and before `build_robot()`:

```python
def _add_geom(stage: Usd.Stage, link_path: str, size: float) -> UsdGeom.Cube:
    """Define the renderable/collidable Cube geometry for a robot link.

    Physical AI purpose:
      Separating Geom from the link Xform lets module 04 (physics annotation)
      attach UsdPhysics.CollisionAPI directly to this shape prim without
      touching the link's transform hierarchy.
    """
    geom = UsdGeom.Cube.Define(stage, f"{link_path}/Geom")
    geom.CreateSizeAttr(size)
    return geom
```

Then update `build_robot()` to call it for both links — replace the body of `build_robot()` with:

```python
def build_robot(output_path: str) -> Usd.Stage:
    """Create and save a USD robot asset stage; return the open stage.

    Physical AI purpose:
      /Robot is the single entry point for the whole asset (kind=component),
      so downstream tools (asset resolvers, USD composition arcs) can reference
      or instance the entire robot by one prim path.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/Robot")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    Usd.ModelAPI(root.GetPrim()).SetKind(Kind.Tokens.component)

    # Base link — the robot's fixed-frame root link, at the origin.
    UsdGeom.Xform.Define(stage, "/Robot/Base")
    _add_geom(stage, "/Robot/Base", size=1.0)

    # Arm link — offset above Base. Physical AI use: link-local transforms are
    # what UsdPhysics.RevoluteJoint (module 04) will connect between parent and
    # child frames; establishing them now keeps the hierarchy joint-ready.
    arm = UsdGeom.Xform.Define(stage, "/Robot/Arm")
    UsdGeom.XformCommonAPI(arm).SetTranslate(Gf.Vec3d(0.0, 1.0, 0.0))
    _add_geom(stage, "/Robot/Arm", size=0.5)

    stage.Save()
    return stage
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_base_geom_exists \
                 tests/03_robot_asset_library/test_build_robot.py::test_arm_geom_exists \
                 tests/03_robot_asset_library/test_build_robot.py::test_geom_sizes -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/03_robot_asset_library/test_build_robot.py \
        03_robot_asset_library/build_robot.py
git commit -m "feat: add Cube geometry under Base and Arm links"
```

---

## Task 4: Materials and MaterialBindingAPI binding

**Files:**
- Modify: `tests/03_robot_asset_library/test_build_robot.py`
- Modify: `03_robot_asset_library/build_robot.py`

Two `UsdPreviewSurface` materials — `Metal` (bound to Base) and `Plastic` (bound to Arm) — live under `/Robot/Materials`, inside the `/Robot` defaultPrim hierarchy per this repo's USD rule ("Material paths must be within defaultPrim hierarchy").

- [ ] **Step 1: Add the failing tests**

Append to `tests/03_robot_asset_library/test_build_robot.py`:

```python
def test_materials_exist(tmp_path):
    """Metal and Plastic materials must exist under /Robot/Materials."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    metal = stage.GetPrimAtPath("/Robot/Materials/Metal")
    plastic = stage.GetPrimAtPath("/Robot/Materials/Plastic")
    assert metal.IsValid() and metal.GetTypeName() == "Material"
    assert plastic.IsValid() and plastic.GetTypeName() == "Material"


def test_material_shader_inputs(tmp_path):
    """Each material's UsdPreviewSurface shader must carry PBR inputs."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    metal_shader = UsdShade.Shader(stage.GetPrimAtPath("/Robot/Materials/Metal/PreviewSurface"))
    assert metal_shader.GetIdAttr().Get() == "UsdPreviewSurface"
    assert metal_shader.GetInput("metallic").Get() == pytest.approx(0.9)
    assert metal_shader.GetInput("roughness").Get() == pytest.approx(0.3)

    plastic_shader = UsdShade.Shader(stage.GetPrimAtPath("/Robot/Materials/Plastic/PreviewSurface"))
    assert plastic_shader.GetIdAttr().Get() == "UsdPreviewSurface"
    assert plastic_shader.GetInput("metallic").Get() == pytest.approx(0.0)
    assert plastic_shader.GetInput("roughness").Get() == pytest.approx(0.6)


def test_base_bound_to_metal(tmp_path):
    """Base/Geom must be bound to the Metal material via MaterialBindingAPI."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base_geom = stage.GetPrimAtPath("/Robot/Base/Geom")
    assert "MaterialBindingAPI" in base_geom.GetAppliedSchemas()
    bound, _ = UsdShade.MaterialBindingAPI(base_geom).ComputeBoundMaterial()
    assert bound.GetPath() == Sdf.Path("/Robot/Materials/Metal")


def test_arm_bound_to_plastic(tmp_path):
    """Arm/Geom must be bound to the Plastic material via MaterialBindingAPI."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    arm_geom = stage.GetPrimAtPath("/Robot/Arm/Geom")
    assert "MaterialBindingAPI" in arm_geom.GetAppliedSchemas()
    bound, _ = UsdShade.MaterialBindingAPI(arm_geom).ComputeBoundMaterial()
    assert bound.GetPath() == Sdf.Path("/Robot/Materials/Plastic")
```

Also add `from pxr import UsdShade, Sdf` at the top of the test file.

- [ ] **Step 2: Run — expect FAIL (materials don't exist yet)**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_materials_exist -v
```

Expected: `AssertionError` (prim invalid)

- [ ] **Step 3: Add materials and bindings to `build_robot.py`**

Add a private helper. Insert into `03_robot_asset_library/build_robot.py`, after `_add_geom()` and before `build_robot()`:

```python
def _add_material(
    stage: Usd.Stage,
    path: str,
    diffuse_color: tuple[float, float, float],
    metallic: float,
    roughness: float,
) -> UsdShade.Material:
    """Define a UsdPreviewSurface material.

    Physical AI purpose:
      UsdPreviewSurface is the USD-standard PBR shader — any USD-compliant
      renderer (including Isaac Sim's RTX renderer) can render this material
      without a vendor-specific shader graph.
    """
    material = UsdShade.Material.Define(stage, path)
    shader = UsdShade.Shader.Define(stage, f"{path}/PreviewSurface")
    shader.CreateIdAttr("UsdPreviewSurface")
    shader.CreateInput("diffuseColor", Sdf.ValueTypeNames.Color3f).Set(diffuse_color)
    shader.CreateInput("metallic", Sdf.ValueTypeNames.Float).Set(metallic)
    shader.CreateInput("roughness", Sdf.ValueTypeNames.Float).Set(roughness)
    material.CreateSurfaceOutput().ConnectToSource(shader.ConnectableAPI(), "surface")
    return material


def _bind_material(geom_prim: Usd.Prim, material: UsdShade.Material) -> None:
    """Bind a material to a geometry prim via MaterialBindingAPI.

    Physical AI purpose:
      MaterialBindingAPI.Apply() prepends the schema to apiSchemas (per this
      repo's USD rule) and Bind() adds the direct material:binding relationship
      that any USD-compliant renderer resolves at render time.
    """
    UsdShade.MaterialBindingAPI.Apply(geom_prim).Bind(material)
```

Then update `build_robot()` — replace the body with:

```python
def build_robot(output_path: str) -> Usd.Stage:
    """Create and save a USD robot asset stage; return the open stage.

    Physical AI purpose:
      /Robot is the single entry point for the whole asset (kind=component),
      so downstream tools (asset resolvers, USD composition arcs) can reference
      or instance the entire robot by one prim path.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/Robot")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    Usd.ModelAPI(root.GetPrim()).SetKind(Kind.Tokens.component)

    # Materials — declared under /Robot so material paths stay within the
    # defaultPrim hierarchy (this repo's USD rule).
    metal = _add_material(
        stage, "/Robot/Materials/Metal",
        diffuse_color=(0.6, 0.6, 0.65), metallic=0.9, roughness=0.3,
    )
    plastic = _add_material(
        stage, "/Robot/Materials/Plastic",
        diffuse_color=(0.9, 0.2, 0.1), metallic=0.0, roughness=0.6,
    )

    # Base link — the robot's fixed-frame root link, at the origin.
    UsdGeom.Xform.Define(stage, "/Robot/Base")
    base_geom = _add_geom(stage, "/Robot/Base", size=1.0)
    _bind_material(base_geom.GetPrim(), metal)

    # Arm link — offset above Base. Physical AI use: link-local transforms are
    # what UsdPhysics.RevoluteJoint (module 04) will connect between parent and
    # child frames; establishing them now keeps the hierarchy joint-ready.
    arm = UsdGeom.Xform.Define(stage, "/Robot/Arm")
    UsdGeom.XformCommonAPI(arm).SetTranslate(Gf.Vec3d(0.0, 1.0, 0.0))
    arm_geom = _add_geom(stage, "/Robot/Arm", size=0.5)
    _bind_material(arm_geom.GetPrim(), plastic)

    stage.Save()
    return stage
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_materials_exist \
                 tests/03_robot_asset_library/test_build_robot.py::test_material_shader_inputs \
                 tests/03_robot_asset_library/test_build_robot.py::test_base_bound_to_metal \
                 tests/03_robot_asset_library/test_build_robot.py::test_arm_bound_to_plastic -v
```

Expected: all `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/03_robot_asset_library/test_build_robot.py \
        03_robot_asset_library/build_robot.py
git commit -m "feat: add Metal/Plastic materials bound to links via MaterialBindingAPI"
```

---

## Task 5: Semantic-class primvars

**Files:**
- Modify: `tests/03_robot_asset_library/test_build_robot.py`
- Modify: `03_robot_asset_library/build_robot.py`

Each `Geom` prim carries a constant `primvars:semantic:class` string primvar — the ground-truth label a synthetic-data/segmentation pipeline reads per prim.

- [ ] **Step 1: Add the failing tests**

Append to `tests/03_robot_asset_library/test_build_robot.py`:

```python
def test_base_geom_semantic_class(tmp_path):
    """Base/Geom must carry a constant primvars:semantic:class = 'robot_base'."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    base_geom = stage.GetPrimAtPath("/Robot/Base/Geom")
    pv = UsdGeom.PrimvarsAPI(base_geom).GetPrimvar("semantic:class")
    assert pv.IsDefined(), "primvars:semantic:class missing on Base/Geom"
    assert pv.Get() == "robot_base"
    assert pv.GetInterpolation() == UsdGeom.Tokens.constant


def test_arm_geom_semantic_class(tmp_path):
    """Arm/Geom must carry a constant primvars:semantic:class = 'robot_arm'."""
    out = str(tmp_path / "robot.usda")
    stage = br.build_robot(out)
    arm_geom = stage.GetPrimAtPath("/Robot/Arm/Geom")
    pv = UsdGeom.PrimvarsAPI(arm_geom).GetPrimvar("semantic:class")
    assert pv.IsDefined(), "primvars:semantic:class missing on Arm/Geom"
    assert pv.Get() == "robot_arm"
    assert pv.GetInterpolation() == UsdGeom.Tokens.constant
```

- [ ] **Step 2: Run — expect FAIL (primvar not defined yet)**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_base_geom_semantic_class -v
```

Expected: `AssertionError: primvars:semantic:class missing on Base/Geom`

- [ ] **Step 3: Add the semantic primvar helper to `build_robot.py`**

Add a private helper. Insert into `03_robot_asset_library/build_robot.py`, after `_bind_material()` and before `build_robot()`:

```python
def _set_semantic_class(geom_prim: Usd.Prim, class_label: str) -> None:
    """Tag a geometry prim with a constant semantic-class primvar.

    Physical AI purpose:
      primvars:semantic:class is read by synthetic-data pipelines (e.g. domain
      randomization / segmentation-mask renderers) to assign a per-pixel class
      ID without a side-channel label file — the label travels with the prim.
    """
    UsdGeom.PrimvarsAPI(geom_prim).CreatePrimvar(
        "semantic:class", Sdf.ValueTypeNames.String, UsdGeom.Tokens.constant
    ).Set(class_label)
```

Then update `build_robot()` to call it for both links — replace the body with:

```python
def build_robot(output_path: str) -> Usd.Stage:
    """Create and save a USD robot asset stage; return the open stage.

    Physical AI purpose:
      /Robot is the single entry point for the whole asset (kind=component),
      so downstream tools (asset resolvers, USD composition arcs) can reference
      or instance the entire robot by one prim path.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/Robot")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)
    Usd.ModelAPI(root.GetPrim()).SetKind(Kind.Tokens.component)

    # Materials — declared under /Robot so material paths stay within the
    # defaultPrim hierarchy (this repo's USD rule).
    metal = _add_material(
        stage, "/Robot/Materials/Metal",
        diffuse_color=(0.6, 0.6, 0.65), metallic=0.9, roughness=0.3,
    )
    plastic = _add_material(
        stage, "/Robot/Materials/Plastic",
        diffuse_color=(0.9, 0.2, 0.1), metallic=0.0, roughness=0.6,
    )

    # Base link — the robot's fixed-frame root link, at the origin.
    UsdGeom.Xform.Define(stage, "/Robot/Base")
    base_geom = _add_geom(stage, "/Robot/Base", size=1.0)
    _bind_material(base_geom.GetPrim(), metal)
    _set_semantic_class(base_geom.GetPrim(), "robot_base")

    # Arm link — offset above Base. Physical AI use: link-local transforms are
    # what UsdPhysics.RevoluteJoint (module 04) will connect between parent and
    # child frames; establishing them now keeps the hierarchy joint-ready.
    arm = UsdGeom.Xform.Define(stage, "/Robot/Arm")
    UsdGeom.XformCommonAPI(arm).SetTranslate(Gf.Vec3d(0.0, 1.0, 0.0))
    arm_geom = _add_geom(stage, "/Robot/Arm", size=0.5)
    _bind_material(arm_geom.GetPrim(), plastic)
    _set_semantic_class(arm_geom.GetPrim(), "robot_arm")

    stage.Save()
    return stage
```

- [ ] **Step 4: Run — expect PASS**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_base_geom_semantic_class \
                 tests/03_robot_asset_library/test_build_robot.py::test_arm_geom_semantic_class -v
```

Expected: both `PASSED`

- [ ] **Step 5: Commit**

```bash
git add tests/03_robot_asset_library/test_build_robot.py \
        03_robot_asset_library/build_robot.py
git commit -m "feat: add primvars:semantic:class to Base/Arm Geom prims"
```

---

## Task 6: `validate_robot.py` — usdchecker wrapper + CLI test

**Files:**
- Create: `03_robot_asset_library/validate_robot.py`
- Create: `tests/03_robot_asset_library/test_validate_robot.py`
- Modify: `tests/03_robot_asset_library/test_build_robot.py`

Pattern is identical to `02_sensor_simulation/validate_sensors.py` — including the `ComplianceChecker` deprecation `TODO`, which was dropped once already in this repo's history and must not be dropped again.

- [ ] **Step 1: Create `validate_robot.py`**

```python
"""
validate_robot.py — runs usdchecker on the robot asset and exits non-zero on errors.

Physical AI purpose:
  usdchecker enforces USD spec compliance. A clean check guarantees the robot
  asset will load in any USD-compliant runtime (Isaac Sim, ROS2 bridge, etc.)
  without silent degradation.

Usage:
    python validate_robot.py [path/to/robot.usda]
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
        os.path.dirname(__file__), "output", "robot.usda"
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

- [ ] **Step 2: Add the in-process usdchecker test**

Append to `tests/03_robot_asset_library/test_build_robot.py`:

```python
def test_usdchecker_passes(tmp_path):
    """Generated robot.usda must pass usdchecker with zero errors."""
    import validate_robot as vr
    out = str(tmp_path / "robot.usda")
    br.build_robot(out)
    errors = vr.validate(out)
    assert errors == [], f"usdchecker errors: {errors}"
```

(No extra `sys.path.insert` needed here — the module-level insert at the top of the file already makes `03_robot_asset_library/` importable.)

- [ ] **Step 3: Create the CLI subprocess test**

Create `tests/03_robot_asset_library/test_validate_robot.py`:

```python
"""Integration test: generated robot.usda must pass usdchecker with zero errors."""
import sys
import pathlib
import subprocess

REPO_ROOT = pathlib.Path(__file__).parents[2]
MODULE_DIR = REPO_ROOT / "03_robot_asset_library"
sys.path.insert(0, str(MODULE_DIR))

import build_robot as br  # noqa: E402 — depends on sys.path.insert above


def test_validate_robot_exits_zero(tmp_path):
    """validate_robot.py must exit 0 when the generated robot asset is valid."""
    out = str(tmp_path / "robot.usda")
    br.build_robot(out)

    result = subprocess.run(
        [sys.executable, str(MODULE_DIR / "validate_robot.py"), out],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"validate_robot.py exited {result.returncode}\n"
        f"stdout: {result.stdout}\nstderr: {result.stderr}"
    )
```

- [ ] **Step 4: Run the new tests**

```bash
python -m pytest tests/03_robot_asset_library/test_build_robot.py::test_usdchecker_passes \
                 tests/03_robot_asset_library/test_validate_robot.py::test_validate_robot_exits_zero -v
```

Expected: both `PASSED`

- [ ] **Step 5: Generate the output file and run validate standalone**

```bash
python 03_robot_asset_library/build_robot.py
python 03_robot_asset_library/validate_robot.py
```

Expected:
```
Saved: 03_robot_asset_library/output/robot.usda
usdchecker PASSED: 03_robot_asset_library/output/robot.usda
```

- [ ] **Step 6: Run the full test suite (whole repo, no regressions)**

```bash
python -m pytest tests/ -v
```

Expected: all tests `PASSED`, zero failures — including `01_scene_assembly` and `02_sensor_simulation`.

- [ ] **Step 7: Commit**

```bash
git add 03_robot_asset_library/validate_robot.py \
        03_robot_asset_library/output/robot.usda \
        tests/03_robot_asset_library/test_build_robot.py \
        tests/03_robot_asset_library/test_validate_robot.py
git commit -m "feat: add validate_robot.py; 03_robot_asset_library complete — usdchecker passes"
```

---

## Task 7: Update CLAUDE.md session handoff

**Files:**
- Modify: `CLAUDE.md`

- [ ] **Step 1: Mark 03_robot_asset_library complete in the handoff section**

In `CLAUDE.md`, change:

```markdown
- [ ] 03_robot_asset_library
```

to:

```markdown
- [x] 03_robot_asset_library — Xform link hierarchy, MaterialBindingAPI, semantic primvars, usdchecker ✓
```

And update the "Next session should start with:" line:

```markdown
### Next session should start with:
Implement 04_physics_annotation: UsdPhysics CollisionAPI, MassAPI, RevoluteJoint.
Reference pattern: build_robot.py / validate_robot.py from 03_robot_asset_library.
The Base/Arm Geom prims are already separated from their link Xforms specifically
so CollisionAPI can attach to Geom without disturbing the transform hierarchy.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "chore: mark 03_robot_asset_library complete in session handoff notes"
```

---

## Self-Review

**Spec coverage check:**
- [x] Xform hierarchy → Task 2 (Base/Arm links)
- [x] MaterialBindingAPI → Task 4
- [x] Semantic primvars → Task 5
- [x] `build_robot.py` (generates USD files) → Tasks 2–5
- [x] `validate_robot.py` (runs usdchecker) → Task 6
- [x] defaultPrim set → Task 2
- [x] `.usda` ASCII format → `Usd.Stage.CreateNew(*.usda)` throughout
- [x] `upAxis=Y`, `metersPerUnit=1.0` → Task 2
- [x] Material paths within defaultPrim hierarchy → Task 4 (`/Robot/Materials/*`)
- [x] `prepend apiSchemas` for API schemas → Task 4 (`MaterialBindingAPI.Apply()` prepends by default)
- [x] Zero usdchecker errors → Task 6, verified interactively before writing the plan
- [x] TDD (tests before implementation) → every task follows write-test-first order
- [x] CLI subprocess coverage for validate script → Task 6 (lesson carried over from 02_sensor_simulation review)
- [x] No Float-vs-Double precision trap → all custom numeric attributes use `Double`; only schema-constrained `Float` attrs (Cube size, PBR shader inputs) use `pytest.approx`

**No placeholders:** all code blocks contain actual runnable code, verified against the installed `usd-core` (see API verification note in the header).

**Type consistency:** `build_robot(output_path: str) -> Usd.Stage` defined in Task 2, imported and called by the same signature in all subsequent tasks and tests. Helper signatures (`_add_geom`, `_add_material`, `_bind_material`, `_set_semantic_class`) are introduced once each and reused verbatim.
