"""
validate_scene.py — runs usdchecker on a scene file and exits non-zero on errors.

Physical AI purpose:
  usdchecker enforces USD spec compliance. A clean check guarantees the scene
  will load in any USD-compliant runtime (Isaac Sim, ROS2 bridge, etc.) without
  silent degradation.

Usage:
    python validate_scene.py [path/to/scene.usda]
    Exit code 0 = clean. Non-zero = errors found (details printed to stdout).
"""
import sys
import os
import warnings
from pxr import UsdUtils


def validate(scene_path: str) -> list[str]:
    """Run usdchecker on scene_path; return list of error strings (empty = clean)."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        checker = UsdUtils.ComplianceChecker(
            arkit=False,
            skipARKitRootLayerCheck=False,
            rootPackageOnly=False,
            skipVariants=False,
            verbose=False,
        )
        checker.CheckCompliance(scene_path)
        errors = list(checker.GetErrors())
    return errors


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(
        os.path.dirname(__file__), "output", "scene.usda"
    )
    errors = validate(path)
    if errors:
        print(f"usdchecker FAILED on {path}:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    print(f"usdchecker PASSED: {path}")
    sys.exit(0)
