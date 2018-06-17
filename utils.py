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
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(planeSource.GetOutput())
    planeActor = vtk.vtkActor()
    planeActor.SetMapper(mapper)
    planeActor.GetProperty().SetColor(params.PlaneColor)
    return planeActor


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
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    return actor


def createStlActorInOrigin(filename):
    reader = vtk.vtkSTLReader()
    reader.SetFileName(filename)
    reader.Update()
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputConnection(reader.GetOutputPort())
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
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
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(block)
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)
        transform = vtk.vtkTransform()
        # rotate to abs coords firstly and then apply last rotation
        transform.PostMultiply()
        transform.RotateZ(-rotations[lays2rots[i]].z_rot)
        transform.PostMultiply()
        transform.RotateX(-rotations[lays2rots[i]].x_rot)

        transform.PostMultiply()
        transform.RotateX(rotations[-1].x_rot)
        transform.PostMultiply()
        transform.RotateZ(rotations[-1].z_rot)
        actor.SetUserTransform(transform)

        actor.GetProperty().SetColor(params.LayerColor)
        actors.append(actor)

    actors[-1].GetProperty().SetColor(params.LastLayerColor)
    return actors
