from typing import List

class DeltaParams:
    def __init__(self):
        self.diagonals = {
            'X': 0.0,
            'Y': 0.0,
            'Z': 0.0,
        }
        self.deltaRadius = 0.0
        self.homedHeight = 0.0
        self.bedRadius = 0.0
        self.towerAngCorr = {
            'X': 0.0,
            'Y': 0.0,
            'Z': 0.0,
        }
        self.endstopCorr = {
            'X': 0.0,
            'Y': 0.0,
            'Z': 0.0,
        }
        self.bedTilt = {
            'X': 0.0,
            'Y': 0.0,
        }

class Point:
    def __init__(self, X: float, Y: float, Z: float):
        self.X = X
        self.Y = Y
        self.Z = Z

def Esher(dp: DeltaParams, points: List[Point], factorsNumber: int) -> DeltaParams:
    K = factorsNumber
    M = len(points)

    A = [[0.0] * K for i in range(M * 3)]
    X = [0.0] * (M * 3)

    # Fill A matrix and X vector
    for i, point in enumerate(points):
        x, y, z = point.X, point.Y, point.Z

        r2 = x * x + y * y
        r = pow(r2, 0.5)

        if r > dp.deltaRadius:
            continue

        sqrt3 = 1.73205080757
        sin120 = sqrt3 / 2.0
        cos120 = -0.5
        sin240 = -sqrt3 / 2.0
        cos240 = -0.5

        x3 = dp.diagonals['X']
        y3 = dp.diagonals['Y']
        z3 = dp.diagonals['Z']

        if r > 1e-6:
            zp = z - dp.homedHeight
            theta = math.atan2(y, x)
            phi = math.atan2(zp, r)

            # Trigonometric relations
            sinTheta = math.sin(theta)
            cosTheta = math.cos(theta)
            sinPhi = math.sin(phi)
            cosPhi = math.cos(phi)
            sinThetaPhi = math.sin(theta + phi)
            cosThetaPhi = math.cos(theta + phi)

            # Tower X
            A[3 * i + 0][0] = x3 * sinThetaPhi - y3 * cosThetaPhi
            A[3 * i + 0][1] = zp
            A[3 * i + 0][2] = dp.bedRadius - r

            # Tower Y
            A[3 * i + 1][0] = x3 * (cos120 * cosTheta + sin120 * sinThetaPhi) - \
                              y3 * (cos120 * sinTheta - sin120 * cosThetaPhi)
            A[3 * i + 1][1] = zp
            A[3 * i + 1][2] = dp.bedRadius - r

            # Tower Z
            A[3 * i + 2][0] = x3* (cos240 * cosTheta + sin240 * sinThetaPhi) - \
                          y3 * (cos240 * sinTheta - sin240 * cosThetaPhi)
            A[3 * i + 2][1] = zp
            A[3 * i + 2][2] = dp.bedRadius - r

            X[3 * i + 0] = x
            X[3 * i + 1] = y
            X[3 * i + 2] = z

    # Calculate least squares
    ATA = numpy.dot(numpy.transpose(A), A)
    ATX = numpy.dot(numpy.transpose(A), X)
    dp.towerAngCorr = numpy.dot(numpy.linalg.inv(ATA), ATX)

    # Endstop corrections
    dp.endstopCorr = {
        'X': dp.diagonals['X'] - dp.towerAngCorr[0],
        'Y': dp.diagonals['Y'] - dp.towerAngCorr[1],
        'Z': dp.diagonals['Z'] - dp.towerAngCorr[2],
    }

    # Bed tilt
    B = [[0.0] * 3 for i in range(2)]
    for i in range(2):
        B[i][0] = A[i * 3][0] - A[i * 3 + 2][0]
        B[i][1] = A[i * 3][1] - A[i * 3 + 2][1]
        B[i][2] = A[i * 3][2] - A[i * 3 + 2][2]

    C = numpy.dot(numpy.linalg.inv(numpy.dot(numpy.transpose(B), B)),
                numpy.transpose(B))
    D = numpy.dot(C, dp.endstopCorr.values())
    dp.bedTilt = {
        'X': D[0],
        'Y': D[1],
    }

    return dp






