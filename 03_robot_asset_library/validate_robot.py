"""
validate_robot.py — runs usdchecker on the robot asset and exits non-zero on errors.

Physical AI purpose:
  usdchecker enforces USD spec compliance. A clean check guarantees the robot
  asset will load in any USD-compliant runtime (Isaac Sim, ROS2 bridge, etc.)
  without silent degradation.

Usage:
    python validate_robot.py [path/to/robot.usda]
    Exit code 0 = clean. Non-zero = errors found (details printed to stdout).
"""
import sys
import os
import warnings
from pxr import UsdUtils


def validate(scene_path: str) -> list[str]:
    """Run usdchecker on scene_path; return list of error strings (empty = clean)."""
    # TODO: UsdUtils.ComplianceChecker is deprecated in usd-core ≥24.x in favour of
    # the Usd Validation Framework. Migrate when usd-core drops ComplianceChecker.
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
        os.path.dirname(__file__), "output", "robot.usda"
    )
    errors = validate(path)
    if errors:
        print(f"usdchecker FAILED on {path}:")
        for e in errors:
            print(f"  {e}")
        sys.exit(1)
    print(f"usdchecker PASSED: {path}")
    sys.exit(0)
