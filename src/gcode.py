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
        self.currPos = Position(0, 0, 0, 0, 0, 0)
        self.prevPos = Position(0, 0, 0, 0, 0, 0)

        self.rotationPoint = np.array([s.hardware.rotation_center_x, s.hardware.rotation_center_y, s.hardware.rotation_center_z])
        self.cone_axis = rotation_matrix([1, 0, 0], 0).dot([0, 0, 1])

        self.path = []
        self.layer = []
        self.layers = []
        self.rotations = []
        self.rotations.append(Rotation(0, 0))
        self.lays2rots = []
        self.abs_pos = True  # absolute positioning

    def parseArgs(self, args):
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

        return res

    def setAbsPos(self, args):
        res = self.parseArgs(args)

        for key, val in res.items():
            setattr(self.currPos, key, val)

    def setRelPos(self, args):
        res = self.parseArgs(args)

        for key, val in res.items():
            val += getattr(self.currPos, key)
            setattr(self.currPos, key, val)

    def updatePos(self, args):
        # update previous position
        self.prevPos.apply(self.currPos)

        # apply values to the printer position
        if self.abs_pos:
            self.setAbsPos(args)
        else:
            self.setRelPos(args)

        self.dX = self.prevPos.X - self.currPos.X
        self.dY = self.prevPos.Y - self.currPos.Y
        self.dZ = self.prevPos.Z - self.currPos.Z
        self.dU = self.prevPos.U - self.currPos.U
        self.dE = self.prevPos.E - self.currPos.E
        noMove = self.dX == 0 and self.dY == 0 and self.dZ == 0 and self.dU == 0

        if self.dE == 0 or noMove:
            self.finishPath()
        else:
            if len(self.path) == 0:
                self.path.append(self.prevPos.getCopy())
            self.path.append(self.currPos.getCopy())

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

    def finishPath(self):
        # finish path and start new
        if len(self.path) < 2:
            return

        # U coordinate of cone path differs from current bed plane Z rotation
        pathIsCone = False
        for pos in self.path:
            if pos.U != self.rotations[-1].z_rot:
                pathIsCone = True
                break

        points = []
        if pathIsCone:
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
    layer = []
    planes = []

    s = src.settings.sett()

    current_layer = 0

    t = 0  # select extruder (t==0) or incline (t==2) or rotate (t==1)
    printer = Printer(src.settings.sett())

    for line in lines:
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
                printer.abs_pos = True
            elif args[0] == "G91":  # relative positioning
                printer.abs_pos = False
            elif args[0] == "G92":  # set position
                printer.setAbsPos(args[1:])
                printer.finishPath()
            else:
                pass  # skip

    printer.finishLayer()  # not forget about last layer
    src.settings.save_settings()

    printer.layers.append(layer)  # add dummy layer for back rotations
    printer.lays2rots.append(len(printer.rotations) - 1)
    return GCode(printer.layers, printer.rotations, printer.lays2rots)
