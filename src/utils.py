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
    center = params.PlaneCenter
    planeSource.SetOrigin(center[0] - xsize / 2, center[1] - ysize / 2, center[2] - 0.1)
    planeSource.SetPoint1(center[0] + xsize / 2, center[1] - ysize / 2, center[2] - 0.1)
    planeSource.SetPoint2(center[0] - xsize / 2, center[1] + ysize / 2, center[2] - 0.1)
    planeSource.Update()
    planeActor = build_actor(planeSource)
    planeActor.GetProperty().SetColor(params.PlaneColor)
    return planeActor


def createPlaneActor2():
    xsize = params.PlaneXSize
    ysize = params.PlaneYSize
    center = params.PlaneCenter

    points = vtk.vtkPoints()
    points.InsertNextPoint((center[0] - xsize / 2, center[1] - ysize / 2, center[2] - 0.1))
    points.InsertNextPoint((center[0] + xsize / 2, center[1] - ysize / 2, center[2] - 0.1))
    points.InsertNextPoint((center[0] + xsize / 2, center[1] + ysize / 2, center[2] - 0.1))
    points.InsertNextPoint((center[0] - xsize / 2, center[1] + ysize / 2, center[2] - 0.1))

    triangle = vtk.vtkTriangle()
    triangle.GetPointIds().SetId(0, 0)
    triangle.GetPointIds().SetId(1, 1)
    triangle.GetPointIds().SetId(2, 2)

    triangle2 = vtk.vtkTriangle()
    triangle2.GetPointIds().SetId(0, 2)
    triangle2.GetPointIds().SetId(1, 3)
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
    cylinder.SetRadius(params.PlaneDiameter / 2)
    cylinder.SetHeight(0.1)
    cylinder.SetCenter(params.PlaneCenter[0], params.PlaneCenter[2] - 0.1, params.PlaneCenter[1])  # WHAT? vtk :(
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


def createStlActorInOriginWithColorize(filename):
    # actor, reader = createStlActor(filename)
    # output = reader.GetOutput()
    # actor = colorizeSTL(output)
    # origin = findStlOrigin(output)
    # print(origin)
    # return actor, (0,0,0)
    return createStlActorInOrigin(filename , colorize=True)


def createStlActorInOrigin(filename, colorize=False):
    actor, reader = createStlActor(filename)
    output = reader.GetOutput()

    if colorize:
        print("yes")
        actor = colorizeSTL(output)

    origin = findStlOrigin(output)
    transform = vtk.vtkTransform()
    c = params.PlaneCenter
    transform.Translate(-origin[0] + c[0], -origin[1] + c[1], -origin[2] + c[2])
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


def colorizeSTL(output):
    polys = output.GetPolys()
    allpoints = output.GetPoints()

    size = polys.GetSize()
    triangles = vtk.vtkCellArray()
    triangles2 = vtk.vtkCellArray()
    points = vtk.vtkPoints()
    points2 = vtk.vtkPoints()

    tocolor = []
    with open(params.InColorFile, "rb") as f:
        content = f.read()
        for b in content:
            if b==1:
                tocolor.append(True)
            else:
                tocolor.append(False)

    a, b = 0, 0
    for i in range(size):  # TODO: refactor me
        idList = vtk.vtkIdList()
        polys.GetNextCell(idList)
        num = idList.GetNumberOfIds()
        if num != 3:
            break

        id0 = idList.GetId(0)
        id1 = idList.GetId(1)
        id2 = idList.GetId(2)

        p0 = allpoints.GetPoint(id0)
        p1 = allpoints.GetPoint(id1)
        p2 = allpoints.GetPoint(id2)

        if tocolor[i]:
            triangle = vtk.vtkTriangle()
            triangle.GetPointIds().SetId(0, a)
            triangle.GetPointIds().SetId(1, a + 1)
            triangle.GetPointIds().SetId(2, a + 2)
            triangles.InsertNextCell(triangle)

            points.InsertNextPoint(p0)
            points.InsertNextPoint(p1)
            points.InsertNextPoint(p2)

            a += 3

        else:
            triangle = vtk.vtkTriangle()
            triangle.GetPointIds().SetId(0, b)
            triangle.GetPointIds().SetId(1, b + 1)
            triangle.GetPointIds().SetId(2, b + 2)
            triangles2.InsertNextCell(triangle)

            points2.InsertNextPoint(p0)
            points2.InsertNextPoint(p1)
            points2.InsertNextPoint(p2)

            b += 3

    trianglePolyData = vtk.vtkPolyData()
    trianglePolyData.SetPoints(points)
    trianglePolyData.SetPolys(triangles)
    trianglePolyData2 = vtk.vtkPolyData()
    trianglePolyData2.SetPoints(points2)
    trianglePolyData2.SetPolys(triangles2)

    actor = build_actor(trianglePolyData, True)
    actor.GetProperty().SetColor(0.86, 0.08, 0.04)
    actor2 = build_actor(trianglePolyData2, True)
    #actor2.GetProperty().SetColor(0.86, 0.78, 0.24)

    assembly = vtk.vtkAssembly()
    assembly.AddPart(actor)
    assembly.AddPart(actor2)

    return assembly


def build_actor(source, as_is=False):
    mapper = vtk.vtkPolyDataMapper()
    if as_is:
        mapper.SetInputData(source)
    else:
        mapper.SetInputData(source.GetOutput())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor
