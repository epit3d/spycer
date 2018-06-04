import vtk

class Line:
    def __init__(self, p1, p2):
        self.p1 = p1
        self.p2 = p2

    def draw(self):
        pts = vtk.vtkPoints()
        pts.InsertNextPoint(self.p1)
        pts.InsertNextPoint(self.p2)

        line = vtk.vtkLine()
        line.GetPointIds().SetId(0, 0)
        line.GetPointIds().SetId(1, 1)

        lines = vtk.vtkCellArray()
        lines.InsertNextCell(line)

        linePolyData = vtk.vtkPolyData()
        linePolyData.SetPoints(pts)
        linePolyData.SetLines(lines)
        return linePolyData

class Triangle:
    def __init__(self, p1, p2, p3):
        self.p1 = p1
        self.p2 = p2
        self.p3 = p3

    def draw(self):
        points = vtk.vtkPoints()
        points.InsertNextPoint(self.p1)
        points.InsertNextPoint(self.p2)
        points.InsertNextPoint(self.p3)

        triangle = vtk.vtkTriangle()
        triangle.GetPointIds().SetId(0, 0)
        triangle.GetPointIds().SetId(1, 1)
        triangle.GetPointIds().SetId(2, 2)

        triangles = vtk.vtkCellArray()
        triangles.InsertNextCell(triangle)

        trianglePolyData = vtk.vtkPolyData()
        trianglePolyData.SetPoints( points )
        trianglePolyData.SetPolys( triangles )
        return trianglePolyData

class Debug:
    def __init__(self, objs):
        self.objs = objs
        self.actorList = []

    def drawObjs(self, color, size):
        colors = vtk.vtkNamedColors()
        vtkColor = colors.GetColor3d(color)
        for obj in self.objs:
            block = obj.draw()

            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(block)
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(vtkColor)
            actor.GetProperty().SetLineWidth(size)
            self.actorList.append(actor)

