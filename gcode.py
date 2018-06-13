import vtk

import params


class GCode:
    def __init__(self, layers, rotations, lays2rots):
        self.layers = layers
        self.rotations = rotations
        self.lays2rots = lays2rots

    def __str__(self):
        return "gcode, layers: " + str(len(self.layers)) + " rotations: " + str(len(self.rotations)) + "-1"


class Rotation:
    def __init__(self, x, z):
        self.x_rot = x
        self.z_rot = z

    def __str__(self):
        return " x:" + str(self.x_rot) + " z:" + str(self.z_rot)


def parseArgs(args, x, y, z):
    xr, yr, zr = x, y, z
    for arg in args:
        if len(arg) == 0:
            continue
        if arg[0] == "X":
            xr = float(arg[1:])
        elif arg[0] == "Y":
            yr = float(arg[1:])
        elif arg[0] == "Z":
            zr = float(arg[1:])
        elif arg[0] == ";":
            break
    return xr, yr, zr


def parseRotation(args):
    x, _, z = parseArgs(args, 0, 0, 0)
    return Rotation(x, z)


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

    rotations.append(Rotation(0, 0))
    x, y, z = 0, 0, 0

    def finishLayer():
        nonlocal path, layer
        if len(path) > 1:
            layer.append(path)
        path = [[x, y, z]]
        if len(layer) > 0:
            layers.append(layer)
            lays2rots.append(len(rotations) - 1)
        layer = []

    for line in lines:
        if len(line) == 0:
            continue
        if line[0] == ';':
            if line.startswith(";LAYER:"):
                finishLayer()
        else:
            args = line.split(" ")
            if args[0] == "G0":
                if len(path) > 1:  # finish path and start new
                    layer.append(path)
                x, y, z = parseArgs(args[1:], x, y, z)
                path = [[x, y, z]]
            elif args[0] == "G1":
                x, y, z = parseArgs(args[1:], x, y, z)
                path.append([x, y, z])
            elif args[0] == "G62":
                finishLayer()  # rotation could not be inside the layer
                rotations.append(parseRotation(args[1:]))

    finishLayer()  # not forget about last layer

    return GCode(layers, rotations, lays2rots)


def vtkBlocks(layers):
    blocks = []
    for layer in layers:
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        block = vtk.vtkPolyData()
        points_count = 0
        for path in layer:
            line = vtk.vtkLine()
            for k in range(len(path) - 1):
                points.InsertNextPoint(path[k])
                line.GetPointIds().SetId(0, points_count + k)
                line.GetPointIds().SetId(1, points_count + k + 1)
                lines.InsertNextCell(line)
            points.InsertNextPoint(path[-1])  # not forget to add last point
            points_count += len(path)
        block.SetPoints(points)
        block.SetLines(lines)
        blocks.append(block)
    return blocks

def wrapWithActors(g):
    blocks = vtkBlocks(g.layers)
    actors = []
    for i in range(len(blocks)):
        block = blocks[i]

        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(block)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        transform = vtk.vtkTransform()
        # rotate to abs coords firstly and then apply last rotation
        transform.PostMultiply()
        transform.RotateZ(g.rotations[g.lays2rots[i]].z_rot)
        transform.PostMultiply()
        transform.RotateX(g.rotations[g.lays2rots[i]].x_rot)

        transform.PostMultiply()
        transform.RotateX(-g.rotations[-1].x_rot)
        transform.PostMultiply()
        transform.RotateZ(-g.rotations[-1].z_rot)
        actor.SetUserTransform(transform)

        actor.GetProperty().SetColor(params.LayerColor)
        actors.append(actor)

    actors[-1].GetProperty().SetColor(params.LastLayerColor)
    return actors