"""Tests for 02_sensor_simulation/build_sensors.py."""
import sys
import pathlib

import pytest

sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))

import build_sensors as bs  # noqa: E402
from pxr import UsdGeom


def test_pxr_imports():
    """Confirm usd-core is installed and required pxr modules are importable."""
    from pxr import Usd, UsdGeom, Sdf  # ImportError = test failure


def test_stage_has_default_prim(tmp_path):
    """Stage metadata must declare a defaultPrim."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert stage.GetDefaultPrim().IsValid(), "defaultPrim not set"


def test_stage_up_axis_and_units(tmp_path):
    """Stage must use Y-up and metersPerUnit=1.0 (SI robot sim convention)."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    assert UsdGeom.GetStageUpAxis(stage) == UsdGeom.Tokens.y
    assert UsdGeom.GetStageMetersPerUnit(stage) == 1.0


def test_lidar_prim_exists(tmp_path):
    """LiDAR sensor prim must exist at /SensorRig/LiDAR as an Xform."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    assert prim.IsValid(), "/SensorRig/LiDAR prim not found"
    assert prim.GetTypeName() == "Xform", "LiDAR prim must be Xform"


def test_lidar_attributes_present(tmp_path):
    """LiDAR prim must carry all required sensor:lidar: custom attributes."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    expected = [
        "sensor:type",
        "sensor:lidar:minRange",
        "sensor:lidar:maxRange",
        "sensor:lidar:horizontalFovStart",
        "sensor:lidar:horizontalFovEnd",
        "sensor:lidar:verticalFovLower",
        "sensor:lidar:verticalFovUpper",
        "sensor:lidar:rotationFrequency",
        "sensor:lidar:horizontalResolution",
        "sensor:lidar:numChannels",
    ]
    for name in expected:
        attr = prim.GetAttribute(name)
        assert attr.IsValid(), f"LiDAR attribute '{name}' missing"


def test_lidar_attribute_values(tmp_path):
    """LiDAR custom attributes must hold the expected default values."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/LiDAR")
    assert prim.GetAttribute("sensor:type").Get() == "lidar"
    # sensor:lidar:* are stored as 32-bit Float (matches Isaac Sim's
    # RangeSensorCreateLidar schema); approx accounts for float32 rounding.
    assert prim.GetAttribute("sensor:lidar:minRange").Get() == pytest.approx(0.1)
    assert prim.GetAttribute("sensor:lidar:maxRange").Get() == pytest.approx(100.0)
    assert prim.GetAttribute("sensor:lidar:horizontalFovStart").Get() == pytest.approx(-180.0)
    assert prim.GetAttribute("sensor:lidar:horizontalFovEnd").Get() == pytest.approx(180.0)
    assert prim.GetAttribute("sensor:lidar:verticalFovLower").Get() == pytest.approx(-15.0)
    assert prim.GetAttribute("sensor:lidar:verticalFovUpper").Get() == pytest.approx(15.0)
    assert prim.GetAttribute("sensor:lidar:rotationFrequency").Get() == pytest.approx(10.0)
    assert prim.GetAttribute("sensor:lidar:horizontalResolution").Get() == pytest.approx(0.2)
    assert prim.GetAttribute("sensor:lidar:numChannels").Get() == 16


def test_camera_prim_exists(tmp_path):
    """Camera sensor prim must exist at /SensorRig/Camera as a Camera type."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/Camera")
    assert prim.IsValid(), "/SensorRig/Camera prim not found"
    assert prim.GetTypeName() == "Camera", "Camera prim must be Camera type"


def test_camera_standard_attributes(tmp_path):
    """Camera prim must carry standard UsdGeom.Camera attributes with expected values."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    cam = UsdGeom.Camera(stage.GetPrimAtPath("/SensorRig/Camera"))
    # Focal length/aperture are stored as 32-bit Float per UsdGeom.Camera schema;
    # approx accounts for float32 rounding of non-binary-exact literals.
    assert cam.GetFocalLengthAttr().Get() == pytest.approx(24.0)
    assert cam.GetHorizontalApertureAttr().Get() == pytest.approx(20.955)
    assert cam.GetVerticalApertureAttr().Get() == pytest.approx(15.2908)
    clip = cam.GetClippingRangeAttr().Get()
    assert abs(clip[0] - 0.1) < 1e-5
    assert abs(clip[1] - 1000.0) < 1e-5


def test_camera_custom_attributes(tmp_path):
    """Camera prim must carry custom sensor:camera: attributes."""
    out = str(tmp_path / "sensor_rig.usda")
    stage = bs.build_sensors(out)
    prim = stage.GetPrimAtPath("/SensorRig/Camera")
    assert prim.GetAttribute("sensor:type").Get() == "camera"
    assert prim.GetAttribute("sensor:camera:imageWidth").Get() == 1920
    assert prim.GetAttribute("sensor:camera:imageHeight").Get() == 1080
    assert prim.GetAttribute("sensor:camera:frameRate").Get() == 30.0


def test_usdchecker_passes(tmp_path):
    """Generated sensor_rig.usda must pass usdchecker with zero errors."""
    import sys
    sys.path.insert(0, str(pathlib.Path(__file__).parents[2] / "02_sensor_simulation"))
    import validate_sensors as vs
    out = str(tmp_path / "sensor_rig.usda")
    bs.build_sensors(out)
    errors = vs.validate(out)
    assert errors == [], f"usdchecker errors: {errors}"
