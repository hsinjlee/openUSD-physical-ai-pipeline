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


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "robot.usda")
    build_robot(out)
    print(f"Saved: {out}")
