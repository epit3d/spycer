import vtk


def drawLine(p1, p2):
    pts = vtk.vtkPoints()
    pts.InsertNextPoint(p1)
    pts.InsertNextPoint(p2)

    line = vtk.vtkLine()
    line.GetPointIds().SetId(0, 0)
    line.GetPointIds().SetId(1, 1)

    lines = vtk.vtkCellArray()
    lines.InsertNextCell(line)

    linePolyData = vtk.vtkPolyData()
    linePolyData.SetPoints(pts)
    linePolyData.SetLines(lines)
    return linePolyData


def drawTriangle(p1, p2, p3):
    points = vtk.vtkPoints()
    points.InsertNextPoint(p1)
    points.InsertNextPoint(p2)
    points.InsertNextPoint(p3)

    triangle = vtk.vtkTriangle()
    triangle.GetPointIds().SetId(0, 0)
    triangle.GetPointIds().SetId(1, 1)
    triangle.GetPointIds().SetId(2, 2)

    triangles = vtk.vtkCellArray()
    triangles.InsertNextCell(triangle)

    trianglePolyData = vtk.vtkPolyData()
    trianglePolyData.SetPoints(points)
    trianglePolyData.SetPolys(triangles)
    return trianglePolyData


def makeActor(block, vtkColor, size):
    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(block)
    actor = vtk.vtkActor()
    actor.SetMapper(mapper)
    actor.GetProperty().SetColor(vtkColor)
    actor.GetProperty().SetLineWidth(size)
    return actor


def readFile(render, file, color, size):
    with open(file) as f:
        content = f.readlines()
    vtkColor = vtk.vtkNamedColors().GetColor3d(color)

    for line in content:
        vals = line.strip().split(" ")
        if vals[0] == "line":
            block = drawLine(toPoint(vals[1:4]), toPoint(vals[4:7]))
        else:  # vals[0] == "triangle"
            block = drawTriangle(toPoint(vals[1:4]), toPoint(vals[4:7]), toPoint(vals[7:10]))
        render.AddActor(makeActor(block, vtkColor, size))


def toPoint(vs):
    return [float(x) for x in vs]
