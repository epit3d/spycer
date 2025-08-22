import unittest
import sys
import types
import os

# Ensure the src package can be imported
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

# Stub heavy dependencies not required for parser logic
def _prepare_transform(*args, **kwargs):
    class _Tf:
        def TransformPoint(self, pt):
            return pt

    return _Tf()

gui_utils_module = types.ModuleType("src.gui_utils")
gui_utils_module.prepareTransform = _prepare_transform
sys.modules["src.gui_utils"] = gui_utils_module
sys.modules["vtk"] = types.ModuleType("vtk")
sys.modules["stk"] = types.ModuleType("stk")

settings_module = types.ModuleType("src.settings")


class _Hardware:
    rotation_center_x = 0
    rotation_center_y = 0
    rotation_center_z = 0


class _Slicing:
    print_time = 0
    consumption_material = 0
    planes_contact_with_nozzle = ""


_settings = types.SimpleNamespace(hardware=_Hardware(), slicing=_Slicing())


def sett():
    return _settings


settings_module.sett = sett

import importlib
src_pkg = importlib.import_module("src")
src_pkg.settings = settings_module
sys.modules["src.settings"] = settings_module

from src.gcode import parseRotation, Rotation, parseGCode, Printer


def parseArgs(args, X, Y, Z, abs_pos=True):
    """Wrapper around Printer to mimic legacy parseArgs behaviour."""
    printer = Printer(sett())
    printer.currPos = types.SimpleNamespace(X=X, Y=Y, Z=Z, U=0, V=0, E=0)
    if abs_pos:
        printer.setAbsPos(args)
    else:
        printer.setRelPos(args)
    return (
        printer.currPos.X,
        printer.currPos.Y,
        printer.currPos.Z,
        None,
    )


class TestParseGCode(unittest.TestCase):
    def testParseArgs(self):
        self.assertEqual((0, 0, 0, None), parseArgs([], 0, 0, 0))
        self.assertEqual((1, 3, 4, None), parseArgs(["X1"], 0, 3, 4))
        self.assertEqual((1.11, 2.22, 4, None), parseArgs(["Y2.22"], 1.11, 3, 4))
        self.assertEqual(
            (1.11, 2.22, 3.33, None), parseArgs(["Y2.22", "Z3.33"], 1.11, 8, 9)
        )
        self.assertEqual(
            (4.44, 2.22, 3.33, None), parseArgs(["Y2.22", "Z3.33", "X4.44"], 1.11, 8, 9)
        )
        self.assertEqual(
            (1.11, 2.22, 53.3299999999999983, None),
            parseArgs(["Y2.22", "Z53.33"], 1.11, 8, 9),
        )
        self.assertEqual(
            (1.11, 2.22, 9, None),
            parseArgs(["Y2.22", ";comment", "about", "smtg"], 1.11, 8, 9),
        )

        self.assertEqual(
            (1.11, 10.22, 9, None), parseArgs(["Y2.22"], 1.11, 8, 9, False)
        )
        self.assertEqual(
            (4.11, 8, 11.22, None), parseArgs(["Z+2.22", "X-1"], 5.11, 8, 9, False)
        )

    def testParseRotation(self):
        self.assertEqual(0, parseRotation([]))
        self.assertEqual(3.3, parseRotation(["U3.3"]))
        self.assertEqual(-4.4, parseRotation(["V-4.4", ";other", "stuff"]))

    def testParseGCode(self):
        gcode = [
            "G0 X0 Y0 Z0",
            "G1 X1 Y0 Z0 E1",
            ";LAYER:1",
            "G0 X0 Y0 Z0",
            "G1 X1 Y1 Z0 E2",
            "G0 U35;rotation",
            ";End",
        ]
        result = parseGCode(gcode)
        self.assertEqual(4, len(result.layers))
        self.assertEqual(
            [(0, 0), (0, 35.0)],
            [(r.x_rot, r.z_rot) for r in result.rotations],
        )
        self.assertEqual([0, 0, 0, 1], result.lays2rots)
        first_path = [(p.x, p.y, p.z) for p in result.layers[0][0]]
        self.assertEqual([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)], first_path)
        second_path = [(p.x, p.y, p.z) for p in result.layers[2][0]]
        self.assertEqual([(0.0, 0.0, 0.0), (1.0, 1.0, 0.0)], second_path)


if __name__ == "__main__":
    unittest.main()
