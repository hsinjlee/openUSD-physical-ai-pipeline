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


def _add_lidar(stage: Usd.Stage, path: str) -> UsdGeom.Xform:
    """Define a LiDAR sensor prim with custom attributes.

    Physical AI purpose:
      These attributes map directly to Isaac Sim's RangeSensorCreateLidar
      parameters and NVIDIA's sensor extension schema, letting the same USD
      file drive both simulation and hardware-in-the-loop configs.
    """
    lidar = UsdGeom.Xform.Define(stage, path)
    prim = lidar.GetPrim()

    # Sensor type identifier for programmatic discovery
    prim.CreateAttribute("sensor:type", Sdf.ValueTypeNames.Token).Set("lidar")

    float_attrs = {
        "sensor:lidar:minRange":            (Sdf.ValueTypeNames.Float, 0.1),
        "sensor:lidar:maxRange":            (Sdf.ValueTypeNames.Float, 100.0),
        "sensor:lidar:horizontalFovStart":  (Sdf.ValueTypeNames.Float, -180.0),
        "sensor:lidar:horizontalFovEnd":    (Sdf.ValueTypeNames.Float, 180.0),
        "sensor:lidar:verticalFovLower":    (Sdf.ValueTypeNames.Float, -15.0),
        "sensor:lidar:verticalFovUpper":    (Sdf.ValueTypeNames.Float, 15.0),
        "sensor:lidar:rotationFrequency":   (Sdf.ValueTypeNames.Float, 10.0),
        "sensor:lidar:horizontalResolution":(Sdf.ValueTypeNames.Float, 0.2),
    }
    for name, (type_name, value) in float_attrs.items():
        prim.CreateAttribute(name, type_name).Set(value)

    prim.CreateAttribute("sensor:lidar:numChannels", Sdf.ValueTypeNames.Int).Set(16)
    return lidar


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

    _add_lidar(stage, "/SensorRig/LiDAR")

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensor_rig.usda")
    build_sensors(out)
    print(f"Saved: {out}")
