import numpy as np
from math import sin, cos, radians


def polar2cart(angle, radius):
    return radius * cos(radians(angle)), radius * sin(radians(angle))


def rotateVector(vector, angle):
    alpha = radians(angle)

    # use rotation matrix around X axis
    matrix = np.array([
        [1,          0,           0],  # noqa
        [0, cos(alpha), -sin(alpha)],  # noqa
        [0, sin(alpha),  cos(alpha)],  # noqa
    ])

    return np.array([
        vector.dot(matrix[0]),
        vector.dot(matrix[1]),
        vector.dot(matrix[2]),
    ])


def tiltPoint(point, angle, rotVector):
    rotVector = np.array(rotVector)
    vector = np.array(point)
    return rotateVector(vector - rotVector, angle) + rotVector
