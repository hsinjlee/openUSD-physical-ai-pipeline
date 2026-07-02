# CLAUDE.md — Project Brief for Claude Code

## Project Purpose
Demonstrate OpenUSD for Physical AI pipelines: scene assembly, robot asset 
description, sensor simulation, physics annotation, and TensorRT inference 
configuration. 

## Tech Stack
- Python 3.10+
- usd-core (pip) — pxr library
- No Omniverse required; all scripts must run with pip-installed usd-core only
- TensorRT references are structural/metadata only (no GPU required to run demos)

## Repo Structure
openUSD-physical-ai-pipeline/
├── CLAUDE.md
├── README.md
├── requirements.txt
├── 01_scene_assembly/
├── 02_sensor_simulation/
├── 03_robot_asset_library/
├── 04_physics_annotation/
├── 05_tensorrt_inference_bridge/
├── 06_ros2_usdz_export/
└── notebooks/

## Module Goals (build in order)
1. 01_scene_assembly     — LIVRPS composition, VariantSets, defaultPrim, usdchecker
2. 02_sensor_simulation  — Custom attributes for LiDAR/camera sensor prims
3. 03_robot_asset_library — Xform hierarchy, MaterialBindingAPI, semantic primvars
4. 04_physics_annotation  — UsdPhysics CollisionAPI, MassAPI, RevoluteJoint
5. 05_tensorrt_inference_bridge — Custom USD metadata → inference config dict
6. 06_ros2_usdz_export   — USDZ packaging, joint hierarchy mapping notes

## Coding Conventions
- Each module has: build_*.py (generates USD files) + validate_*.py (runs checks)
- Every generated .usda file must pass usdchecker with zero errors
- Add docstrings explaining the Physical AI purpose of each USD construct
- Keep scripts runnable standalone: python 01_scene_assembly/build_scene.py

## USD-Specific Rules
- Always set defaultPrim in stage metadata
- Material paths must be within defaultPrim hierarchy
- Use prepend apiSchemas for all API schemas
- Prefer .usda (ASCII) for all committed files so diffs are human-readable

## What NOT to do
- Do not use Omniverse-only APIs
- Do not hardcode absolute paths
- Do not commit large binary .usdc files
- Do not skip usdchecker validation

## Session Handoff Notes
(Update this section after each Claude Code session with what was completed
and what comes next — so the next session picks up cleanly)

### Completed:
- [x] 01_scene_assembly — LIVRPS composition, VariantSets, defaultPrim, usdchecker ✓
- [x] 02_sensor_simulation — LiDAR + Camera sensor prims, custom sensor:* attributes, usdchecker ✓
- [x] 03_robot_asset_library — Xform link hierarchy, MaterialBindingAPI, semantic primvars, usdchecker ✓
- [~] 04_physics_annotation — IN PROGRESS on branch feature/04-physics-annotation (5 of 7 plan tasks done)
- [ ] 05_tensorrt_inference_bridge
- [ ] 06_ros2_usdz_export

### Next session should start with:
Resume 04_physics_annotation on branch feature/04-physics-annotation (pushed to
origin, in sync at e6b9ce7, working tree clean).
Read the CURRENT handoff first: ~/.claude/session-data/2026-07-02-physics-04-handoff2-session.tmp
(it supersedes 2026-07-02-physics-annot-04-session.tmp, which has the fuller history).
Plan: docs/superpowers/plans/2026-07-02-04-physics-annotation.md. Tasks 1-5
implemented; Task 5 spec review done (fix c3ce2bd), quality-review fixes applied
(e6b9ce7) but the final re-review verdict is still outstanding — do that first.
Remaining: Task 6 (validate_physics.py + test, mirroring 03's validator — use
UsdUtils.ComplianceChecker, there is NO usdchecker CLI in this env) and Task 7
(finalize these handoff notes). Builder + 16 module tests (51 total) all pass.
Then final code review and merge/PR (PRs go through the hsinjlee account).
