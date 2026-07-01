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
