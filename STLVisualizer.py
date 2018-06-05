# -*- coding: utf-8 -*-

import subprocess
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QTextEdit, QGridLayout, QSlider, QCheckBox, QPushButton,
                             QApplication, QFileDialog)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from gcode_reader import *
from debug import *
from stl_operations import *

debugFlag = True


class Ui_MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        self.setupUi()

    def setupUi(self):
        # Labels

        self.nozzleDiam_label = QLabel('Диаметр сопла, мм:')
        self.layerWidth_label = QLabel('Толщина слоя, мм:')
        self.movementVel_label = QLabel('Скорость движения, мм/с:')
        self.printTemp_label = QLabel(
            "<html><head/><body><p>Температура печати, <span style=\" vertical-align:super;\">о</span>С:</p></body></html>")
        self.fillDensity_label = QLabel('Плотность заполнения, %:')
        self.lineWidth_label = QLabel('Толщина линии: ')
        self.slider_label = QLabel('Отображаемые слои: ')
        self.layersNumber_label = QLabel()

        # LineEdits

        self.nozzleDiam_value = QLineEdit("2")
        self.layerWidth_value = QLineEdit("0.2")
        self.movementVel_value = QLineEdit("1")
        self.printTemp_value = QLineEdit("100")
        self.fillDensity_value = QLineEdit("100")
        self.lineWidth_value = QLineEdit("1")

        # Widgets

        self.vtkWidget = QVTKRenderWindowInteractor()
        self.pictureSlider = QSlider()
        self.pictureSlider.setOrientation(QtCore.Qt.Horizontal)
        self.modelSwitch_box = QCheckBox('Отображение STL модели')
        self.loadModel_button = QPushButton('Загрузка модели')
        self.slice_button = QPushButton('Slice!')
        self.saveGCode_button = QPushButton('Сохранить GCode...')
        self.debug_button = QPushButton('Open debug model')

        # Prepare layout grid
        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setColumnStretch(0, 2)
        # Place widgets
        grid.addWidget(self.vtkWidget, 1, 0, 20, 1)
        grid.addWidget(self.nozzleDiam_label, 2, 1)
        grid.addWidget(self.nozzleDiam_value, 2, 2)
        grid.addWidget(self.layerWidth_label, 3, 1)
        grid.addWidget(self.layerWidth_value, 3, 2)
        grid.addWidget(self.movementVel_label, 4, 1)
        grid.addWidget(self.movementVel_value, 4, 2)
        grid.addWidget(self.printTemp_label, 5, 1)
        grid.addWidget(self.printTemp_value, 5, 2)
        grid.addWidget(self.fillDensity_label, 6, 1)
        grid.addWidget(self.fillDensity_value, 6, 2)

        grid.addWidget(self.modelSwitch_box, 8, 1)
        self.modelSwitch_box.setEnabled(False)

        grid.addWidget(self.slider_label, 10, 1)
        self.slider_label.setEnabled(False)
        grid.addWidget(self.layersNumber_label, 10, 2)
        self.layersNumber_label.setEnabled(False)
        grid.addWidget(self.pictureSlider, 11, 1, 1, 2)
        self.pictureSlider.setEnabled(False)

        grid.addWidget(self.lineWidth_label, 13, 1)
        self.lineWidth_label.setEnabled(False)
        grid.addWidget(self.lineWidth_value, 13, 2)
        self.lineWidth_value.setEnabled(False)

        grid.addWidget(self.loadModel_button, 15, 1, 1, 2)
        grid.addWidget(self.slice_button, 16, 1, 1, 2)
        grid.addWidget(self.saveGCode_button, 17, 1, 1, 2)
        if debugFlag:
            grid.addWidget(self.debug_button, 18, 1, 1, 2)

        # Add layouts grid to the main window

        self.setLayout(grid)

        self.setWindowTitle('Spycer')
        self.resize(994, 707)
        # VTK window initialization
        self.vtkWidget.Initialize()
        self.vtkWidget.Start()


class vtkView():
    def __init__(self, parent=None):
        colors = vtk.vtkNamedColors()
        self.ui = Ui_MainWindow()
        self.ui.loadModel_button.clicked.connect(self.openFile)
        self.ui.slice_button.clicked.connect(self.sliceSTL)
        self.ui.saveGCode_button.clicked.connect(self.saveGCodeFile)
        self.ui.debug_button.clicked.connect(self.debugModel)
        self.ui.modelSwitch_box.stateChanged.connect(self.switchModels)
        # Initialize renderer and render widget
        self.ren = vtk.vtkRenderer()
        self.ren.SetBackground(colors.GetColor3d("SlateGray"))
        self.ui.vtkWidget.GetRenderWindow().AddRenderer(self.ren)
        self.iren = self.ui.vtkWidget.GetRenderWindow().GetInteractor()
        self.iren.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        # Create axis widget
        axes = vtk.vtkAxesActor()

        self.axeswidget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        colors.GetColor("Carrot", rgba)
        self.axeswidget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        self.axeswidget.SetOrientationMarker(axes)
        self.axeswidget.SetInteractor(self.iren)
        self.axeswidget.SetViewport(0.0, 0.0, 0.3, 0.3)
        self.axeswidget.SetEnabled(1)
        self.axeswidget.InteractiveOff()

        # classes
        self.stl_io = STL_Operations()
        self.gcode_io = GCode()

        # rotation layers list
        self.rot_info = []
        # plane actor
        self.planeActor = vtk.vtkActor()
        # STL model actor
        self.stlActor = vtk.vtkActor()
        # GCode actor list
        self.actorList = []
        # default color
        self.layerColor = [0, 0, 0]
        # default output GCode filename
        self.output_gcode = "out.gcode"

    def loadGCode(self):

        self.gcode_io.SetFileName(self.filename)
        self.gcode_io.loadGCodeImage()

        self.actorList = self.gcode_io.actorList

        for i in range(self.gcode_io.fullLayerNumber):
            self.ren.AddActor(self.actorList[i])

        # Create substrate plane
        self.gcode_io.plane_info.createPlane()  # TODO: fix len
        self.gcode_io.plane_info.rotatePlane(self.gcode_io.rotation_info[len(self.gcode_io.rotation_info) - 1])
        self.planeActor = self.gcode_io.plane_info.planeActor
        self.ren.AddActor(self.planeActor)
        # Reset camera
        self.ren.ResetCamera()
        # Enable and setup slider and line width settings
        if not self.ui.pictureSlider.isEnabled():
            self.ui.pictureSlider.setEnabled(True)
            self.ui.slider_label.setEnabled(True)
            self.ui.lineWidth_label.setEnabled(True)
            self.ui.lineWidth_value.setEnabled(True)
            self.ui.layersNumber_label.setEnabled(True)
        self.ui.pictureSlider.setMinimum(1)
        self.ui.pictureSlider.setMaximum(self.gcode_io.fullLayerNumber)
        self.ui.pictureSlider.setValue(1)
        self.ui.pictureSlider.setSliderPosition(self.gcode_io.fullLayerNumber)
        self.ui.layersNumber_label.setText(str(self.gcode_io.fullLayerNumber))
        self.ui.lineWidth_value.setText("1")
        # Disable switching if gcode is loaded without slicing
        if self.ui.modelSwitch_box.isEnabled():
            self.ui.modelSwitch_box.setEnabled(False)
            self.ui.modelSwitch_box.setChecked(False)
        # Connect slider and line width with layer visualization
        self.ui.pictureSlider.valueChanged.connect(self.changeLayerView)
        self.ui.lineWidth_value.textChanged.connect(self.changeLineWidth)
        for r in self.gcode_io.rotation_info:
            print("x=" + str(r.x_rot), str(r.z_rot))

    def loadSTL(self):
        # Create source
        self.stl_io.loadSTLImage(self.filename)
        self.stlActor = self.stl_io.image_actor

        self.ren.AddActor(self.stlActor)
        # Create substrate plane
        self.stl_io.plane_info.createPlane()
        self.stl_io.plane_info.rotatePlane(Rotations())
        # Save actor
        self.planeActor = self.stl_io.plane_info.planeActor
        self.ren.AddActor(self.planeActor)
        # Reset camera
        self.ren.ResetCamera()

        # Disable slider instruments
        if self.ui.pictureSlider.isEnabled():
            self.ui.pictureSlider.setEnabled(False)
            self.ui.slider_label.setEnabled(False)
            self.ui.layersNumber_label.setEnabled(False)
            self.ui.layersNumber_label.setText(" ")
            self.ui.lineWidth_label.setEnabled(False)
            self.ui.lineWidth_value.setEnabled(False)
            self.ui.modelSwitch_box.setEnabled(False)
            self.ui.modelSwitch_box.setChecked(False)

    def openFile(self):
        try:
            self.filename = str(QFileDialog.getOpenFileName(None, "Open STL file", "/home")[0])
            if len(self.filename) > 0:
                self.ren.RemoveAllViewProps()
                file_ext = os.path.splitext(self.filename)[1]
                if "stl" in file_ext or "STL" in file_ext:
                    self.stlFileName = self.filename
                    if len(self.gcode_io.all_rotations) > 0:
                        self.gcode_io.all_rotations.clear()
                    self.loadSTL()
                    self.iren.Render()
                elif "gcode" in file_ext:
                    self.loadGCode()
                    self.iren.Render()
                    self.stlFileName = ""
                else:
                    print("This file format isn't supported!")
        except IOError:
            print("Error during file opening")

    def debugModel(self):
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

    def saveGCodeFile(self):
        try:
            name = str(QFileDialog.getSaveFileName(None, 'Save GCode File')[0])
            os.rename(self.output_gcode, name)
        except IOError:
            print("Error during file saving")

    def sliceSTL(self):
        if hasattr(self, "stlFileName") and len(self.stlFileName) > 0:
            layerWidth = self.ui.layerWidth_value.text()
            if len(layerWidth) == 0:
                layerWidth = "0.2"
            command_line = ['./goosli', '--stl=' + self.stlFileName, '--gcode=' + self.output_gcode,
                            '--thickness=' + layerWidth,
                            '--originx=' + str(self.stl_io.substrate_center[0]),
                            '--originy=' + str(self.stl_io.substrate_center[1]),
                            '--originz=' + str(self.stl_io.substrate_center[2])]
            subprocess.check_output(command_line)
            self.filename = self.output_gcode
            self.ren.RemoveAllViewProps()
            self.loadGCode()
            # Last actor in the list belongs to STL model
            transform = vtk.vtkTransform()
            transform.Translate(-self.gcode_io.substrate_center[0], -self.gcode_io.substrate_center[1],
                                -self.gcode_io.substrate_center[2])
            for j in range(len(self.gcode_io.rotation_info)):
                if self.gcode_io.rotation_info[j].isX:
                    transform.PostMultiply()
                    transform.RotateX(self.gcode_io.rotation_info[j].x_rot)
                else:
                    transform.PostMultiply()
                    transform.RotateZ(self.gcode_io.rotation_info[j].z_rot)

            self.stlActor.SetUserTransform(transform)
            self.actorList.append(self.stlActor)
            self.ren.AddActor(self.stlActor)
            self.stlActor.VisibilityOff()
            self.ren.Modified()
            self.iren.Render()
            # Enable model switching
            self.ui.modelSwitch_box.setEnabled(True)
            self.ui.modelSwitch_box.setChecked(False)
        else:
            print("Wrong file to slice!")

    def changeLayerView(self):
        colors = vtk.vtkNamedColors()
        newSliderValue = self.ui.pictureSlider.value()
        self.actorList[newSliderValue - 1].GetProperty().SetColor(colors.GetColor3d("Red"))
        self.actorList[self.gcode_io.currLayerNumber - 1].GetProperty().SetColor(self.gcode_io.layerColor)
        self.ui.layersNumber_label.setText(str(newSliderValue))
        if newSliderValue < self.gcode_io.currLayerNumber:
            for layer in range(newSliderValue, self.gcode_io.currLayerNumber):
                self.actorList[layer].VisibilityOff()
        else:
            for layer in range(self.gcode_io.currLayerNumber, newSliderValue):
                self.actorList[layer].VisibilityOn()
        if self.gcode_io.all_rotations[newSliderValue - 1] != self.gcode_io.all_rotations[
                    self.gcode_io.currLayerNumber - 1]:
            for block in range(newSliderValue):
                transform = vtk.vtkTransform()
                # transform.Translate(-self.gcode_io.substrate_center[0], -self.gcode_io.substrate_center[1],
                #                  -self.gcode_io.substrate_center[2])
                transform.PostMultiply()
                transform.RotateZ(self.gcode_io.rotation_info[self.gcode_io.all_rotations[block]].z_rot)
                transform.PostMultiply()
                transform.RotateX(self.gcode_io.rotation_info[self.gcode_io.all_rotations[block]].x_rot)

                transform.PostMultiply()
                transform.RotateX(-self.gcode_io.rotation_info[self.gcode_io.all_rotations[newSliderValue - 1]].x_rot)
                transform.PostMultiply()
                transform.RotateZ(-self.gcode_io.rotation_info[self.gcode_io.all_rotations[newSliderValue - 1]].z_rot)
                self.actorList[block].SetUserTransform(transform)
                if block == 0:
                    tr = vtk.vtkTransform()
                    tr.PostMultiply()
                    tr.RotateX(
                        -self.gcode_io.rotation_info[self.gcode_io.all_rotations[newSliderValue - 1]].x_rot)
                    tr.PostMultiply()
                    tr.RotateZ(
                        -self.gcode_io.rotation_info[self.gcode_io.all_rotations[newSliderValue - 1]].z_rot)
                    self.planeActor.SetUserTransform(tr)
                    self.stlActor.SetUserTransform(tr)
        self.gcode_io.currLayerNumber = newSliderValue
        self.ren.Modified()
        self.iren.Render()

    def changeLineWidth(self):
        if len(self.ui.lineWidth_value.text()) > 0:
            for layer in range(self.gcode_io.fullLayerNumber):
                self.actorList[layer].GetProperty().SetLineWidth(float(self.ui.lineWidth_value.text()))
            self.ren.Modified()
            self.iren.Render()

    def switchModels(self, state):
        if state == QtCore.Qt.Checked:
            for i in range(self.gcode_io.currLayerNumber):
                self.actorList[i].VisibilityOff()
            self.actorList[len(self.actorList) - 1].VisibilityOn()
        else:
            for i in range(self.gcode_io.currLayerNumber):
                self.actorList[i].VisibilityOn()
            self.actorList[len(self.actorList) - 1].VisibilityOff()
        self.ren.Modified()
        self.iren.Render()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = vtkView()
    window.ui.show()
    window.filename = "/home/l1va/out_home.gcode"
    window.loadGCode()
    window.iren.Render()
    window.stlFileName = ""
    sys.exit(app.exec_())
