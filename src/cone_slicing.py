"""
Module contains logic behind the cone slicing
"""
from typing import Tuple

import numpy as np
from stl import mesh

from src.settings import sett


def load_mesh(filename: str) -> mesh:
    # TODO: we should take already loaded mesh object, because it might be rotated or translated
    model = mesh.Mesh.from_file(filename)

    s = sett()

    model.translate([s.slicing.originx, s.slicing.originy, s.slicing.originz])
    return model


def cross_stl(mesh_input: mesh.Mesh, cone: Tuple[float, Tuple[float, float, float]]):
    """
    Intersection lines of stl model and cone surface

    mesh - triangles from stl model (opened with numpy-stl library)
    Example:
    mesh = mesh.Mesh.from_file('support_var2.stl')
    mesh = array([
                     [ 1.4, -0.5, 20. ,  2.2, -0.9, 20. ,  2.3, -0.8, 20. ],
                     [ 1.4, -0.6, 20. ,  2.2, -0.9, 20. ,  2.2, -0.9, 20. ],
                    ],
                    dtype=float32)

    cone - cone surface
    cone = [10, [0, 0, 0]]
    cone[0] - cone angle in degrees
    cone[1] - vertex of the cone: [x, y, z]

    Function returns a List of paths for each layer
    """
    s = sett()
    layers = []
    vertex = [*cone[1]]
    starting_height = vertex[2]
    # update function to return layers
    for layer_idx in range(100):
        cross_p_list = []
        vertex[2] = starting_height + s.slicing.layer_height * layer_idx
        for triangle in mesh_input:
            t = [triangle[:3], triangle[3:6], triangle[6:9]]

            points = []
            for x, y in ((t[0], t[1]), (t[0], t[2]), (t[1], t[2])):
                cross_p = cone_cross(x, y, cone[0], np.array(vertex))  # find cross point(s) of line and cone
                if cross_p:
                    if len(cross_p) == 3:  # one intersection point of line and cone
                        if cross_p not in points:
                            points.append(cross_p)
                        elif len(cross_p) == 2:  # two intersection points of line and cone
                            points = cross_p
                        if len(points) in [2, 4, 6]:
                            cross_p_list.append(points)  # add intersection lines

        layers.append(cross_p_list)
    return layers
    # return cross_p_list  # example: array([[[ 2. , -0.7, 20. ], [ 2. , -0.7, 20. ]], [[ 1.6, -1.3, 20. ], [ 1.7, -1.3, 20. ]]])


def cone_cross(p_1, p_2, alpha_cone=10.0, p_cone=np.array([0.0, 0.0, 0.0])):
    """
    Intersection point(s) of line and cone surface

    p_1 - line 1st point: [x, y, z]
    p_2 - line 2nd point: [x, y, z]
    alpha_cone - cone angle in degrees
    p_cone - vertex of the cone: [x, y, z]
    """
    a = [p_2[0] - p_1[0], p_2[1] - p_1[1], p_2[2] - p_1[2]]  # direction vector of the line
    ctg_alpha_cone = 1 / np.tan(alpha_cone * np.pi / 180)
    a_1 = a[2] ** 2 - (a[0] ** 2 + a[1] ** 2) * ctg_alpha_cone ** 2
    b_1 = 2 * (a[2] * p_1[2] - a[2] * p_cone[2] - (a[0] * p_1[0] + a[1] * p_1[1]) * ctg_alpha_cone ** 2)
    c_1 = p_1[2] ** 2 + p_cone[2] ** 2 - 2 * p_cone[2] * p_1[2] - (p_1[0] ** 2 + p_1[1] ** 2) * ctg_alpha_cone ** 2
    D = b_1 ** 2 - 4 * a_1 * c_1  # discriminant

    if D > 0:
        lam_1 = (-b_1 - D ** 0.5) / (2 * a_1)
        lam_2 = (-b_1 + D ** 0.5) / (2 * a_1)

        x_1 = lam_1 * a[0] + p_1[0]
        y_1 = lam_1 * a[1] + p_1[1]
        z_1 = lam_1 * a[2] + p_1[2]

        x_2 = lam_2 * a[0] + p_1[0]
        y_2 = lam_2 * a[1] + p_1[1]
        z_2 = lam_2 * a[2] + p_1[2]

        # check that points are on the line
        check_points = [min(p_1[0], p_2[0]) <= x_1 <= max(p_1[0], p_2[0]),
                        min(p_1[1], p_2[1]) <= y_1 <= max(p_1[1], p_2[1]),
                        min(p_1[2], p_2[2]) <= z_1 <= max(p_1[2], p_2[2]),
                        min(p_1[0], p_2[0]) <= x_2 <= max(p_1[0], p_2[0]),
                        min(p_1[1], p_2[1]) <= y_2 <= max(p_1[1], p_2[1]),
                        min(p_1[2], p_2[2]) <= z_2 <= max(p_1[2], p_2[2])]
        if all(check_points) and z_1 <= p_cone[2] and z_2 <= p_cone[2]:
            return [[x_1, y_1, z_1], [x_2, y_2, z_2]]  # two intersection points
        elif all(check_points[:3]) and z_1 <= p_cone[2]:
            return [x_1, y_1, z_1]  # one intersection point: [x_1, y_1, z_1]
        elif all(check_points[3:]) and z_2 <= p_cone[2]:
            return [x_2, y_2, z_2]  # one intersection point: [x_2, y_2, z_2]

    elif D == 0:
        lam = -b_1 / (2 * a_1)
        x = lam * a[0] + p_1[0]
        y = lam * a[1] + p_1[1]
        z = lam * a[2] + p_1[2]
        return [x, y, z]  # one intersection point: [x, y, z]

    return 0  # no intersection points


if __name__ == "__main__":
    ...
    # load my_mesh
    # cross_stl(my_mesh[:10], [10, [0, 0, 32]])
