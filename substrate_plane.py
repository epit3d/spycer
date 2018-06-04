import os
import sys
import vtk


class Plane:
    def __init__(self):
        # points for plane
        self.figureCenter = []
        self.planeCenter = []
        self.x_mid = 0
        self.y_mid = 0
        self.z_mid = 0
        self.z_min = 0
        self.z_max = 0
        self.x_min = 0
        self.x_max = 0
        self.y_min = 0
        self.y_max = 0
        # plane actor
        self.planeActor = vtk.vtkActor()

    def findFigureProfile(self, obj_data, isSingleBlock):
        # Find points for substrate plane
        self.x_mid = 0
        self.y_mid = 0
        self.z_mid = 0
        self.x_min = 1e10
        self.y_min = 1e10
        self.z_min = 1e10
        self.x_max = 0
        self.y_max = 0
        self.z_max = 0
        n_blocks = 1  # difference between vtkPolyData and vtkMultiBlockDataSet
        if not isSingleBlock:
            n_blocks = obj_data.GetNumberOfBlocks()
        # Figure's min and max coordinates
        for k in range(n_blocks):
            block = vtk.vtkPolyData()
            if not isSingleBlock:
                block = obj_data.GetBlock(k)
            else:
                block = obj_data
            bound = [0, 0, 0, 0, 0, 0]
            block.GetBounds(bound)
            self.x_min = min(bound[0], self.x_min)
            self.y_min = min(bound[2], self.y_min)
            self.z_min = min(bound[4], self.z_min)
            self.x_max = max(bound[1], self.x_max)
            self.y_max = max(bound[3], self.y_max)
            self.z_max = max(bound[5], self.z_max)
        # Fugure's center
        self.x_mid = (self.x_min + self.x_max) / 2
        self.y_mid = (self.y_min + self.y_max) / 2
        self.z_mid = (self.z_min + self.z_max) / 2
        self.figureCenter = [self.x_mid, self.y_mid, self.z_mid]
        self.planeCenter = [self.x_mid, self.y_mid, self.z_min - 0.1]

    def createPlane(self):
        # Create a plane
        planeSource = vtk.vtkPlaneSource()
        # small indent from object plane, render problems, 200x200 substrate
        planeSource.SetOrigin(self.x_mid - 100, self.y_mid - 100, self.z_min - 0.1)
        planeSource.SetPoint1(self.x_mid + 100, self.y_mid - 100, self.z_min - 0.1)
        planeSource.SetPoint2(self.x_mid - 100, self.y_mid + 100, self.z_min - 0.1)

        planeSource.Update()

        plane = planeSource.GetOutput()

        # Create a mapper and actor
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(plane)

        colors = vtk.vtkNamedColors()
        self.planeActor.SetMapper(mapper)
        self.planeActor.GetProperty().SetColor(colors.GetColor3d("Cyan"))

    def rotatePlane(self, rotations):
        transform = vtk.vtkTransform()
        #transform.Translate(-self.planeCenter[0], -self.planeCenter[1], -self.planeCenter[2])
        for r in rotations:
            if r.isX:
                transform.PostMultiply()
                transform.RotateX(r.x_rot)
            else:
                transform.PostMultiply()
                transform.RotateZ(r.z_rot)
        self.planeActor.SetUserTransform(transform)
