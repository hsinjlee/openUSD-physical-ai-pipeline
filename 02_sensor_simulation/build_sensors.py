"""
build_sensors.py — generates a USD scene with LiDAR and camera sensor prims.

Physical AI purpose:
  Sensor prims with typed custom attributes let simulation runtimes (Isaac Sim,
  CARLA bridge) read sensor parameters directly from USD without side-channel
  config files. The sensor: namespace is a widely-used convention for
  Physical AI pipelines.
"""
import os
from pxr import Usd, UsdGeom, Sdf

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")


def build_sensors(output_path: str) -> Usd.Stage:
    """Create and save a USD sensor-rig stage; return the open stage.

    Physical AI purpose:
      /SensorRig is the mount frame for all sensors on a robot. downstream
      consumers reference this file and bind each sensor prim to a perception
      pipeline by prim path — no string config required.
    """
    stage = Usd.Stage.CreateNew(output_path)

    root = UsdGeom.Xform.Define(stage, "/SensorRig")
    stage.SetDefaultPrim(root.GetPrim())
    UsdGeom.SetStageUpAxis(stage, UsdGeom.Tokens.y)
    UsdGeom.SetStageMetersPerUnit(stage, 1.0)

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensor_rig.usda")
    build_sensors(out)
    print(f"Saved: {out}")
