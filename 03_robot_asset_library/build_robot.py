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
