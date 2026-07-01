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

    # Double (not Float): these are custom attributes with no schema constraint,
    # so store full precision rather than forcing float32 rounding on consumers.
    float_attrs = {
        "sensor:lidar:minRange":            (Sdf.ValueTypeNames.Double, 0.1),
        "sensor:lidar:maxRange":            (Sdf.ValueTypeNames.Double, 100.0),
        "sensor:lidar:horizontalFovStart":  (Sdf.ValueTypeNames.Double, -180.0),
        "sensor:lidar:horizontalFovEnd":    (Sdf.ValueTypeNames.Double, 180.0),
        "sensor:lidar:verticalFovLower":    (Sdf.ValueTypeNames.Double, -15.0),
        "sensor:lidar:verticalFovUpper":    (Sdf.ValueTypeNames.Double, 15.0),
        "sensor:lidar:rotationFrequency":   (Sdf.ValueTypeNames.Double, 10.0),
        "sensor:lidar:horizontalResolution":(Sdf.ValueTypeNames.Double, 0.2),
    }
    for name, (type_name, value) in float_attrs.items():
        prim.CreateAttribute(name, type_name).Set(value)

    prim.CreateAttribute("sensor:lidar:numChannels", Sdf.ValueTypeNames.Int).Set(16)
    return lidar


def _add_camera(stage: Usd.Stage, path: str) -> UsdGeom.Camera:
    """Define a Camera sensor prim with standard and custom attributes.

    Physical AI purpose:
      UsdGeom.Camera standardises intrinsic parameters so any USD-aware
      renderer or vision pipeline can extract focal length and aperture
      without bespoke parsing. Custom sensor:camera: attrs carry
      runtime-specific config (resolution, frame rate) in the same prim.
    """
    cam = UsdGeom.Camera.Define(stage, path)
    # Standard UsdGeom.Camera intrinsics (millimetre units per USD convention)
    cam.CreateFocalLengthAttr().Set(24.0)           # 24 mm — wide-angle robot camera
    cam.CreateHorizontalApertureAttr().Set(20.955)  # APS-C sensor width
    cam.CreateVerticalApertureAttr().Set(15.2908)   # APS-C sensor height
    cam.CreateClippingRangeAttr().Set((0.1, 1000.0))

    # Custom sensor attributes for runtime config
    prim = cam.GetPrim()
    prim.CreateAttribute("sensor:type", Sdf.ValueTypeNames.Token).Set("camera")
    prim.CreateAttribute("sensor:camera:imageWidth",  Sdf.ValueTypeNames.Int).Set(1920)
    prim.CreateAttribute("sensor:camera:imageHeight", Sdf.ValueTypeNames.Int).Set(1080)
    # Double (not Float): custom attribute, no schema constraint — full precision.
    prim.CreateAttribute("sensor:camera:frameRate",   Sdf.ValueTypeNames.Double).Set(30.0)
    return cam


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
    _add_camera(stage, "/SensorRig/Camera")

    stage.Save()
    return stage


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    out = os.path.join(OUTPUT_DIR, "sensor_rig.usda")
    build_sensors(out)
    print(f"Saved: {out}")
