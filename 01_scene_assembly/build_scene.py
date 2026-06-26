"""
build_scene.py — generates a USD scene demonstrating LIVRPS composition.

Physical AI purpose:
  A well-composed USD stage is the foundation for robot simulation pipelines.
  LIVRPS (Local, Inherits, VariantSets, References, Payloads, Specializes) defines
  opinion strength ordering; understanding it is required for multi-asset robot scenes.
"""
import os
from pxr import Usd, UsdGeom


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_scene(output_path: str) -> Usd.Stage:
    """Create and save a USD scene; return the open stage.

    Physical AI purpose:
      defaultPrim tells downstream consumers (ROS2 bridge, Isaac Sim loader) which
      prim is the entry point without requiring path negotiation. upAxis=Y and
      metersPerUnit=1.0 are required conventions for robot simulation runtimes that
      enforce SI units and consistent gravity direction.
    """
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

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "scene.usda")
    build_scene(out)
    print(f"Saved: {out}")
