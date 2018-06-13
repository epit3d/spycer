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
    return Rotation(-x, -z)


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

    return layers, rotations, lays2rots
