import os
import sys
import vtk

from substrate_plane import *

class STL_Operations :
    def __init__(self) :
        self.image_actor = vtk.vtkActor()
        self.substrate_center = []
        self.plane_info = Plane()

    def loadSTLImage(self, filename) :
        # Create source
        reader = vtk.vtkSTLReader()
        reader.SetFileName(filename)
        reader.Update()                          

        # Create a mapper
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        # Create an actor     
        self.image_actor.SetMapper(mapper)

        # Find figure and substrate center
        self.plane_info.findFigureProfile(reader.GetOutput(), reader.GetOutput().IsA("vtkPolyData"))
        self.substrate_center = self.plane_info.planeCenter





#if __name__ == '__main__':
#   f_io=GCode()
#   f_io.SetFileName("with_rotation.gcode")
#   f_io.readGCode()
