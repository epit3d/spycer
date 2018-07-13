import vtk
import params


def findStlOrigin(vtkBlock):
    bound = [0, 0, 0, 0, 0, 0]
    vtkBlock.GetBounds(bound)
    x_mid = (bound[0] + bound[1]) / 2
    y_mid = (bound[2] + bound[3]) / 2
    return x_mid, y_mid, bound[4]


def createPlaneActor():
    planeSource = vtk.vtkPlaneSource()
    # small indent from object plane, render problems, 200x200 plane
    xsize = params.PlaneXSize
    ysize = params.PlaneYSize
    planeSource.SetOrigin(- xsize / 2, - ysize / 2, - 0.1)
    planeSource.SetPoint1(+ xsize / 2, - ysize / 2, - 0.1)
    planeSource.SetPoint2(- xsize / 2, + ysize / 2, - 0.1)
    planeSource.Update()
    planeActor = build_actor(planeSource)
    planeActor.GetProperty().SetColor(params.PlaneColor)
    return planeActor

def createPlaneActor2():
    xsize = params.PlaneXSize
    ysize = params.PlaneYSize

    points = vtk.vtkPoints()
    points.InsertNextPoint((-xsize/2, -ysize/2, -0.1))
    points.InsertNextPoint((+xsize/2, -ysize/2, -0.1))
    points.InsertNextPoint((+xsize/2, +ysize/2, -0.1))
    points.InsertNextPoint((-xsize / 2, +ysize / 2, -0.1))

    triangle = vtk.vtkTriangle()
    triangle.GetPointIds().SetId(0, 0)
    triangle.GetPointIds().SetId(1, 1)
    triangle.GetPointIds().SetId(2, 2)

    triangle2 = vtk.vtkTriangle()
    triangle2.GetPointIds().SetId(0, 2)
    triangle2.GetPointIds().SetId(1,3)
    triangle2.GetPointIds().SetId(2, 0)

    triangles = vtk.vtkCellArray()
    triangles.InsertNextCell(triangle)
    triangles.InsertNextCell(triangle2)

    colors = vtk.vtkUnsignedCharArray()
    colors.SetNumberOfComponents(3)
    colors.SetName("Colors")
    colors.InsertNextTuple3(255, 0, 0)
    colors.InsertNextTuple3(0, 255, 0)
    colors.InsertNextTuple3(0, 0, 255)
    colors.InsertNextTuple3(0, 255, 0)

    trianglePolyData = vtk.vtkPolyData()
    trianglePolyData.SetPoints(points)
    trianglePolyData.SetPolys(triangles)
    trianglePolyData.GetPointData().SetScalars(colors)

    return build_actor(trianglePolyData, True)

def createPlaneActorCircle():
    cylinder = vtk.vtkCylinderSource()
    cylinder.SetResolution(50)
    cylinder.SetRadius(params.PlaneDiameter/2)
    cylinder.SetHeight(0.1)
    cylinder.SetCenter(0,0,-0.1)
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(cylinder.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(params.PlaneColor)
    actor.RotateX(90)
    return actor



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


def createStlActorInOrigin(filename):
    actor, reader  = createStlActor(filename)
    origin = findStlOrigin(reader.GetOutput())
    transform = vtk.vtkTransform()
    transform.Translate(-origin[0], -origin[1], -origin[2])
    actor.SetUserTransform(transform)
    return actor, origin


def makeBlocks(layers):
    blocks = []
    for layer in layers:
        points = vtk.vtkPoints()
        lines = vtk.vtkCellArray()
        block = vtk.vtkPolyData()
        points_count = 0
        for path in layer:
            line = vtk.vtkLine()
            for k in range(len(path) - 1):
                points.InsertNextPoint(path[k])
                line.GetPointIds().SetId(0, points_count + k)
                line.GetPointIds().SetId(1, points_count + k + 1)
                lines.InsertNextCell(line)
            points.InsertNextPoint(path[-1])  # not forget to add last point
            points_count += len(path)
        block.SetPoints(points)
        block.SetLines(lines)
        blocks.append(block)
    return blocks


def wrapWithActors(blocks, rotations, lays2rots):
    actors = []
    for i in range(len(blocks)):
        block = blocks[i]
        actor = build_actor(block, True)
        transform = vtk.vtkTransform()
        # rotate to abs coords firstly and then apply last rotation
        transform.PostMultiply()
        transform.RotateX(-rotations[lays2rots[i]].x_rot)
        transform.PostMultiply()
        transform.RotateZ(-rotations[lays2rots[i]].z_rot)

        transform.PostMultiply()
        transform.RotateZ(rotations[-1].z_rot)
        transform.PostMultiply()
        transform.RotateX(rotations[-1].x_rot)
        actor.SetUserTransform(transform)

        actor.GetProperty().SetColor(params.LayerColor)
        actors.append(actor)

    actors[-1].GetProperty().SetColor(params.LastLayerColor)
    return actors

def build_actor(source, as_is = False):
    mapper = vtk.vtkPolyDataMapper()
    if as_is:
        mapper.SetInputData(source)
    else:
        mapper.SetInputData(source.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor