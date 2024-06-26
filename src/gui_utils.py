from typing import Tuple, List, Dict

import vtk
import numpy as np
from PyQt5.QtWidgets import QMessageBox
from vtkmodules.vtkCommonColor import vtkNamedColors
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from vtkmodules.vtkCommonTransforms import vtkTransform
from vtkmodules.vtkFiltersSources import vtkLineSource, vtkConeSource
from vtkmodules.vtkRenderingCore import vtkActor, vtkPolyDataMapper, vtkAssembly

from src.settings import sett, get_color, get_color_rgb, PathBuilder


def findStlOrigin(vtkBlock):
    polydata = vtkBlock.GetMapper().GetInput()
    points = polydata.GetPoints()

    transform = vtkBlock.GetUserTransform()
    boundingBox = vtk.vtkBoundingBox()
    for i in range(points.GetNumberOfPoints()):
        point = points.GetPoint(i)
        boundingBox.AddPoint(transform.TransformPoint(point))

    center = [0.0, 0.0, 0.0]
    boundingBox.GetCenter(center)

    zMin = boundingBox.GetMinPoint()[2]

    return center[0], center[1], zMin


def getBounds(vtkBlock):
    bound = [0, 0, 0, 0, 0, 0]
    vtkBlock.GetBounds(bound)
    return bound


def createPlaneActorCircle():
    s = sett().hardware
    center = [s.plane_center_x, s.plane_center_y, s.plane_center_z]
    return createPlaneActorCircleByCenter(center)


def createPlaneActorCircleByCenter(center):
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(200)
    cylinder.SetRadius(sett().hardware.plane_diameter / 2)
    cylinder.SetHeight(0.1)
    cylinder.SetCenter(center[0], center[2] - 0.1, center[1])  # WHAT? vtk :(
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(get_color(sett().colors.plane))
    actor.GetProperty().SetOpacity(sett().common.opacity_table)
    actor.RotateX(90)
    return actor


def create_splane_actor(center, x_rot, z_rot):
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(50)
    cylinder.SetRadius(sett().common.splane_diameter / 2)
    cylinder.SetHeight(0.1)
    # cylinder.SetCenter(center[0], center[2] - 0.1, center[1])  # WHAT? vtk :(
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(get_color(sett().colors.splane))
    actor.GetProperty().SetOpacity(sett().common.opacity_plane)
    actor.RotateX(90)
    # actor.RotateX(x_rot)
    # actor.SetPosition(center[0], center[1],center[2] - 0.1)
    # actor.RotateY(x_rot)
    # actor.GetUserTransform()
    transform = vtk.vtkTransform()
    transform.PostMultiply()
    transform.RotateX(x_rot)
    transform.PostMultiply()
    transform.RotateZ(z_rot)
    transform.Translate(center[0], center[1], center[2] - 0.1)
    actor.SetUserTransform(transform)
    return actor


def create_cone_actor(
    vertex: Tuple[float, float, float], bending_angle: float, h1: float, h2: float
):
    # TODO maybe it is not good to pass cone object destructed (hard to add new parameters)
    """
    :param bending_angle: angle of triangles relative Z axis we want to compensate (in degrees)
    """

    if bending_angle == 0:
        actor = create_splane_actor(vertex, 0, 0)
        actor.GetProperty().SetRepresentationToWireframe()
        return actor

    sign = lambda x: 0 if not x else int(x / abs(x))

    # cone angle is complementary to bending angle
    # such that during print we would get a parallel surface to the XY base frame
    cone_angle = sign(bending_angle) * (90 - sign(bending_angle) * bending_angle)

    coneSource = vtkConeSource()
    coneSource.SetHeight(h2)
    # coneSource.SetAngle(angle)
    coneSource.SetResolution(120)
    # coneSource.SetHeight(vertex[2])
    import math

    coneSource.SetRadius(h2 * math.tan(math.radians(math.fabs(cone_angle))))
    coneSource.SetCenter(vertex[0], vertex[1], vertex[2] - sign(cone_angle) * h2 / 2)
    coneSource.SetDirection(0, 0, 1 * sign(cone_angle))
    coneSource.Update()
    # update parameters

    # plane to cut from h1
    clipPlane = vtk.vtkPlane()
    clipPlane.SetOrigin(vertex[0], vertex[1], vertex[2] - h1 * sign(cone_angle))
    clipPlane.SetNormal(0, 0, -1 * sign(cone_angle))

    clipper = vtk.vtkClipPolyData()
    clipper.SetInputConnection(coneSource.GetOutputPort())
    clipper.SetClipFunction(clipPlane)
    clipper.GenerateClipScalarsOff()
    clipper.GenerateClippedOutputOff()
    clipper.Update()

    # plane to cut to h2
    clipPlane2 = vtk.vtkPlane()
    clipPlane2.SetOrigin(vertex[0], vertex[1], vertex[2] - h2 * sign(cone_angle))
    clipPlane2.SetNormal(0, 0, 1 * sign(cone_angle))

    clipper2 = vtk.vtkClipPolyData()
    clipper2.SetInputConnection(clipper.GetOutputPort())
    clipper2.SetClipFunction(clipPlane2)
    clipper2.GenerateClipScalarsOff()
    clipper2.GenerateClippedOutputOff()
    clipper2.Update()

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(clipper2.GetOutputPort())

    actor = vtkActor()
    actor.SetMapper(mapper)

    # create a checkbox for visualization
    actor.GetProperty().SetRepresentationToWireframe()
    actor.GetProperty().SetColor(get_color(sett().colors.splane))
    actor.GetProperty().SetOpacity(sett().common.opacity_plane)

    return actor


def createBoxActors():
    s = sett()

    res = []
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(50)
    cylinder.SetRadius(3)
    cylinder.SetHeight(200)
    cylinder.SetCenter(
        s.hardware.plane_center_x - 100,
        s.hardware.plane_center_z,
        s.hardware.plane_center_y + 100,
    )  # WHAT? vtk :(
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(get_color(s.colors.blue))
    actor.RotateX(90)
    res.append(actor)

    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(50)
    cylinder.SetRadius(3)
    cylinder.SetHeight(200)

    cylinder.SetCenter(
        s.hardware.plane_center_x + 100,
        s.hardware.plane_center_z,
        s.hardware.plane_center_y - 100,
    )  # WHAT? vtk :(
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(get_color(s.colors.plane))
    actor.GetProperty().SetOpacity(sett().common.opacity_plane)
    actor.RotateY(90)
    res.append(actor)

    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(50)
    cylinder.SetRadius(3)
    cylinder.SetHeight(200)
    cylinder.SetCenter(
        s.hardware.plane_center_x - 100,
        s.hardware.plane_center_z,
        s.hardware.plane_center_y - 100,
    )  # WHAT? vtk :(
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(get_color(s.colors.last_layer))
    actor.GetProperty().SetOpacity(sett().common.opacity_current_plane)
    actor.RotateZ(90)
    res.append(actor)

    return res


def createAxes(interactor):
    axesWidget = vtk.vtkOrientationMarkerWidget()
    rgba = [0] * 4
    vtk.vtkNamedColors().GetColor("Carrot", rgba)
    axesWidget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
    axesWidget.SetOrientationMarker(vtk.vtkAxesActor())
    axesWidget.SetInteractor(interactor)
    axesWidget.SetViewport(0.0, 0.0, 0.3, 0.3)
    axesWidget.SetEnabled(1)
    axesWidget.InteractiveOff()
    return axesWidget


def createStlActor(filename):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)
    reader.Update()
    return build_actor(reader), reader


def createStlActorInOrigin(filename, colorize=False):
    actor, reader = createStlActor(filename)
    output = reader.GetOutput()

    actor = StlActor(output)

    if colorize:
        actor.ColorizeCriticalOverhangs()

    actor = setTransformFromSettings(actor)
    return actor


def setTransformFromSettings(actor):
    s = sett()
    transform = vtk.vtkTransform()

    m = vtkMatrix4x4()
    for i in range(4):
        for j in range(4):
            m.SetElement(i, j, getattr(s.slicing.transformation_matrix, f"m{i}{j}"))

    transform.SetMatrix(m)
    actor.SetUserTransform(transform)

    return actor


def makeBlocks(layers, rotations, lays2rots):
    blocks = []
    for i in range(len(layers)):
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        block = vtk.vtkPolyData()
        points_count = 0
        for path in layers[i]:
            line = vtk.vtkLine()
            for k in range(len(path) - 1):
                points.InsertNextPoint(path[k].xyz(rotations[lays2rots[i]]))
                line.GetPointIds().SetId(0, points_count + k)
                line.GetPointIds().SetId(1, points_count + k + 1)
                lines.InsertNextCell(line)
            points.InsertNextPoint(
                path[-1].xyz(rotations[lays2rots[i]])
            )  # not forget to add last point
            points_count += len(path)
        block.SetPoints(points)
        block.SetLines(lines)
        blocks.append(block)
    return blocks


def wrapWithActors(blocks, rotations, lays2rots):
    actors = []
    s = sett()
    for i in range(len(blocks)):
        block = blocks[i]
        actor = build_actor(block, True)
        # rotate to abs coords firstly and then apply last rotation
        tnf = prepareTransform(rotations[lays2rots[i]], rotations[0])
        actor.SetUserTransform(tnf)

        actor.GetProperty().SetColor(get_color(s.colors.layer))
        actor.GetProperty().SetOpacity(sett().common.opacity_layer)
        actors.append(actor)

    actors[-1].GetProperty().SetColor(get_color(s.colors.last_layer))
    actors[-1].GetProperty().SetOpacity(sett().common.opacity_last_layer)
    return actors


#  R(V - rotcentr) + rotcenter
def prepareTransform(cancelRot, applyRot):
    sh = sett().hardware
    tf = vtk.vtkTransform()
    # cancel rotation
    tf.PostMultiply()
    tf.Translate(-sh.rotation_center_x, -sh.rotation_center_y, -sh.rotation_center_z)
    tf.PostMultiply()
    tf.RotateX(-cancelRot.x_rot)
    tf.PostMultiply()
    tf.RotateZ(-cancelRot.z_rot)
    # tf.PostMultiply()    #Translates are canceled T+T-=0
    # tf.Translate(sh.rotation_center_x, sh.rotation_center_y, sh.rotation_center_z)

    # apply rotation
    # tf.PostMultiply()
    # tf.Translate(-sh.rotation_center_x, -sh.rotation_center_y, -sh.rotation_center_z)
    tf.PostMultiply()
    tf.RotateZ(applyRot.z_rot)
    tf.PostMultiply()
    tf.RotateX(applyRot.x_rot)
    tf.PostMultiply()
    tf.Translate(sh.rotation_center_x, sh.rotation_center_y, sh.rotation_center_z)
    return tf


def plane_tf(rotation):
    sh = sett().hardware
    tf = vtk.vtkTransform()
    tf.PostMultiply()
    tf.Translate(-sh.rotation_center_x, -sh.rotation_center_y, -sh.rotation_center_z)
    tf.PostMultiply()
    tf.RotateZ(rotation.z_rot)
    tf.PostMultiply()
    tf.RotateX(rotation.x_rot)
    tf.PostMultiply()
    tf.Translate(sh.rotation_center_x, sh.rotation_center_y, sh.rotation_center_z)
    return tf


class ActorFromPolyData(vtkActor):
    def __init__(self, output):
        super().__init__()
        mapper = vtkPolyDataMapper()
        mapper.SetInputData(output)
        self.SetMapper(mapper)


class ActorWithColor(vtkAssembly):
    def __init__(self, output):
        polys = output.GetPolys()
        allpoints = output.GetPoints()

        tocolor = []
        with open(PathBuilder.colorizer_result(), "rb") as f:
            content = f.read()
            for b in content:
                if b == 1:
                    tocolor.append(True)
                else:
                    tocolor.append(False)

        triangles = vtk.vtkCellArray()
        triangles2 = vtk.vtkCellArray()
        for i in range(polys.GetSize()):
            idList = vtk.vtkIdList()
            polys.GetNextCell(idList)
            num = idList.GetNumberOfIds()
            if num != 3:
                break

            triangle = vtk.vtkTriangle()
            triangle.GetPointIds().SetId(0, idList.GetId(0))
            triangle.GetPointIds().SetId(1, idList.GetId(1))
            triangle.GetPointIds().SetId(2, idList.GetId(2))

            if tocolor[i]:
                triangles.InsertNextCell(triangle)
            else:
                triangles2.InsertNextCell(triangle)

        trianglePolyData = vtk.vtkPolyData()
        trianglePolyData.SetPoints(allpoints)
        trianglePolyData.SetPolys(triangles)
        trianglePolyData2 = vtk.vtkPolyData()
        trianglePolyData2.SetPoints(allpoints)
        trianglePolyData2.SetPolys(triangles2)

        actor = ActorFromPolyData(trianglePolyData)
        actor.GetProperty().SetColor(get_color(sett().colorizer.color))
        actor2 = ActorFromPolyData(trianglePolyData2)

        self.AddPart(actor)
        self.AddPart(actor2)


def build_actor(source, as_is=False):
    if as_is:
        return ActorFromPolyData(source)
    else:
        return ActorFromPolyData(source.GetOutput())


class StlActorMixin:
    lastMove = (0, 0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tfUpdateMethods = []

        self.findBounds()
        self.findCenter()
        self.ResetColorize()

    def findBounds(self):
        self.bound = getBounds(self)

    def findCenter(self):
        x_mid = (self.bound[0] + self.bound[1]) / 2
        y_mid = (self.bound[2] + self.bound[3]) / 2
        z_mid = (self.bound[4] + self.bound[5]) / 2
        self.center = x_mid, y_mid, z_mid

    def addUserTransformUpdateCallback(self, *methods):
        self.tfUpdateMethods += methods
        tf = self.GetUserTransform()
        self._execUserTransformUpdateCallback(tf)

    def SetUserTransform(self, *args, **kwargs):
        tf = args[0]
        self._execUserTransformUpdateCallback(tf)
        super().SetUserTransform(*args, **kwargs)

    def _execUserTransformUpdateCallback(self, tf):
        сenterTf = vtkTransform()
        сenterTf.DeepCopy(tf)
        сenterTf.Translate(self.center)
        ox, oy, oz = сenterTf.GetPosition()
        _, _, cz = self.center
        _, _, _, _, bnz, _ = self.bound
        center = ox, oy, oz - (cz - bnz)
        for method in self.tfUpdateMethods:
            method(center, tf.GetOrientation(), tf.GetScale())

    def ColorizeCriticalOverhangs(self):
        with open(PathBuilder.colorizer_result(), "rb") as f:
            content = f.read()

            model_color = get_color_rgb(sett().colors.model)
            critical_color = get_color_rgb(sett().colors.last_layer)

            colors = vtk.vtkUnsignedCharArray()
            colors.SetNumberOfComponents(3)
            colors.SetNumberOfTuples(len(content))

            for i, b in enumerate(content):
                if b == 1:
                    colors.SetTuple(i, critical_color)
                else:
                    colors.SetTuple(i, model_color)

            poly_data = self.GetMapper().GetInput()
            poly_data.GetCellData().SetScalars(colors)

    def ResetColorize(self):
        poly_data = self.GetMapper().GetInput()
        number_triangles = poly_data.GetNumberOfCells()

        model_color = get_color_rgb(sett().colors.model)

        colors = vtk.vtkUnsignedCharArray()
        colors.SetNumberOfComponents(3)
        colors.SetNumberOfTuples(number_triangles)

        for i in range(number_triangles):
            colors.SetTuple(i, model_color)

        poly_data.GetCellData().SetScalars(colors)

    def GetTriangleNormal(self, triangle_id):
        poly_data = self.GetMapper().GetInput()
        triangle = poly_data.GetCell(triangle_id)

        v0 = triangle.GetPoints().GetPoint(0)
        v1 = triangle.GetPoints().GetPoint(1)
        v2 = triangle.GetPoints().GetPoint(2)

        side1 = np.array(v1) - np.array(v0)
        side2 = np.array(v2) - np.array(v0)

        normal = np.cross(side1, side2)
        normal /= np.linalg.norm(normal)

        return normal

    def RotateByVector(self, vector):
        v = [0, 0, 1]
        theta = np.arccos(
            np.dot(vector, v) / (np.linalg.norm(vector) * np.linalg.norm(v))
        )
        rotation_angle = np.degrees(theta)

        if np.array_equal(vector, [0, 0, -1]):
            rotation_axis = [-1, 0, 0]
        else:
            rotation_axis = np.cross(vector, v)

        rotation_matrix = self.GetUserTransform()

        scale = [0.0, 0.0, 0.0]
        rotation_matrix.GetScale(scale)
        rotation_matrix.Identity()
        rotation_matrix.RotateWXYZ(rotation_angle, rotation_axis)
        rotation_matrix.Scale(scale)

        self.SetUserTransform(rotation_matrix)


class StlActor(StlActorMixin, ActorFromPolyData):
    def __init__(self, output):
        super().__init__(output)


class ColorizedStlActor(StlActorMixin, ActorWithColor):
    def __init__(self, output):
        super().__init__(output)


class Plane:
    def __init__(self, incl, rot, point, smooth=False):
        self.incline = incl
        self.x = point[0]
        self.y = point[1]
        self.z = point[2]
        self.rot = rot
        self.smooth = smooth

    def toFile(self):
        plane = f"plane X{self.x:.2f} Y{self.y:.2f} Z{self.z:.2f} T{self.incline:.2f} R{self.rot:.2f}"
        if self.smooth:
            plane += " S"
        return plane

    def params(self) -> Dict[str, float]:
        return {
            "X": self.x,
            "Y": self.y,
            "Z": self.z,
            "Rotation": self.rot,
            "Tilt": self.incline,
            "Smooth": self.smooth,
        }

    def __eq__(self, value: object) -> bool:
        if not isinstance(value, Plane):
            return False
        return (
            self.x == value.x
            and self.y == value.y
            and self.z == value.z
            and self.incline == value.incline
            and self.rot == value.rot
            and self.smooth == value.smooth
        )


class Cone:
    def __init__(
        self,
        cone_angle: float,
        point: Tuple[float, float, float],
        h1: float = 0,
        h2: float = 100,
    ):
        self.cone_angle = cone_angle
        self.x, self.y, self.z = point
        self.h1 = h1
        self.h2 = h2

    def toFile(self) -> str:
        return f"cone X{self.x:.2f} Y{self.y:.2f} Z{self.z:.2f} A{self.cone_angle:.2f} H{self.h1:.2f} H{self.h2:.2f}"

    def params(self) -> Dict[str, float]:
        return {
            "X": self.x,
            "Y": self.y,
            "Z": self.z,
            "A": self.cone_angle,
            "H1": self.h1,
            "H2": self.h2,
        }


def read_planes(filename):
    planes = []
    with open(filename) as fp:
        for line in fp:
            planes.append(read_plane(line))

    return planes


def read_plane(line: str):
    v = line.strip().split(" ")

    if v[0] == "plane":
        # plane X10 Y10 Z10 T-60 R0 - Plane string format
        return Plane(
            float(v[4][1:]),
            float(v[5][1:]),
            (float(v[1][1:]), float(v[2][1:]), float(v[3][1:])),
            len(v) > 6 and v[6] == "S",
        )
    else:
        # cone X0 Y0 Z10 A60 H10 H50 - Cone string format
        return Cone(
            float(v[4][1:]),
            (float(v[1][1:]), float(v[2][1:]), float(v[3][1:])),
            float(v[5][1:]),
            float(v[6][1:]),
        )


def isfloat(value):
    try:
        float(value)
        return True
    except ValueError:
        return False


def showErrorDialog(text_msg):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Critical)

    msg.setText(text_msg)
    # msg.setInformativeText("This is additional information")
    msg.setWindowTitle("Error")
    # msg.setDetailedText("The details are as follows:")
    msg.setStandardButtons(QMessageBox.Close)
    # msg.buttonClicked.connect(msgbtn)

    retval = msg.exec_()
    # print "value of pressed message box button:", retval


def showInfoDialog(text_msg):
    msg = QMessageBox()
    msg.setIcon(QMessageBox.Information)

    msg.setText(text_msg)
    msg.setWindowTitle("Info")
    msg.setStandardButtons(QMessageBox.Close)

    retval = msg.exec_()


def createCustomXYaxis(
    origin: Tuple[float, float, float], endPoints: List[Tuple[float, float, float]]
) -> List[vtkActor]:
    """
    Function creates 4 ended axes which describe position of focal point
    :param origin:
    :param endPoints:
    :return:
    """

    output = []

    for endPoint in endPoints:
        output.append(createLine(origin, endPoint, color="lightgreen"))

    return output


def createLine(point1: tuple, point2: tuple, color: str = "Black") -> vtkActor:
    """
    :param point1:
    :param point2:
    :param color:
    :return:
    """
    line = vtkLineSource()

    line.SetPoint1(*point1)
    line.SetPoint2(*point2)

    mapper = vtkPolyDataMapper()
    mapper.SetInputConnection(line.GetOutputPort())

    actor = vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(vtkNamedColors().GetColor3d(color))

    return actor


class StlMover:
    def __init__(self, view):
        self.view = view
        self.tf = vtkTransform()

    def getTransform(self):
        self.view.boxWidget.GetTransform(self.tf)

    def setTransform(self):
        self.view.boxWidget.SetTransform(self.tf)
        self.view.stlActor.SetUserTransform(self.tf)
        self.view.updateTransform()
        self.view.reload_scene()
        self.view.save_current_movement()

    def set(self, text, axis):
        try:
            val = float(text)
        except ValueError:
            val = 0
        self.getTransform()
        self.setMethod(val, axis)
        self.setTransform()

    def setMethod(self, val, axis):
        pass

    def act(self, val, axis):
        self.getTransform()
        self.actMethod(val, axis)
        self.setTransform()

    def actMethod(self, val, axis):
        pass


class StlTranslator(StlMover):
    def __init__(self, view):
        super().__init__(view)

    def setMethod(self, val, axis):
        x, y, z = axis
        cx, cy, cz = self.view.stlActor.center
        _, _, _, _, bnz, _ = self.view.stlActor.bound
        self.tf.Translate(cx, cy, cz)
        m = vtkMatrix4x4()
        self.tf.GetMatrix(m)
        m.SetElement((x * 1 + y * 2 + z * 3) - 1, 3, val + (cz - bnz) * z)
        self.tf.SetMatrix(m)
        self.tf.Translate(-cx, -cy, -cz)

    def actMethod(self, val, axis):
        x, y, z = axis
        self.tf.PostMultiply()
        self.tf.Translate(x * val, y * val, z * val)
        self.tf.PreMultiply()


class StlRotator(StlMover):
    def __init__(self, view):
        super().__init__(view)

    def setMethod(self, val, axis):
        x, y, z = axis
        cx, cy, cz = self.view.stlActor.center
        rx, ry, rz = self.tf.GetOrientation()
        rx = val - rx if x else 0
        ry = val - ry if y else 0
        rz = val - rz if z else 0

        tf = vtkTransform()
        tf.Translate(cx, cy, cz)

        tf.RotateZ(rz)
        tf.RotateX(rx)
        tf.RotateY(ry)

        tf.Translate(-cx, -cy, -cz)
        tf.Concatenate(self.tf)

        self.tf = tf

    def actMethod(self, val, axis):
        x, y, z = axis
        rx, ry, rz = self.tf.GetOrientation()
        val = val + rx if x else val
        val = val + ry if y else val
        val = val + rz if z else val

        self.setMethod(val, axis)


class StlScale(StlMover):
    def __init__(self, view):
        super().__init__(view)

    def setMethod(self, val, axis):
        x, y, z = axis
        x1, y1, z1 = self.tf.GetScale()
        val = val if val > 0 else 1
        val = val / 100

        sx = val / x1 if x else 1
        sy = val / y1 if y else 1
        sz = val / z1 if z else 1

        tf = vtk.vtkTransform()
        tf.Scale(sx, sy, sz)
        tf.Concatenate(self.tf)

        self.tf = tf

    def actMethod(self, val, axis):
        x, y, z = axis
        rx, ry, rz = self.tf.GetScale()
        val = val + rx * 100 if x else val
        val = val + ry * 100 if y else val
        val = val + rz * 100 if z else val

        self.setMethod(val, axis)
