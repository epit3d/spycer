import unittest

from gcode import parseArgs, parseRotation, Rotation, parseGCode


class TestParseGCode(unittest.TestCase):
    def testParseArgs(self):
        self.assertEqual((0, 0, 0), parseArgs([], 0, 0, 0))
        self.assertEqual((1, 3, 4), parseArgs(["X1"], 0, 3, 4))
        self.assertEqual((1.11, 2.22, 4), parseArgs(["Y2.22"], 1.11, 3, 4))
        self.assertEqual((1.11, 2.22, 3.33), parseArgs(["Y2.22", "Z3.33"], 1.11, 8, 9))
        self.assertEqual((4.44, 2.22, 3.33), parseArgs(["Y2.22", "Z3.33", "X4.44"], 1.11, 8, 9))
        self.assertEqual((1.11, 2.22, 9), parseArgs(["Y2.22", ";comment", "about", "smtg"], 1.11, 8, 9))

    def testParseRotation(self):
        compare = {
            Rotation(0, 0): parseRotation([]),
            Rotation(-3.3, 0): parseRotation(["X3.3"]),
            Rotation(-3.3, -4.4): parseRotation(["X3.3", "Z4.4"]),
            Rotation(-3.3, -4.4): parseRotation(["X3.3", "Z4.4", ";other", "stuff"]),
        }
        for expected, got in compare.items():
            self.assertEqual(expected.x_rot, got.x_rot)
            self.assertEqual(expected.z_rot, got.z_rot)

    def testParseGCode(self):
        gcode = [
            ";LAYER:0",
            "G0 F1800 X81.848 Y55.873 Z0.2",
            "G1 F1650 X83.547 Z1.5 Y53.478 E0.09767",
            ";Put printing message on LCD screen",
            "G1 X83.756 Y53.208 E0.10902",
            "G0 X56.78 Y12.34 Z0.5",
            "G1 F1650 X5 Z6 Y7 E0.09767",
            ";LAYER:1",
            "G0 X84.696 Y66.058 Z2.3",
            "G1 X85.223 Y65.95 E30.50471",
            "G62 X35 Z6.7",
            ";LAYER:2",
            "G1 X89.223 Y67.95 E30.50471",
            "G1 X23.3 Z4.45",
            "G0 F1800 X85.188 Y66.146"
        ]
        layers, rotations, lays2rots = parseGCode(gcode)

        self.assertEqual(3, len(layers))
        self.assertSequenceEqual(layers[0],
                                 [[[81.848, 55.873, 0.2], [83.547, 53.478, 1.5], [83.756, 53.208, 1.5]],
                                  [[56.78, 12.34, 0.5], [5, 7, 6]]])
        self.assertSequenceEqual(layers[1],
                                 [[[84.696, 66.058, 2.3], [85.223, 65.95, 2.3]]])
        self.assertSequenceEqual(layers[2],
                                 [[[85.223, 65.95, 2.3], [89.223, 67.95, 2.3], [23.3, 67.95, 4.45]]])

        self.assertEqual(2, len(rotations))
        self.assertEqual(rotations[0].x_rot, 0)
        self.assertEqual(rotations[0].z_rot, 0)
        self.assertEqual(rotations[1].x_rot, -35)
        self.assertEqual(rotations[1].z_rot, -6.7)

        self.assertSequenceEqual([0, 0, 1], lays2rots)


if __name__ == '__main__':
    unittest.main()
