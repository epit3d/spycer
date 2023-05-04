from typing import List
import math
import numpy as np

class DeltaParams:
    def __init__(self, bedRadius: float, deltaRadius: float, homedHeight: float, diagonals: dict):
        self.bedRadius = bedRadius
        self.deltaRadius = deltaRadius
        self.homedHeight = homedHeight
        self.diagonals = diagonals

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
        else:
            # When the point is very close to the center
            # we need to set the angles to zero.
            A[3 * i + 0][0] = 1.0
            A[3 * i + 1][1] = 1.0
            A[3 * i + 2][2] = 1.0

            X[3 * i + 0] = x
            X[3 * i + 1] = y
            X[3 * i + 2] = z

    # Calculate least squares
    AT = [[A[j][i] for j in range(len(A))] for i in range(K)]
    ATA = [[0.0] * K for i in range(K)]
    ATX = [0.0] * K

    for i in range(K):
        for j in range(K):
            for k in range(len(A)):
                ATA[i][j] += AT[i][k] * A[k][j]

        for k in range(len(A)):
            ATX[i] += AT[i][k] * X[k]

    try:
        ATA_inv = np.linalg.inv(ATA)
        factors = np.matmul(ATA_inv, ATX)
    except np.linalg.LinAlgError:
        # Singular matrix, can't calculate factors
        return dp

    # Update delta params with calculated factors
    for i in range(K):
        dp.diagonals[i] *= factors[i]
        dp.towerPosition[i] += factors[i + 3]

    return dp
