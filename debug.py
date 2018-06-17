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

    def debugModel(self): #TODO: refactor me
        self.readDebugFile("/home/l1va/debug.txt", "Green", 4)
        self.readDebugFile("/home/l1va/debug_simplified.txt", "Red", 3)

        self.ren.ResetCamera()
        self.ren.Modified()
        self.iren.Render()
        print("done")

    def readDebugFile(self, file, color, size):
        with open(file) as f:
            content = f.readlines()
        objs = []

        def toPoint(vs):
            return [float(x) for x in vs]

        for line in content:
            vals = line.strip().split(" ")
            if vals[0] == "line":
                objs.append(Line(toPoint(vals[1:4]), toPoint(vals[4:7])))
            elif vals[0] == "triangle":
                objs.append(Triangle(toPoint(vals[1:4]), toPoint(vals[4:7]), toPoint(vals[7:10])))
        d = Debug(objs)
        d.drawObjs(color, size)
        for a in d.actorList:
            self.ren.AddActor(a)