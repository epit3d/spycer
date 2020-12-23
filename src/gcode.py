class GCode:
    def __init__(self, layers, rotations, lays2rots):
        self.layers = layers
        self.rotations = rotations
        self.lays2rots = lays2rots


class Rotation:
    def __init__(self, x, z):
        self.x_rot = x
        self.z_rot = z

    def __str__(self):
        return " x:" + str(self.x_rot) + " z:" + str(self.z_rot)


def parseArgs(args, x, y, z, absolute=True):
    xr, yr, zr = 0, 0, 0
    z_rot = None
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
        # elif arg[0] == "A":
        #     z_rot = -float(arg[1:])
        elif arg[0] == ";":
            break
    if absolute:
        return xr, yr, zr, z_rot
    return xr + x, yr + y, zr + z, z_rot


def parseRotation(args):
    e = 0
    for arg in args:
        if len(arg) == 0:
            continue
        if arg[0] == "E":
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

    t = 0  # select extruder (t==0) or incline (t==2) or rotate (t==1)
    for line in lines:
        line = line.strip()
        if len(line) == 0:
            continue
        if line[0] == ';':  # comment
            if line.startswith(";LAYER:"):
                finishLayer()
            elif line.startswith(";End"):
                break
        if line == "T0":
            t = 0
        if line == "T1":
            t = 1
        if line == "T2":
            t = 2
        else:
            args = line.split(" ")
            if args[0] == "G0":  # move to (or rotate)
                if len(path) > 1:  # finish path and start new
                    layer.append(path)
                x, y, z, z_rot = parseArgs(args[1:], x, y, z, abs_pos)
                path = [[x, y, z]]
                if z_rot is not None:
                    finishLayer()
                    rotations.append(Rotation(rotations[-1].x_rot, z_rot))
            elif args[0] == "G1":  # draw to
                if t == 0:
                    x, y, z, _ = parseArgs(args[1:], x, y, z, abs_pos)
                    path.append([x, y, z])
                elif t == 1:  # rotate
                    finishLayer()  # rotation could not be inside the layer
                    rotations.append(Rotation(rotations[-1].x_rot, -parseRotation(args[1:])))
                else:  # inclines
                    finishLayer()  # rotation could not be inside the layer
                    rotations.append(Rotation(parseRotation(args[1:]), rotations[-1].z_rot))
            # elif args[0] == "G62":  # rotate plate
            #     finishLayer()  # rotation could not be inside the layer
            #     rotations.append(parseRotation(args[1:]))
            # elif args[0] == "M43":  # incline X
            #     finishLayer()  # rotation could not be inside the layer
            #     rotations.append(Rotation(InclineXValue, rotations[-1].z_rot))
            # elif args[0] == "M42":  # incline X BACK
            #     finishLayer()  # rotation could not be inside the layer
            #     rotations.append(Rotation(0, rotations[-1].z_rot))
            elif args[0] == "G90":  # absolute positioning
                abs_pos = True
            elif args[0] == "G91":  # relative positioning
                abs_pos = False
            else:
                pass  # skip

    finishLayer()  # not forget about last layer

    layers.append(layer)  # add dummy layer for back rotations
    lays2rots.append(len(rotations) - 1)
    return GCode(layers, rotations, lays2rots)
