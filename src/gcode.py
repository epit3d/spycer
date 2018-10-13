class Rotation:
    def __init__(self, x, z):
        self.x_rot = x
        self.z_rot = z

    def __str__(self):
        return " x:" + str(self.x_rot) + " z:" + str(self.z_rot)


def parseArgs(args, x, y, z, absolute=True):
    xr, yr, zr = 0, 0, 0
    if absolute:
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
    if absolute:
        return xr, yr, zr
    return xr + x, yr + y, zr + z


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
    abs_pos = True  # absolute positioning

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
        if line[0] == ';':  # comment
            if line.startswith(";LAYER:"):
                finishLayer()
            elif line.startswith(";End"):
                break
        else:
            args = line.split(" ")
            if args[0] == "G0": # move to
                if len(path) > 1:  # finish path and start new
                    layer.append(path)
                x, y, z = parseArgs(args[1:], x, y, z, abs_pos)
                path = [[x, y, z]]
            elif args[0] == "G1": # draw to
                x, y, z = parseArgs(args[1:], x, y, z, abs_pos)
                path.append([x, y, z])
            elif args[0] == "G62": # rotate plate
                finishLayer()  # rotation could not be inside the layer
                rotations.append(parseRotation(args[1:]))
            elif args[0] == "G90": # absolute positioining
                abs_pos = True
            elif args[0] == "G91": # relative positioining
                abs_pos = False
            else:
                pass  # skip

    finishLayer()  # not forget about last layer

    return layers, rotations, lays2rots
