"""
build_physics.py — annotates the module-03 robot asset with UsdPhysics schemas
in a non-destructive overlay layer.

Physical AI purpose:
  Physics annotation as a separate USD layer is how simulation teams add
  collision, mass, and joint definitions to assets they don't own (vendor
  robots, marketplace props). The original asset stays pristine; the overlay
  composes over it via the layer stack (LIVRPS), and any UsdPhysics runtime
  (Isaac Sim, PhysX) consumes the composed result.
"""
import os
import sys
from pxr import Usd, UsdPhysics, Sdf, Gf

MODULE_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_DIR = os.path.join(MODULE_DIR, "output")
ROBOT_MODULE_DIR = os.path.normpath(
    os.path.join(MODULE_DIR, os.pardir, "03_robot_asset_library")
)
ROBOT_USDA = os.path.join(ROBOT_MODULE_DIR, "output", "robot.usda")

sys.path.insert(0, ROBOT_MODULE_DIR)
from build_robot import build_robot  # noqa: E402 — depends on sys.path.insert


def _ensure_robot_asset() -> None:
    """(Re)generate 03's robot.usda unless its layer is already open in-process.

    Physical AI purpose:
      The overlay depends on the base asset existing on disk. Regenerating it
      keeps the demo deterministic; the Sdf.Layer.Find guard avoids re-creating
      a layer that a live stage (e.g. a previous build in the same pytest
      process) still holds open. If that live layer's backing file has been
      removed from disk, re-save it so the sublayer reference stays resolvable.
    """
    layer = Sdf.Layer.Find(ROBOT_USDA)
    if layer is None:
        os.makedirs(os.path.dirname(ROBOT_USDA), exist_ok=True)
        build_robot(ROBOT_USDA)
    elif not os.path.isfile(ROBOT_USDA):
        layer.Save(force=True)


def _add_rigid_body(stage: Usd.Stage, link_path: str, mass: float) -> None:
    """Mark a link Xform as a dynamic rigid body with an explicit mass.

    Physical AI purpose:
      RigidBodyAPI on the link Xform (not the Geom) makes the whole link one
      dynamic body; MassAPI overrides density-derived mass with the measured
      value a real robot datasheet provides — critical for sim-to-real
      transfer of dynamics.
    """
    prim = stage.GetPrimAtPath(link_path)
    UsdPhysics.RigidBodyAPI.Apply(prim)
    UsdPhysics.MassAPI.Apply(prim).CreateMassAttr(mass)


def build_physics(output_path: str) -> Usd.Stage:
    """Create and save the physics overlay stage; return the open stage.

    Physical AI purpose:
      The root layer sublayers robot.usda via a *relative* asset path, so the
      pair of files stays relocatable as a unit (no absolute paths — repo
      rule). Physics opinions authored on this stage land in the overlay
      layer, never in the base asset.

    Note: release any previously returned stage for the same output_path
    before rebuilding — Usd.Stage.CreateNew fails while the old layer is
    still open.
    """
    _ensure_robot_asset()
    stage = Usd.Stage.CreateNew(output_path)
    robot_rel = os.path.relpath(
        ROBOT_USDA, os.path.dirname(os.path.abspath(output_path))
    ).replace(os.sep, "/")
    stage.GetRootLayer().subLayerPaths.append(robot_rel)
    stage.SetDefaultPrim(stage.GetPrimAtPath("/Robot"))
    _add_rigid_body(stage, "/Robot/Base", mass=10.0)
    _add_rigid_body(stage, "/Robot/Arm", mass=2.0)
    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "robot_physics.usda")
    build_physics(out)
    print(f"Saved: {out}")
