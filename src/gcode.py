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


class Dummy:
    pass


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


class Position:
    def __init__(self, X=None, Y=None, Z=None, U=None, V=None, E=None):
        self.X = X
        self.Y = Y
        self.Z = Z
        self.U = U
        self.V = V
        self.E = E

    def apply(self, pos):
        for key in "XYZUVE":
            val = getattr(pos, key)
            if val is not None:
                setattr(self, key, val)

    def getCopy(self):
        return Position(self.X, self.Y, self.Z, self.U, self.V, self.E)


class Printer:
    def __init__(self, s):
        self.tmp = 0
        self.currPos = Position(0, 0, 0, 0, 0, 0)
        self.prevPos = Position(0, 0, 0, 0, 0, 0)

        self.rotationPoint = np.array([s.hardware.rotation_center_x, s.hardware.rotation_center_y, s.hardware.rotation_center_z])
        self.cone_axis = rotation_matrix([1, 0, 0], 0).dot([0, 0, 1])
        self.model = Dummy()
        self.model.layers = Dummy()
        self.path = []
        self.pathIsCone = False
        self.layer = []
        self.layers = []
        self.rotations = []
        self.rotations.append(Rotation(0, 0))
        self.lays2rots = []

    def updatePos(self, args):
        if len(self.layers) == 150:
            print(args)
        # update previous position
        self.prevPos.apply(self.currPos)

        # convert text args to values
        res = {}
        for arg in args:
            if len(arg) == 0:
                continue
            key, val = arg[0], arg[1:]
            if key in "XYZUVE":
                res[key] = float(val)
            elif key == ";":
                break

        # apply values to the printer position
        for key, val in res.items():
            setattr(self.currPos, key, val)

        self.dX = self.prevPos.X - self.currPos.X
        self.dY = self.prevPos.Y - self.currPos.Y
        self.dZ = self.prevPos.Z - self.currPos.Z
        self.dU = self.prevPos.U - self.currPos.U
        self.dE = self.prevPos.E - self.currPos.E
        noMove = self.dX == 0 and self.dY == 0 and self.dZ == 0 and self.dU == 0

        if self.dE == 0 or noMove:
            self.finishPath()
        else:
            # if self.rotations[-1].z_rot == 0 and (self.currPos.U != 0 or self.prevPos.U != 0):
            if self.dU != 0 or self.rotations[-1].z_rot != self.currPos.U:
                self.pathIsCone = True

            if len(self.path) == 0:
                self.path.append(self.prevPos.getCopy())
            self.path.append(self.currPos.getCopy())

            p1 = self.path[-2]
            p2 = self.currPos
            # if len(self.rotations) > 1 and self.tmp < 400:
            if len(self.layers) == 150 and self.tmp < 3000:
                print(f"{len(self.layers):2d} {p1.X:7.3f} {p1.Y:7.3f} {p1.Z:7.3f} {p1.U:8.3f} {len(self.path):3d} {p2.X:7.3f} {p2.Y:7.3f} {p2.Z:7.3f} {p2.U:8.3f}")
                self.tmp += 1

    def pathSplit(self):
        maxDeltaU = 5

        lastPos = self.path[0]
        res = [(lastPos.X, lastPos.Y, lastPos.Z, lastPos.U)]
        for pos in self.path[1:]:
            numPoints = int(abs(lastPos.U - pos.U) // maxDeltaU)
            if numPoints > 0:
                rangeU = list(np.linspace(
                    lastPos.U, pos.U, numPoints + 2)[1:])
                rangeX = list(np.linspace(
                    lastPos.X, pos.X, numPoints + 2)[1:])
                rangeY = list(np.linspace(
                    lastPos.Y, pos.Y, numPoints + 2)[1:])
                rangeZ = list(np.linspace(
                    lastPos.Z, pos.Z, numPoints + 2)[1:])

                for dU, dX, dY, dZ in zip(rangeU, rangeX, rangeY, rangeZ):
                    res.append((dX, dY, dZ, dU))
            else:
                res.append(
                    (pos.X, pos.Y, pos.Z, pos.U))
            lastPos = pos

        return res

    def getPoints(self):
        maxDeltaU = 5
        numPoints = int(abs(self.dU) // maxDeltaU)

        res = []
        if numPoints > 0:
            rangeU = list(np.linspace(
                self.prevPos.U, self.currPos.U, numPoints + 2)[1:])
            rangeX = list(np.linspace(
                self.prevPos.X, self.currPos.X, numPoints + 2)[1:])
            rangeY = list(np.linspace(
                self.prevPos.Y, self.currPos.Y, numPoints + 2)[1:])
            rangeZ = list(np.linspace(
                self.prevPos.Z, self.currPos.Z, numPoints + 2)[1:])

            for dU, dX, dY, dZ in zip(rangeU, rangeX, rangeY, rangeZ):
                res.append(
                    (
                        f"X{dX}",
                        f"Y{dY}",
                        f"Z{dZ}",
                        f"U{dU}",
                    )
                )
        else:
            res.append(
                (
                    f"X{self.currPos.X}",
                    f"Y{self.currPos.Y}",
                    f"Z{self.currPos.Z}",
                    f"U{self.currPos.U}",
                )
            )
        return res

    def finishPath(self):
        if len(self.path) < 2:
            return

        # finish path and start new
        points = []
        if self.pathIsCone:
            rotationPoint = self.rotationPoint
            cone_axis = self.cone_axis

            for xr, yr, zr, ur in self.pathSplit():
                # convert from cylindrical coordinates to xyz
                u = math.radians(ur)
                r = yr
                z = zr

                xr, yr, zr = rotation_matrix(cone_axis, -u).dot(np.array([xr, r, z]) - rotationPoint) + rotationPoint

                points.append(Point(xr, yr, zr, 0, 0))
        else:
            for pos in self.path:
                points.append(Point(pos.X, pos.Y, pos.Z, 0, 0))

        self.layer.append(points)
        self.path = []
        self.pathIsCone = False

    def finishLayer(self):
        self.finishPath()
        if len(self.layer) > 0:
            self.layers.append(self.layer)
            self.lays2rots.append(len(self.rotations) - 1)

        self.layer = []


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
    with open(filename, 'r', encoding="utf-8") as f:
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
    printer = Printer(src.settings.sett())
    tmp_idx = 0
    tmp = 0
    for line in lines:
        #print(line)
        if tmp_idx % 10000 == 0:
            print(tmp_idx)
        tmp_idx += 1
        line = line.strip()
        if len(line) == 0:
            continue
        if line[0] == ';':  # comment
            if line.startswith(";LAYER:"):
                current_layer = int(line[7:])
                printer.finishLayer()
            elif line.startswith(";Estimated print time:"):
                print_time = float(line[23:])
                s.slicing.print_time = print_time
            elif line.startswith(";Estimated consumption material:"):
                consumption_material = float(line[33:])
                s.slicing.consumption_material = consumption_material
            elif line.startswith(";Planes contact with nozzle:"):
                planes_contact_with_nozzle = line[29:]
                s.slicing.planes_contact_with_nozzle = planes_contact_with_nozzle
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
                printer.finishLayer()
                # if any(a.lower().startswith('u') for a in args):  # rotation
                printer.rotations.append(Rotation(printer.rotations[-1].x_rot, parseRotation(args[1:])))
                printer.currPos.U = printer.rotations[-1].z_rot
            elif comment.lower() == "incline":
                printer.finishLayer()
                # if any(a.lower().startswith('v') for a in args):  # incline
                printer.rotations.append(Rotation(parseRotation(args[1:]), printer.rotations[-1].z_rot))

                printer.cone_axis = rotation_matrix([1, 0, 0], np.radians(printer.rotations[-1].x_rot)).dot([0, 0, 1])
                printer.currPos.V = printer.rotations[-1].x_rot
            elif args[0] == "G0":  # move to (or rotate)
                pos = args[1:]

                printer.updatePos(pos)
            elif args[0] == "G1":  # draw to
                pos = args[1:]

                printer.updatePos(pos)
            elif args[0] == "G90":  # absolute positioning
                abs_pos = True
            elif args[0] == "G91":  # relative positioning
                abs_pos = False
            else:
                pass  # skip

    printer.finishLayer()  # not forget about last layer
    src.settings.save_settings()

    printer.layers.append(layer)  # add dummy layer for back rotations
    printer.lays2rots.append(len(printer.rotations) - 1)
    return GCode(printer.layers, printer.rotations, printer.lays2rots)
