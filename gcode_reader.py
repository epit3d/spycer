import os
import sys
import vtk

from substrate_plane import *


class Rotations:
    def __init__(self):
        self.n_layers = 0  # number of layers to rotate
        self.x_rot = 0  # x angle rotation
        self.z_rot = 0  # z angle rotation
        self.isX = True


class GCode:
    def __init__(self):
        self.full_data = []  # data recieved from file
        self.n_layers = 0  # number of layers in the structure (for checking cases)
        self.filename = ""  # GCode file name
        self.rotation_info = []  # information about layers needed to rotate and rotation angles
        self.all_rotations = []  # full info about rotation of every layer
        self.currLayerNumber = 0  # number of layers to visualize
        self.fullLayerNumber = 0  # full layers number in the structure
        self.actorList = []  # list of actors, actor per layer
        self.layerColor = vtk.vtkNamedColors()  # default color for layer
        self.substrate_center = []  # substrate center
        self.plane_info = Plane()

    def SetFileName(self, file_name):
        if not os.path.isfile(file_name):
            file_name = None
        self.filename = file_name

    def readGCode(self):
        try:
            inFile = open(self.filename, 'r')
        except IOError:
            print("====IO exception====")
            print("Cannot open gcode file")

        lines = []
        single_line = []
        self.full_data.clear()
        self.rotation_info = []
        self.all_rotations.clear()

        for line in inFile:
            data_array = line.split()
            coords = []
            if line.startswith('G') and self.n_layers > 0:
                if "G0" in data_array[0] and len(single_line) > 0:
                    lines.append(single_line)
                    single_line = []
                if "G1" in data_array[0]:
                    coords = [0, 0, 0]
                    x = 0
                    y = 0
                    z = 0
                    for i in range(len(data_array)):
                        if data_array[i].startswith('X'):
                            coords[0] = float(data_array[i][1:])
                        elif data_array[i].startswith('Y'):
                            coords[1] = float(data_array[i][1:])
                        elif data_array[i].startswith('Z'):
                            coords[2] = float(data_array[i][1:])
                        else:
                            continue
                    single_line.append(coords)
                curr_rot = Rotations()
                curr_rot.n_layers = len(self.full_data) + 1  # TODO: fix me
                if "G42" in data_array[0]:
                    curr_rot.x_rot = -float(data_array[1])
                if "G52" in data_array[0]:
                    curr_rot.z_rot = -float(data_array[1])
                    curr_rot.isX = False
                if curr_rot.x_rot != 0 or curr_rot.z_rot != 0:
                    self.rotation_info.append(curr_rot)

            if ((line.startswith(';Layer') or line.startswith(';LAYER')) and len(data_array) == 1):
                self.n_layers += 1
                if len(single_line) > 0:
                    lines.append(single_line)
                    single_line = []
                if len(lines) > 0:
                    self.full_data.append(lines)
                    lines = []

        if len(single_line) > 0:
            lines.append(single_line)
            single_line = []
            self.full_data.append(lines)
            single_line = []

        inFile.close()
        # print(self.n_layers)
        # print(len(self.full_data))
        # print(len(self.rotation_info))
        return self.collectVTKData()

    def collectVTKData(self):

        structure = vtk.vtkMultiBlockDataSet()
        for i in range(len(self.full_data)):  # each layer
            points = vtk.vtkPoints()
            block = vtk.vtkPolyData()
            lines = vtk.vtkCellArray()
            points_ids_temp = 0
            for j in range(len(self.full_data[i])):  # each line in the layer
                line = vtk.vtkLine()
                for k in range(len(self.full_data[i][j])):  # each point of the single line
                    points.InsertNextPoint(self.full_data[i][j][k])
                    if k == len(self.full_data[i][j]) - 1:
                        continue
                    line.GetPointIds().SetId(0, points_ids_temp + k)
                    line.GetPointIds().SetId(1, points_ids_temp + k + 1)
                    lines.InsertNextCell(line)
                points_ids_temp = points_ids_temp + len(self.full_data[i][j])
            block.SetPoints(points)
            block.SetLines(lines)
            structure.SetBlock(i, block)
        # collect rotations for all blocks
        r = Rotations()
        r.n_layers = structure.GetNumberOfBlocks()
        self.rotation_info.append(r)  # stub for last segment
        self.all_rotations = [0] * structure.GetNumberOfBlocks()
        cur = 0
        for i in range(len(self.rotation_info)):
            for block in range(cur, self.rotation_info[i].n_layers):
                self.all_rotations[block] = i
            cur = self.rotation_info[i].n_layers
        return structure

    def loadGCodeImage(self):
        # Create source
        source = vtk.vtkMultiBlockDataSet()
        if len(self.actorList) > 0:
            self.actorList.clear()

        source = self.readGCode()

        self.currLayerNumber = source.GetNumberOfBlocks()
        self.fullLayerNumber = source.GetNumberOfBlocks()

        # Find figure and substrate center
        self.plane_info.findFigureProfile(source, source.IsA("vtkPolyData"))
        self.substrate_center = self.plane_info.planeCenter

        # color for layer
        colors = vtk.vtkNamedColors()

        for i in range(self.fullLayerNumber):
            # Create a mapper
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(source.GetBlock(i))
            # Create an actor for every block
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            transform = vtk.vtkTransform()
            transform.Translate(-self.substrate_center[0], -self.substrate_center[1], -self.substrate_center[2])
            for j in range(self.all_rotations[i], len(self.rotation_info) - 1):
                if self.rotation_info[j].isX:
                    transform.PostMultiply()
                    transform.RotateX(self.rotation_info[j].x_rot)
                else:
                    transform.PostMultiply()
                    transform.RotateZ(self.rotation_info[j].z_rot)

            actor.SetUserTransform(transform)
            # get default layer color
            if i == 0:
                self.layerColor = actor.GetProperty().GetColor()
            # set the last layer color as Red
            if i == self.fullLayerNumber - 1:
                actor.GetProperty().SetColor(colors.GetColor3d("Red"))
            self.actorList.append(actor)

# if __name__ == '__main__':
#   f_io=GCode()
#   f_io.SetFileName("with_rotation.gcode")
#   f_io.readGCode()
