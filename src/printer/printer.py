from math import sin, cos, radians
from .utils import polar2cart, tiltPoint
from .http import getPos, getHomed, getObjectModel, execGcode
import time

from .delta import DeltaParams
from .scale import ScaleParams
from .skew import SkewParams


writeGcode = False
useDwell = True
# writeGcode = True
# useDwell = False


def callGcode(gcode):
    print(f'G-code: {gcode}')

    if writeGcode:
        global fileGcode
        fileGcode.write(f'{gcode}\n')
        if useDwell:
            fileGcode.write('G4 P100\n')
        return ''

    return execGcode(gcode)


axisX = 0
axisY = 1
axisZ = 2
axisU = 3
axisV = 4


class Point:
    X = None
    Y = None
    Z = None
    U = None
    V = None
    F = 2000


# def moveTo(X=None, Y=None, Z=None, U=None, V=None, F=2000):
def moveTo(*args, **kwargs):
    point = Point()
    for key, arg in zip('XYZ', args):
        setattr(point, key, arg)

    for key, arg in kwargs.items():
        setattr(point, key, arg)

    parameters = ''
    if point.X is not None:
        parameters += f' X{point.X:.3f}'
    if point.Y is not None:
        parameters += f' Y{point.Y:.3f}'
    if point.Z is not None:
        parameters += f' Z{point.Z:.3f}'
    if point.U is not None:
        parameters += f' U{point.U:.3f}'
    if point.V is not None:
        parameters += f' V{point.V:.3f}'
    gcodes = [
        'G90',  # absolute positioning
        'G0' + parameters + f' F{point.F:d}',
    ]
    for gcode in gcodes:
        result = callGcode(gcode).strip()
        if result.split(' ')[0] == 'Error:':
            raise Exception(result)


def moveRelTo(X=None, Y=None, Z=None, F=2000):
    parameters = ''
    if X is not None:
        parameters += f' X{X:.3f}'
    if Y is not None:
        parameters += f' Y{Y:.3f}'
    if Z is not None:
        parameters += f' Z{Z:.3f}'
    gcodes = [
        'G91',  # relative positioning
        'G0' + parameters + f' F{F:d}',
        'G90',  # absolute positioning
    ]
    for gcode in gcodes:
        result = callGcode(gcode).strip()
        if result.split(' ')[0] == 'Error:':
            raise Exception(result)


def doHoming():
    homed = True
    for axis in (axisX, axisY, axisZ):
        homed = homed and getHomed(axis)

    if not homed:
        callGcode('G28 Z')
    else:
        moveTo(Z=200)
        moveTo(X=0, Y=0)

    homedU = getHomed(axisU) and getPos(axisU) < 360
    if not homedU:
        callGcode('G28 U')
    else:
        rotateBed(U=0)

    homedV = getHomed(axisV)
    if not homedV:
        callGcode('G28 V')
    else:
        tiltBed(V=0)


def rotateBed(U):
    gcodes = [
        f'G0 U{U:d} F1000',
    ]
    for gcode in gcodes:
        callGcode(gcode)


def tiltBed(V, F=1000):
    gcodes = [
        f'G0 V{V:d} F{F:d}',
    ]
    for gcode in gcodes:
        callGcode(gcode)


def probeZ():
    probeNum = 4
    results = []
    gcodes = [
        'G91',  # relative positioning
        'G0 Z2 F100',
        'G90',  # absolute positioning
    ]

    for _ in range(probeNum):
        reply = callGcode('G30 S-1').strip()

        if len(reply) > 0 and reply[:4] == 'Error':
            raise Exception(reply)

        # needed here to let printer update Z position
        time.sleep(0.5)

        results.append(getPos(axisZ))

        for gcode in gcodes:
            callGcode(gcode)

    return sum(results[1:]) / len(results[1:]), results


def requestX():
    return getPos(axisX)


def requestY():
    return getPos(axisY)


def probePosX():
    probeNum = 4
    results = []
    gcodes = [
        'G91',  # relative positioning
        'G0 X-2 F100',
        'G90',  # absolute positioning
    ]

    for _ in range(probeNum):
        callGcode('G38.2 X40')

        results.append(requestX())

        for gcode in gcodes:
            callGcode(gcode)

    return sum(results[1:]) / len(results[1:]), results


def probeNegX():
    probeNum = 4
    results = []
    gcodes = [
        'G91',  # relative positioning
        'G0 X2 F100',
        'G90',  # absolute positioning
    ]

    for _ in range(probeNum):
        callGcode('G38.2 X0')

        results.append(requestX())

        for gcode in gcodes:
            callGcode(gcode)

    return sum(results[1:]) / len(results[1:]), results


def probePosY():
    probeNum = 4
    results = []
    gcodes = [
        'G91',  # relative positioning
        'G0 Y-2 F100',
        'G90',  # absolute positioning
    ]

    for _ in range(probeNum):
        callGcode('G38.2 Y40')

        results.append(requestY())

        for gcode in gcodes:
            callGcode(gcode)

    return sum(results[1:]) / len(results[1:]), results


def probeNegY():
    probeNum = 4
    results = []
    gcodes = [
        'G91',  # relative positioning
        'G0 Y2 F100',
        'G90',  # absolute positioning
    ]

    for _ in range(probeNum):
        callGcode('G38.2 Y0')

        results.append(requestY())

        for gcode in gcodes:
            callGcode(gcode)

    return sum(results[1:]) / len(results[1:]), results


class EpitPrinter:
    def __init__(self):
        self.deltaParams = DeltaParams()
        self.scaleParams = ScaleParams()
        self.skewParams = SkewParams()

    def zProbe(self):
        zA, probes = probeZ()
        self._appendOutput(f'Z:{zA:6.3f} mm' + ' ' + str(probes))

    def __del__(self):
        print('printer deleted')

    def setOutputMethod(self, method):
        self._appendOutput = method

    def setStatusMethod(self, method):
        self._status = method

    def closeGcodeFile(self):
        if writeGcode:
            global fileGcode
            fileGcode.close()

    def openGcodeFile(self):
        if writeGcode:
            global fileGcode
            fileGcode = open('output.g', 'w')

    def defAxisU(self, posZ):
        doHoming()

        points1 = (
            (0, 90),
            (-78, -45),
            (78, -45),
        )

        points2 = (
            (0, -90),
            (78, 45),
            (-78, 45),
        )

        for num, point in enumerate(points1):
            X, Y = point
            moveTo(X, Y, posZ)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, posZ)

            self._appendOutput(f'{num:d}: Z:{zA:6.3f} mm' + ' ' + str(probes))

        rotateBed(U=-180)

        for num, point in enumerate(points2):
            X, Y = point
            moveTo(X, Y, posZ)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, posZ)

            self._appendOutput(f'{num:d}: Z:{zA:6.3f} mm' + ' ' + str(probes))

        doHoming()

    def defAxisV(self, posZ, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        """points1 = (
            (-50, -85, 10),
            (-50, 85, 10),
            (50, -85, 10),
            (50, 85, 10),
        )

        points2 = (
            (-50, 5, 5),
            (-50, 70, 35),
            (50, 5, 5),
            (50, 70, 35),
        )

        points3 = (
            (-50, 35, 10),
            (-50, 70, 50),
            (50, 35, 10),
            (50, 70, 50),
        )"""

        """points1 = (
            (-35, -80, 10), # noqa
            (-35,  12, 10), # noqa
            ( 35, -80, 10), # noqa
            ( 35,  12, 10), # noqa
        )

        points2 = (
            (-35, -57, -24), # noqa
            (-35,  42,  20), # noqa
            ( 35, -57, -24), # noqa
            ( 35,  42,  20), # noqa
        )

        points3 = (
            (-35, -5, -35), # noqa
            (-35, 65,  50), # noqa
            ( 35, -5, -35), # noqa
            ( 35, 65,  50), # noqa
        )"""

        radius = 60

        points1 = (
            polar2cart(-135, radius),  # noqa
            polar2cart( 135, radius),  # noqa
            polar2cart( -45, radius),  # noqa
            polar2cart(  45, radius),  # noqa
        )

        basePoints = []
        rotVector = (0, 0, 63.5)
        ballRadius = 4.965

        moveTo(Z=100)
        tiltBed(V=0)

        self._appendOutput('Area 1')
        for num, point in enumerate(points1):
            X, Y = point
            moveTo(X, Y, posZ)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, posZ)

            basePoints.append((X, Y, zA))

            self._appendOutput(f'{num:d}: X:{X:6.3f} Y:{Y:6.3f} Z:{zA:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=100)
        posV = 25
        tiltBed(V=posV)

        points2 = [tiltPoint(point, posV, rotVector) for point in basePoints]

        self._appendOutput('Area 2')
        for num, point in enumerate(points2):
            X, Y, Z = point
            # incremnet Z position to approach higher
            Z += 5
            # increment Z position more since the ball touches inclined plane earlier
            Z += -ballRadius + ballRadius / cos(radians(posV))

            moveTo(X, Y, Z)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, Z)

            self._appendOutput(f'{num:d}: X:{X:6.3f} Y:{Y:6.3f} Z:{zA:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=100)
        posV = 50
        tiltBed(V=posV)

        points3 = [tiltPoint(point, posV, rotVector) for point in basePoints]

        self._appendOutput('Area 3')
        for num, point in enumerate(points3):
            X, Y, Z = point
            # incremnet Z position to approach higher
            Z += 5
            # increment Z position more since the ball touches inclined plane earlier
            Z += -ballRadius + ballRadius / cos(radians(posV))
            moveTo(X, Y, Z)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, Z)

            self._appendOutput(f'{num:d}: X:{X:6.3f} Y:{Y:6.3f} Z:{zA:6.3f} mm' + ' ' + str(probes))

        doHoming()

    def probeLine(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        """points = (
            (-35, 65,  50), # noqa
            (-25, 65,  50), # noqa
            (-15, 65,  50), # noqa
            (  0, 65,  50), # noqa
            ( 15, 65,  50), # noqa
            ( 25, 65,  50), # noqa
            ( 35, 65,  50), # noqa
        )"""

        points = (
            (-35, 12,  5), # noqa
            (-25, 12,  5), # noqa
            (-15, 12,  5), # noqa
            (  0, 12,  5), # noqa
            ( 15, 12,  5), # noqa
            ( 25, 12,  5), # noqa
            ( 35, 12,  5), # noqa
        )

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)

        self._appendOutput('Area 1')
        for num, point in enumerate(points):
            X, Y, Z = point
            moveTo(X, Y, Z, F=500)

            zA, probes = probeZ()
            print(zA)

            moveTo(X, Y, Z, F=50)

            self._appendOutput(f'{num:d}: Z:{zA:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)

    def defDelta(self, posZ, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        points = (
            (  0,  100), # noqa
            ( 87,   50), # noqa
            ( 87,  -50), # noqa
            (  0, -100), # noqa
            (-87,  -50), # noqa
            (-87,   50), # noqa
            (  0,   15), # noqa
            ( 13, -7.5), # noqa
            (-13, -7.5), # noqa
        )

        result = []

        for num, point in enumerate(points):
            X, Y = point
            moveTo(X, Y, posZ)

            zA, probes = probeZ()
            # we multiply to -1 in order to get the correct values
            # for Web Escher Calculator
            zA = zA * -1
            self._appendOutput(f'Z{num:d}: {zA:6.3f} mm' + ' ' + str(probes))
            print(zA)
            result += [(X, Y, zA)]

            moveTo(X, Y, posZ)

        doHoming()
        return result

    def startCalibration(self, *args, **kwargs):
        print(args, kwargs)

        self._status('Starting calibration')
        self._appendOutput(callGcode('M665'))

        doHoming()
        moveTo(X=0, Y=80, Z=50)
        moveTo(X=0, Y=80, Z=25)

        z1, probes = probeZ()
        self._appendOutput(f'Z1: {z1:.3f} mm' + ' ' + str(probes))
        print(z1)

        moveTo(X=0, Y=80, Z=25)
        moveTo(X=0, Y=80, Z=50)
        moveTo(X=0, Y=-80, Z=50)

        rotateBed(U=-180)
        moveTo(X=0, Y=-80, Z=25)

        z2, probes = probeZ()
        self._appendOutput(f'Z2: {z2:.3f} mm' + ' ' + str(probes))
        dz = abs(z1-z2)
        self._appendOutput(f'dZ: {dz:.3f} mm')
        print(z2)

        moveTo(X=0, Y=-80, Z=25)
        moveTo(X=0, Y=-80, Z=50)

        moveTo(X=0, Y=0, Z=200)
        rotateBed(U=10)

    def defOrigin(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(X=-20, Y=0)
        moveTo(Z=24)

        aX, probes = probePosX()
        print(aX)
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=-20)
        moveTo(Y=20)
        moveTo(X=0)

        aY, probes = probeNegY()
        print(aY)
        self._appendOutput(f'0: Y:{aY:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=20)
        moveTo(Z=100)

        rotateBed(U=-180)

        moveTo(X=20, Y=0)
        moveTo(Z=24)

        aX, probes = probeNegX()
        print(aX)
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=20)
        moveTo(Y=-20)
        moveTo(X=0)

        aY, probes = probePosY()
        print(aY)
        self._appendOutput(f'0: Y:{aY:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=-20)

        doHoming()

    def testCalibration(self, *args, **kwargs):
        print(args, kwargs)

        result = getObjectModel('move.axes')
        self._appendOutput(str(result))
        return

        result = callGcode('M114')

        self._appendOutput(str(result))
        return

        gcodes = [
            'G91',  # relative positioning
            'G0 Z5 F100',
            'G90',  # absolute positioning
        ]

        doHoming()
        callGcode('G0 Z150 F1000')
        for _ in range(10):
            for gcode in gcodes:
                callGcode(gcode)
        callGcode('G0 Z150 F1000')

    def callM112(self, *args, **kwargs):
        print(args, kwargs)

        result = callGcode('M112')
        self._appendOutput(str(result))

    def callProbePosX(self, *args, **kwargs):
        print(args, kwargs)

        aX, probes = probePosX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

    def callProbeNegX(self, *args, **kwargs):
        print(args, kwargs)

        aX, probes = probeNegX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

    def callHome(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()
        self._appendOutput('Homing done')

    def adjustPlateY(self, posY, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(X=25, Y=posY, Z=100)
        moveTo(X=25, Y=posY, Z=5)

        aX, probes = probeNegX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=25, Y=posY, Z=5)

        moveTo(X=25, Y=-posY, Z=5)

        aX, probes = probeNegX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=25, Y=-posY, Z=5)
        moveTo(X=25, Y=-posY, Z=100)

    def measurePlateY(self, posY, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(X=45, Y=posY, Z=100)
        moveTo(X=45, Y=posY, Z=9)

        aX, probes = probeNegX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=45, Y=posY, Z=9)

        moveTo(X=45, Y=-posY, Z=9)

        aX, probes = probeNegX()
        self._appendOutput(f'0: X:{aX:6.3f} mm' + ' ' + str(probes))

        moveTo(X=45, Y=-posY, Z=9)
        moveTo(X=45, Y=-posY, Z=100)

    def adjustPlateX(self, posX, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(X=posX, Y=-25, Z=100)
        moveTo(X=posX, Y=-25, Z=5)

        A, probes = probePosY()
        self._appendOutput(f'0: X:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=posX, Y=-25, Z=5)

        moveTo(X=-posX, Y=-25, Z=5)

        A, probes = probePosY()
        self._appendOutput(f'1: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=-posX, Y=-25, Z=5)
        moveTo(X=-posX, Y=-25, Z=100)

    def measurePlateX(self, posX, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(X=posX, Y=-45, Z=100)
        moveTo(X=posX, Y=-45, Z=9)

        A, probes = probePosY()
        self._appendOutput(f'0: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=posX, Y=-45, Z=9)

        moveTo(X=-posX, Y=-45, Z=9)

        A, probes = probePosY()
        self._appendOutput(f'1: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=-posX, Y=-45, Z=9)
        moveTo(X=-posX, Y=-45, Z=100)

    def incPosX(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(X=8, F=1000)

    def incNegX(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(X=-8, F=1000)

    def incPosY(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(Y=8, F=1000)

    def incNegY(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(Y=-8, F=1000)

    def incPosZ(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(Z=8, F=1000)

    def incNegZ(self, *args, **kwargs):
        print(args, kwargs)

        moveRelTo(Z=-8, F=1000)

    def runGcode(self, gcode, *args, **kwargs):
        print(args, kwargs)

        self._appendOutput(f'Gcode: {gcode}')
        result = callGcode(gcode)
        self._appendOutput(f'Reply: {result}')
        self._status(' '.join(callGcode('M114').split(' ')[:5]))

    def measureXDeviationFromV(self, *args, **kwargs):
        print(args, kwargs)

        points = (
            ( 0, (-17,      0,     15)), # noqa
            (10, (-17,  8.002, 15.429)), # noqa
            (20, (-17, 15.808, 17.241)), # noqa
            (30, (-17,  23.18, 20.381)), # noqa
            (40, (-17, 29.895, 24.754)), # noqa
            (50, (-17, 35.749, 30.226)), # noqa
        )

        doHoming()

        moveTo(X=-17, Y=0, Z=100)
        tiltBed(V=0)
        moveTo(Z=20)

        for V, point in points:
            X, Y, Z = point
            moveTo(X, Y, Z, F=50)
            tiltBed(V, F=50)

            A, probes = probePosX()
            self._appendOutput(f'V={V:2d}: X:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=0, Y=0, Z=100)
        tiltBed(V=0)

    def measureZDeviationFromV(self, *args, **kwargs):
        print(args, kwargs)

        ballDiameter = 9.93
        ballRadius = ballDiameter / 2

        points = (
            ( 0, (      0,      0, 32.081 + 4 + ballRadius * (1 - 1 / cos(radians( 0)) ) )), # noqa
            (10, (-0.0341,  8.063, 32.896 + 4 + ballRadius * (1 - 1 / cos(radians(10)) ) )), # noqa
            (20, (      0, 15.863, 35.097 + 4 + ballRadius * (1 - 1 / cos(radians(20)) ) )), # noqa
            (30, (  0.102, 23.163, 38.617 + 4 + ballRadius * (1 - 1 / cos(radians(30)) ) )), # noqa
            (40, (  0.267, 29.740, 43.349 + 4 + ballRadius * (1 - 1 / cos(radians(40)) ) )), # noqa
            (50, (  0.492, 35.395, 49.151 + 4 + ballRadius * (1 - 1 / cos(radians(50)) ) )), # noqa
        )

        doHoming()

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)
        moveTo(Z=40, F=500)

        for V, point in points:
            X, Y, Z = point
            moveTo(X, Y, Z, F=50)
            tiltBed(V, F=50)

            A, probes = probeZ()
            corrA = A + ballRadius * (1 - 1 / cos(radians(V)) ) # noqa
            text = f'V={V:2d}: Z:{A:6.3f} mm {probes} {corrA:6.3f}'
            self._appendOutput(text)

            moveTo(X, Y, Z, F=50)

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)

    def measureVDeviationFromV(self, *args, **kwargs):
        print(args, kwargs)

        points = (
            ( 0, (0, 50,  8), (0, -50, 8)), # noqa
            (10, (0, 64, 19), (0, -15, 6)), # noqa
            (20, (0, 73, 31), (0,   2, 6)), # noqa
            (30, (0, 80, 46), (0,  13, 6)), # noqa
            (40, (0, 85, 62), (0,  22, 6)), # noqa
            (50, (0, 88, 85), (0,  27, 2)), # noqa
        )

        doHoming()

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)
        moveTo(Z=40, F=500)

        for V, point1, point2 in points:
            X, Y, Z = point1
            moveTo(X, Y, Z, F=1000)

            tiltBed(V, F=50)

            A, probes = probeZ()
            self._appendOutput(f'V={V:2d} 1: Z:{A:6.3f} mm {probes}')

            moveTo(X, Y, Z, F=50)

            X, Y, Z = point2
            moveTo(X, Y, Z, F=1000)

            A, probes = probeZ()
            self._appendOutput(f'V={V:2d} 2: Z:{A:6.3f} mm {probes}')

            moveTo(X, Y, Z, F=50)

        moveTo(Z=100, F=1000)
        moveTo(X=0, Y=0)
        tiltBed(V=0)

    def measureOrthogonalityXY(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(Z=100, F=1000)

        moveTo(X=-50, Y=-30)
        moveTo(Z=12, F=500)

        A, probes = probePosY()
        self._appendOutput(f'X=-50: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=-30, F=50)
        moveTo(X=20, F=500)

        A, probes = probePosY()
        self._appendOutput(f'X= 20: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=-30, F=50)

        moveTo(X=40, F=500)
        moveTo(Y=-15, F=500)
        moveTo(Z=8, F=50)

        A, probes = probeNegX()
        self._appendOutput(f'Y=-15: X:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=40, F=50)
        moveTo(Y=55, F=500)

        A, probes = probeNegX()
        self._appendOutput(f'Y= 55: X:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=40, F=50)
        moveTo(Z=100, F=500)

        moveTo(X=0, Y=0)

    def measureOrthoYZ(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(Z=100, F=1000)

        moveTo(X=0, Y=-50)
        moveTo(Z=10, F=500)

        A, probes = probeZ()
        self._appendOutput(f'Y=-35: Z:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=10, F=100)
        moveTo(Y=20, F=500)

        A, probes = probeZ()
        self._appendOutput(f'Y= 35: Z:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=10, F=100)

        A, probes = probePosY()
        self._appendOutput(f'Z= 10: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=20, F=50)
        moveTo(Z=80, F=500)

        A, probes = probePosY()
        self._appendOutput(f'Z= 80: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Y=20, F=50)
        moveTo(Z=100, F=500)

        moveTo(X=0, Y=0, F=500)

    def measureOrthoXZ(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        moveTo(Z=100, F=1000)

        moveTo(X=-50, Y=0)
        moveTo(Z=10, F=500)

        A, probes = probeZ()
        self._appendOutput(f'Y=-35: Z:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=10, F=100)
        moveTo(X=20, F=500)

        A, probes = probeZ()
        self._appendOutput(f'Y= 35: Z:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(Z=10, F=100)

        A, probes = probePosX()
        self._appendOutput(f'Z= 10: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=20, F=50)
        moveTo(Z=80, F=500)

        A, probes = probePosX()
        self._appendOutput(f'Z= 80: Y:{A:6.3f} mm' + ' ' + str(probes))

        moveTo(X=20, F=50)
        moveTo(Z=100, F=500)

        moveTo(X=0, Y=0, F=500)

    def doHeat(self, *args, **kwargs):
        print('heat', args, kwargs)

        doHoming()

        moveTo(Z=200, F=1000)

        points = (
            (-35, -35, 200), # noqa
            (-35,  35, 200), # noqa
            ( 35,  35, 200), # noqa
            ( 35, -35, 200), # noqa
        )

        V = 0
        U = 0
        for _ in range(20):
            for point in points:
                X, Y, Z = point
                V += 10
                if V > 50:
                    V = 0
                U -= 10
                if U < -50:
                    U = 0

                moveTo(X, Y, Z, V=V)
                continue
                moveTo(X, Y, Z)
                rotateBed(U)
                tiltBed(V)

        rotateBed(U=0)
        tiltBed(V=0)
        moveTo(Z=100)
        moveTo(X=0, Y=0)

    def doDemo(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        rotateBed(U=0)
        tiltBed(V=0)

        points1 = (
            (-35,  12, 10), # noqa
            ( 35,  12, 10), # noqa
            (-35, -80, 10), # noqa
            ( 35, -80, 10), # noqa
        )
        points2 = (
            (-35,  42,  20), # noqa
            ( 35,  42,  20), # noqa
            (-35, -57, -24), # noqa
            ( 35, -57, -24), # noqa
        )
        points3 = (
            (-35, 65,  50), # noqa
            ( 35, 65,  50), # noqa
            (-35, -5, -35), # noqa
            ( 35, -5, -35), # noqa
        )

        U = getPos(axisU)
        for _ in range(50):
            moveTo(Z=100, F=2000)
            tiltBed(V=0)

            self._appendOutput('Area 1')
            for num, point in enumerate(points1):
                X, Y, Z = point
                moveTo(X, Y, Z, F=2000)

            moveTo(Z=100, F=2000)
            U += 90
            moveTo(V=25, U=U)

            self._appendOutput('Area 2')
            for num, point in enumerate(points2):
                X, Y, Z = point
                moveTo(X, Y, Z, F=2000)

            moveTo(Z=100, F=2000)
            U += 90
            moveTo(V=50, U=U)

            self._appendOutput('Area 3')
            for num, point in enumerate(points3):
                X, Y, Z = point
                moveTo(X, Y, Z, F=2000)

            moveTo(Z=100, F=2000)
            moveTo(X=0, Y=0)
            tiltBed(V=0)

        return

        points = (
            (  0, 100, 30), # noqa
            (-87, -50, 30), # noqa
            ( 87, -50, 30), # noqa
        )
        print(num, points)

    def doDemo2(self, *args, **kwargs):
        print(args, kwargs)

        doHoming()

        rotateBed(U=0)
        tiltBed(V=0)

        points1 = (
            (-35,  12, 10), # noqa
            ( 35,  12, 10), # noqa
            (-35, -80, 10), # noqa
            ( 35, -80, 10), # noqa
        )
        points2 = (
            (-35,  42,  20), # noqa
            ( 35,  42,  20), # noqa
            (-35, -57, -24), # noqa
            ( 35, -57, -24), # noqa
        )
        points3 = (
            (-35, 65,  50), # noqa
            ( 35, 65,  50), # noqa
            (-35, -5, -35), # noqa
            ( 35, -5, -35), # noqa
        )

        U = getPos(axisU)
        for _ in range(1):
            moveTo(Z=100, F=2000)
            tiltBed(V=0)

            radius = 100
            moveTo(Z=30, F=2000)
            for a in range(1, 361):
                X = radius * sin(radians(a))
                Y = radius * cos(radians(a))

                moveTo(X, Y)
                # rotateBed(a)

            moveTo(Z=100, F=2000)
            U += 90
            moveTo(V=25, U=U)

            self._appendOutput('Area 2')
            for num, point in enumerate(points2):
                X, Y, Z = point
                moveTo(X, Y, Z, F=2000)

            moveTo(Z=100, F=2000)
            U += 90
            moveTo(V=50, U=U)

            self._appendOutput('Area 3')
            for num, point in enumerate(points3):
                X, Y, Z = point
                moveTo(X, Y, Z, F=2000)

            moveTo(Z=100, F=2000)
            moveTo(X=0, Y=0)
            tiltBed(V=0)

        return

        points = (
            (  0, 100, 30), # noqa
            (-87, -50, 30), # noqa
            ( 87, -50, 30), # noqa
        )
        print(num, points)
