"""
build_scene.py — generates a USD scene demonstrating LIVRPS composition.

Physical AI purpose:
  A well-composed USD stage is the foundation for robot simulation pipelines.
  LIVRPS (Local, Inherits, VariantSets, References, Payloads, Specializes) defines
  opinion strength ordering; understanding it is required for multi-asset robot scenes.
"""
import os
import shutil
from pxr import Usd, UsdGeom


OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_scene(output_path: str, robot_stub_path: str | None = None) -> Usd.Stage:
    """Create and save a USD scene; return the open stage.

    Physical AI purpose:
      defaultPrim tells downstream consumers (ROS2 bridge, Isaac Sim loader) which
      prim is the entry point without requiring path negotiation. upAxis=Y and
      metersPerUnit=1.0 are required conventions for robot simulation runtimes that
      enforce SI units and consistent gravity direction.

    Args:
        output_path: Where to write the .usda file.
        robot_stub_path: Path to a robot stub .usda to reference.
                         Defaults to "./robot_stub.usda" (relative to the output stage).
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

    # Reference: robot stub — demonstrates LIVRPS 'R' (References) layer.
    # Physical AI use: robot assets are maintained separately and referenced in;
    # this decouples scene layout from robot asset versioning.
    if robot_stub_path is None:
        robot_stub_path = "./robot_stub.usda"
    robot_xform = UsdGeom.Xform.Define(stage, "/World/Robot")
    robot_xform.GetPrim().GetReferences().AddReference(robot_stub_path)

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    # Copy robot_stub.usda next to scene.usda so the relative reference resolves
    stub_src = os.path.join(os.path.dirname(__file__), "robot_stub.usda")
    stub_dst = os.path.join(OUTPUT_DIR, "robot_stub.usda")
    if not os.path.exists(stub_dst):
        shutil.copy(stub_src, stub_dst)
    out = os.path.join(OUTPUT_DIR, "scene.usda")
    build_scene(out)
    print(f"Saved: {out}")
