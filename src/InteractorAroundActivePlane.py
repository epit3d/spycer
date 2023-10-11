"""
Module contains custom interactor for vtk
inspired by: https://fossies.org/linux/VTK/Examples/GUI/Python/CustomInteraction.py
"""
from typing import Tuple

import numpy as np
import vtk, src

from src.gui_utils import createCustomXYaxis


def unit(vector: np.array) -> np.array:
    """
    Function normalizes the given vector
    :param vector: Any one-dimensional vector
    :return: one-dimensional unit vector with the same direction
    """
    return np.array([*vector]) / np.sqrt((vector * vector).sum(axis=0))


def RZ(rotRadian: float):
    """
    Creates numpy matrix for rotation around Z-axis
    :param rotRadian: angle of rotations in radians
    :return: numpy matrix of 3 by 3 size
    """
    return np.array([
        [np.cos(rotRadian), -np.sin(rotRadian), 0],
        [np.sin(rotRadian), np.cos(rotRadian), 0],
        [0, 0, 1]
    ])


def Raxis(axis: Tuple[float, float, float], a: float, origin=np.array([0, 0, 0])):
    """
    Creates numpy matrix for rotation around custom axis
    source: https://en.wikipedia.org/wiki/Rotation_matrix
    :param origin:
    :param axis: Tuple of array of 3 components
    :param a: angle of rotation in radians
    :return: numpy matrix of 4 by 4 size (trasformation)
    """
    oneminuscos = 1 - np.cos(a)
    x, y, z = axis

    return np.array([
        [np.cos(a) + (x ** 2) * oneminuscos, x * y * oneminuscos - z * np.sin(a), x * z * oneminuscos + y * np.sin(a),
         origin[0]],
        [y * x * oneminuscos + z * np.sin(a), np.cos(a) + (y ** 2) * oneminuscos, y * z * oneminuscos - x * np.sin(a),
         origin[1]],
        [z * x * oneminuscos - y * np.sin(a), z * y * oneminuscos + x * np.sin(a), np.cos(a) + (z ** 2) * oneminuscos,
         origin[2]],
        [0, 0, 0, 1]
    ])


class InteractionAroundActivePlane:
    pos = np.array([250, 250, 250, 0], dtype=float)
    focalPoint = np.array([0, 0, 0, 0], dtype=float)
    distanceToFocal = np.linalg.norm(pos - focalPoint)

    # True when we pressed left btn, False when we released
    isRotating = False

    # True when pressed right btn, False when we released
    isMoving = False

    # speed for rotation, used to calculate angular velocity depending on focal distance
    ROTATION_SPEED = 0.04

    def __init__(self, currentInteractor, render):
        self.interactor = currentInteractor
        self.render = render
        self.camera = self.render.GetActiveCamera()

        self.axes = []

            # real ability
            # actor.SetOrigin(1, 0, 1)
            # actor.SetOrientation(0, 0, 90)

    def leftBtnPress(self, obj, event, view = None):
        """
        These events are bind: "LeftButtonPressEvent" "LeftButtonReleaseEvent"
        """
        self.isRotating = event == "LeftButtonPressEvent"

        clickPos = self.interactor.GetEventPosition()
            
        picker = vtk.vtkPropPicker()

        self.NewPickedActor = picker.GetActor()
        picker.Pick(clickPos[0], clickPos[1], 0, self.render)

        picker1 = vtk.vtkCellPicker()
        picker1.SetTolerance(0.005)
        picker1.Pick(clickPos[0], clickPos[1], 0, self.render)

        if (picker1.GetCellId() >= 0) and (isinstance(picker.GetActor(), src.gui_utils.StlActor)) and view:
            triangle_id = picker1.GetCellId()

            poly_data = picker.GetActor().GetMapper().GetInput()

            poly_data1 = vtk.vtkPolyData()
            poly_data1.DeepCopy(picker.GetActor().GetMapper().GetInput())

            triangles = poly_data.GetPolys()
            points = poly_data.GetPoints()
            normals = []

            triangles.InitTraversal()
            triangle = vtk.vtkIdList()

            while triangles.GetNextCell(triangle):
                v0 = points.GetPoint(triangle.GetId(0))
                v1 = points.GetPoint(triangle.GetId(1))
                v2 = points.GetPoint(triangle.GetId(2))

                side1 = np.array(v1) - np.array(v0)
                side2 = np.array(v2) - np.array(v0)

                normal = np.cross(side1, side2)
                normal /= np.linalg.norm(normal)
                normals.append(normal)

            if normals:
                selected_triangle_normal = normals[triangle_id]
                theta = np.arccos(np.dot(selected_triangle_normal, [0, 0, -1]) / (np.linalg.norm(selected_triangle_normal) * np.linalg.norm([0, 0, -1])))
                rotation_axis = np.cross(selected_triangle_normal, [0, 0, -1])

                rotation_matrix = vtk.vtkTransform()
                rotation_matrix.Identity()
                rotation_matrix.RotateWXYZ(np.degrees(theta), rotation_axis)

                picker.GetActor().SetUserTransform(rotation_matrix)

                if view:
                    view.model_centering()

            if view:
                view.reload_scene()

    def middleBtnPress(self, obj, event):
        if event == "MouseWheelForwardEvent":
            self.distanceToFocal -= 0.1 * self.distanceToFocal
            # we block the minimal distance to focal point
            self.distanceToFocal = max(self.distanceToFocal, 3)
        else:
            self.distanceToFocal += 0.1 * self.distanceToFocal

        self.pos = unit(self.pos) * self.distanceToFocal
        self.render.GetActiveCamera().SetPosition(*self.pos[:3])
        self.interactor.ReInitialize()

    def rightBtnPress(self, obj, event):
        """
        These events are bind: "RightButtonPressEvent", "RightButtonReleaseEvent"
        """
        self.isMoving = event == "RightButtonPressEvent"

    def mouseMove(self, obj, event, view):
        xLast, yLast = self.interactor.GetLastEventPosition()
        xCur, yCur = self.interactor.GetEventPosition()
        angleSpeed = self.ROTATION_SPEED
        if self.isRotating:
            deltaOnYaw = xCur - xLast
            # negative when we tend to viewGoesAlongZ = 1
            # positive when we tend to viewGoesAlongZ = -1
            deltaOnPitchRoll = yCur - yLast
            # that means if we are close to critical points, we may allow to move in opposite direction

            # apply rotation around Z-axis
            self.pos = Raxis((0, 0, 1), np.deg2rad(-deltaOnYaw * angleSpeed), self.focalPoint).dot(np.array(self.pos))

            # float in range (-1, 1) where if abs == 1 means camera view is on the z-axis
            # 1 - we are facing in opposite direction than z-axis
            # -1 - we are facing along direction of z-axis
            viewGoesAlongZ = np.dot(np.array([0, 0, 1]), unit(self.pos[:3]))
            # normalize value
            maxv = 2  # normalizing range for deltaOnPitchRoll
            deltaOnPitchRoll = maxv if deltaOnPitchRoll > maxv else -maxv if deltaOnPitchRoll < -maxv else deltaOnPitchRoll

            # do not allow camera go too along with z-axis
            threshold = 0.95

            if abs(viewGoesAlongZ) < threshold or (viewGoesAlongZ < threshold and deltaOnPitchRoll < 0) or (
                    viewGoesAlongZ > threshold and deltaOnPitchRoll > 0):
                self.pos = Raxis((self.pos[1], -self.pos[0], 0), np.deg2rad(-deltaOnPitchRoll / self.distanceToFocal / 2),
                                 self.focalPoint).dot(np.array(self.pos))

        if self.isMoving:
            # in this type we will have to move only on 2 axis
            # if we move mouse up-down we will move along projection of line connecting the camera with the origin
            # if we move mouse left-right we will move along perpendicular line to the previous one, also in xy plane

            projVector = unit(np.array([self.pos[0] - self.focalPoint[0], self.pos[1] - self.focalPoint[1]]))
            perpVector = unit(np.array([projVector[1], -projVector[0]]))

            deltaOnProjection: float = xCur - xLast
            deltaOnPerpendicular: float = yCur - yLast

            factor = self.distanceToFocal * 0.001

            # movement along projection: (we change only xy coordinates)
            self.focalPoint[:2] += projVector * factor * deltaOnPerpendicular
            self.pos[:2] += projVector * factor * deltaOnPerpendicular

            # movement along perpendicular line to projection: (we change only xy coordinates)
            self.focalPoint[:2] += perpVector * factor * deltaOnProjection
            self.pos[:2] += perpVector * factor * deltaOnProjection

            for idx, axis in enumerate(self.axes):
                axis.SetPosition(*self.focalPoint[:3])
                axis.SetOrigin(*self.focalPoint[:3])

        # update position and camera
        self.pos = unit(self.pos) * self.distanceToFocal
        self.render.GetActiveCamera().SetPosition(*self.pos[:3])
        self.render.GetActiveCamera().SetFocalPoint(*self.focalPoint[:3])
        self.interactor.ReInitialize()

        clickPos = self.interactor.GetEventPosition()
            
        picker = vtk.vtkPropPicker()

        self.NewPickedActor = picker.GetActor()
        picker.Pick(clickPos[0], clickPos[1], 0, self.render)

        picker1 = vtk.vtkCellPicker()
        picker1.SetTolerance(0.005)
        picker1.Pick(clickPos[0], clickPos[1], 0, self.render)

        if (picker1.GetCellId() >= 0) and (isinstance(picker.GetActor(), src.gui_utils.StlActor)):
            triangle_id = picker1.GetCellId()
            poly_data = picker.GetActor().GetMapper().GetInput()
            colors = poly_data.GetCellData().GetScalars()

            num_triangles = poly_data.GetNumberOfCells()
            colors = vtk.vtkUnsignedCharArray()
            colors.SetNumberOfComponents(3)
            colors.SetNumberOfTuples(num_triangles)
            for i in range(num_triangles):
                colors.SetTuple(i, (255, 255, 255))

            colors.SetTuple(triangle_id, (255, 0, 0))
            poly_data.GetCellData().SetScalars(colors)

            mapper = picker.GetActor().GetMapper()
            mapper.Modified()

            if view:
                view.reload_scene()
