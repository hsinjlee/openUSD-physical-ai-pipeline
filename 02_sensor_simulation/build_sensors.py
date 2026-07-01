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
