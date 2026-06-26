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
