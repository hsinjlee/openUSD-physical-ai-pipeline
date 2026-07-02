# Design: 04_physics_annotation

**Date:** 2026-07-02
**Status:** Approved by user (scope + architecture chosen via Q&A)

## Goal

Demonstrate UsdPhysics annotation of an existing robot asset — CollisionAPI,
MassAPI, RevoluteJoint plus the supporting schemas needed for a
simulation-complete scene (RigidBodyAPI, FixedJoint, ArticulationRootAPI,
PhysicsScene) — authored **non-destructively** as an overlay layer on top of
module 03's `robot.usda`.

## Architecture: non-destructive physics overlay

`build_physics.py`:

1. Imports `build_robot()` from `03_robot_asset_library` (via a relative
   `sys.path` insert — no hardcoded absolute paths) and regenerates
   `03_robot_asset_library/output/robot.usda` on every run (deterministic).
2. Creates `04_physics_annotation/output/robot_physics.usda` whose root layer
   **sublayers** `../../03_robot_asset_library/output/robot.usda` via a
   relative asset path.
3. Authors all physics opinions as `over` prims (plus new `def` prims for
   joints/scene) in the overlay layer only. `robot.usda` is never modified.

This demonstrates the flagship Physical AI workflow: physics-annotating an
asset you don't own, with opinions cleanly separated by layer (LIVRPS).

## Physics prims and schemas

All API schemas applied with `prepend apiSchemas` (repo rule).

| Prim | Schema(s) | Key opinions |
|------|-----------|--------------|
| `/Robot` | `PhysicsArticulationRootAPI` | marks joint chain as one articulation (Isaac Sim convention for robots) |
| `/Robot/Base` | `PhysicsRigidBodyAPI`, `PhysicsMassAPI` | `physics:mass = 10.0` kg |
| `/Robot/Base/Geom` | `PhysicsCollisionAPI` | collision on the shape prim, not the link Xform |
| `/Robot/Arm` | `PhysicsRigidBodyAPI`, `PhysicsMassAPI` | `physics:mass = 2.0` kg |
| `/Robot/Arm/Geom` | `PhysicsCollisionAPI` | |
| `/Robot/FixedBaseJoint` | `PhysicsFixedJoint` (def) | `body1 = /Robot/Base`, body0 empty = world; anchors robot under gravity |
| `/Robot/ArmJoint` | `PhysicsRevoluteJoint` (def) | `body0 = /Robot/Base`, `body1 = /Robot/Arm`, `axis = Z`, limits ±90° |
| `/Robot/PhysicsScene` | `PhysicsScene` (def) | gravity direction (0, −1, 0), magnitude 9.81 — matches Y-up, meters stage |

Joint anchor: placed at the Arm cube's bottom face, world y = 0.75 (Arm link
sits at y = 1.0 and its cube has size 0.5, so the cube spans y = 0.75–1.25;
the Base cube spans y = −0.5–0.5). Expressed per body frame:
`localPos0 = (0, 0.75, 0)` in Base frame, `localPos1 = (0, −0.25, 0)` in Arm
frame.

`PhysicsScene` lives under `/Robot` so every prim stays inside the
defaultPrim hierarchy; the docstring notes production scenes usually place it
at stage root.

## Files

Mirrors module 03 exactly:

- `04_physics_annotation/build_physics.py` — builder; every construct gets a
  docstring explaining its Physical AI purpose.
- `04_physics_annotation/validate_physics.py` — usdchecker runner, same
  contract as 03's (`exit 0` clean, non-zero with errors printed; default path
  `output/robot_physics.usda`, optional argv override).
- `tests/04_physics_annotation/test_build_physics.py`
- `tests/04_physics_annotation/test_validate_physics.py`

## Testing

Pytest on the **composed** stage (`Usd.Stage.Open` on the overlay):

- Each API schema present on the correct prim (`HasAPI` / apiSchemas
  metadata).
- Mass values (10.0 / 2.0).
- RevoluteJoint `body0`/`body1` relationship targets, `axis = Z`,
  `lowerLimit = −90`, `upperLimit = 90`.
- FixedJoint anchors Base to world (`body1` set, `body0` empty).
- PhysicsScene gravity direction/magnitude.
- **Non-destructiveness:** after a full build, 03's `robot.usda` layer
  contains no physics opinions — all physics lives in the overlay layer.
- `validate_physics.py` behavior mirrors 03's validator tests.

Validation gate: `robot_physics.usda` passes usdchecker with zero errors.

## Error handling

- No hardcoded absolute paths (relative sublayer path, `os.path` from
  `__file__`).
- Builder creates `output/` dirs as needed.
- Validator exits non-zero with errors printed to stdout.

## Out of scope

- Drive/actuation APIs (`PhysicsDriveAPI`) — module 04 is annotation only.
- Running an actual simulation — no physics engine in this repo.
- Collision meshes beyond the existing Cube shapes.
