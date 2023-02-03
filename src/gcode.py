import math
import numpy as np
from typing import List, Optional

import src.settings
from src import gui_utils
import vtk


def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis)
    axis = axis / np.sqrt(np.dot(axis, axis))
    a = np.cos(theta / 2.0)
    b, c, d = -axis * np.sin(theta / 2.0)
    aa, bb, cc, dd = a * a, b * b, c * c, d * d
    bc, ad, ac, ab, bd, cd = b * c, a * d, a * c, a * b, b * d, c * d
    return np.array([[aa + bb - cc - dd, 2 * (bc + ad),
                      2 * (bd - ac)], [2 * (bc - ad), aa + cc - bb - dd, 2 * (cd + ab)],
                     [2 * (bd + ac), 2 * (cd - ab), aa + dd - bb - cc]])


class GCode:

    def __init__(self, layers, rotations, lays2rots):
        self.layers: List[List[Point]] = layers
        self.rotations: List[Rotation] = rotations
        self.lays2rots = lays2rots


class Rotation:

    def __init__(self, x, z):
        self.x_rot = x
        self.z_rot = z

    def __str__(self):
        return " x:" + str(self.x_rot) + " z:" + str(self.z_rot)


class Point:

    def __init__(self, x, y, z, a, b):
        self.x = x
        self.y = y
        self.z = z
        self.a = a
        self.b = b

    def xyz(self, rot):
        cur = [self.x, self.y, self.z]
        if self.a == 0:
            return cur
        tf = gui_utils.prepareTransform(Rotation(self.a, self.b), rot)
        res = tf.TransformPoint(cur)
        return res


def parseArgs(args, x, y, z, a, b, cone_axis, rotationPoint, absolute=True):
    xr, yr, zr, ar, br = 0, 0, 0, 0, 0
    if absolute:
        xr, yr, zr, ar, br = x, y, z, a, b

    for arg in args:
        if len(arg) == 0:
            continue
        if arg[0] == "X":
            xr = float(arg[1:])
        elif arg[0] == "Y":
            yr = float(arg[1:])
        elif arg[0] == "Z":
            zr = float(arg[1:])
        elif arg[0] == "A":
            ar = float(arg[1:])
        elif arg[0] == "B":
            br = float(arg[1:])
        elif arg[0] == ";":
            break
        elif arg[0] == "U":  # rotation around z of bed planer
            import numpy as np

            # convert from cylindrical coordinates to xyz
            u = math.radians(float(arg[1:]))
            r = yr
            z = zr

            xr, yr, zr = rotation_matrix(cone_axis, -u).dot(np.array([xr, r, z]) - rotationPoint) + rotationPoint
    if absolute:
        return xr, yr, zr, ar, br
    return xr + x, yr + y, zr + z, ar + a, br + b


def parseRotation(args: List[str]):
    e = 0
    for arg in args:
        if len(arg) == 0:
            continue
        if arg[0].lower() == "U".lower() or arg[0].lower() == "V".lower():
            e = float(arg[1:])
        elif arg[0] == ";":
            break
    return e


def readGCode(filename):
    with open(filename) as f:
        lines = [line.strip() for line in f]
    return parseGCode(lines)


def parseGCode(lines):
    path = []
    layer = []
    layers = []
    rotations = []
    lays2rots = []
    planes = []

    rotations.append(Rotation(0, 0))
    x, y, z, a, b = 0, 0, 0, 0, 0
    abs_pos = True  # absolute positioning

    s = src.settings.sett()
    rotationPoint = np.array([s.hardware.rotation_center_x, s.hardware.rotation_center_y, s.hardware.rotation_center_z])

    cone_axis = rotation_matrix([1, 0, 0], 0).dot([0, 0, 1])

    current_layer = 0

    def finishLayer():
        nonlocal path, layer
        if len(path) > 1:
            layer.append(path)

        path = [Point(x, y, z, a, b)]
        if len(layer) > 0:
            layers.append(layer)
            if a != 0:  # TODO: fixme
                rotations.append(Rotation(layer[-1][-1].a, layer[-1][-1].b))
            lays2rots.append(len(rotations) - 1)

        layer = []

    t = 0  # select extruder (t==0) or incline (t==2) or rotate (t==1)
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        if line[0] == ';':  # comment
            if line.startswith(";LAYER:"):
                current_layer = int(line[7:])
                finishLayer()
            elif line.startswith(";Estimated print time:"):
                print_time = float(line[23:])
                s.slicing.print_time = print_time
            elif line.startswith(";Estimated consumption material:"):
                consumption_material = float(line[33:])
                s.slicing.consumption_material = consumption_material
            elif line.startswith(";End"):
                break
        if line == "T0":
            t = 0
        if line == "T1":
            t = 1
        if line == "T2":
            t = 2
        else:
            line = line + ";" if len(line) == 0 or ";" not in line else line
            args, comment = line.split(";")[:2]
            args = args.split(" ")
            if comment.lower() == "rotation":  # we have either rotation or incline
                finishLayer()
                # if any(a.lower().startswith('u') for a in args):  # rotation
                rotations.append(Rotation(rotations[-1].x_rot, parseRotation(args[1:])))
            elif comment.lower() == "incline":
                finishLayer()
                # if any(a.lower().startswith('v') for a in args):  # incline
                rotations.append(Rotation(parseRotation(args[1:]), rotations[-1].z_rot))

                cone_axis = rotation_matrix([1, 0, 0], np.radians(rotations[-1].x_rot)).dot([0, 0, 1])
            elif args[0] == "G0":  # move to (or rotate)
                if len(path) > 1:  # finish path and start new
                    layer.append(path)
                x, y, z, a, b = parseArgs(args[1:], x, y, z, a, b, cone_axis, rotationPoint, abs_pos)
                path = [Point(x, y, z, a, b)]
            elif args[0] == "G1":  # draw to
                x, y, z, a, b = parseArgs(args[1:], x, y, z, a, b, cone_axis, rotationPoint, abs_pos)
                path.append(Point(x, y, z, a, b))
            elif args[0] == "G90":  # absolute positioning
                abs_pos = True
            elif args[0] == "G91":  # relative positioning
                abs_pos = False
            else:
                pass  # skip

    finishLayer()  # not forget about last layer
    src.settings.save_settings()

    layers.append(layer)  # add dummy layer for back rotations
    lays2rots.append(len(rotations) - 1)
    return GCode(layers, rotations, lays2rots)