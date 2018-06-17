import os
import subprocess
import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QGridLayout, QSlider, QCheckBox, QPushButton, QFileDialog)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from shutil import copy2
import gcode
import locales
import params
import utils

NothingState = "nothing"
GCodeState = "gcode"
StlState = "stl"
BothState = "both"


class Gui(QWidget):
    def prepareWidgets(self):
        self.setWindowTitle('Spycer')
        self.resize(994, 707)  # TODO: full window

        grid = QGridLayout()
        grid.setSpacing(5)
        grid.setColumnStretch(0, 2)

        widget3d = QVTKRenderWindowInteractor()
        widget3d.Initialize()
        widget3d.Start()
        self.render = vtk.vtkRenderer()
        self.render.SetBackground(params.BackgroundColor)
        widget3d.GetRenderWindow().AddRenderer(self.render)
        self.interactor = widget3d.GetRenderWindow().GetInteractor()
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.axesWidget = utils.createAxes(self.interactor)
        grid.addWidget(widget3d, 1, 0, 20, 1)

        loc = locales.getLocale()
        thickness_label = QLabel(loc.Thickness)
        self.thickness_value = QLineEdit("0.2")
        grid.addWidget(thickness_label, 3, 1)
        grid.addWidget(self.thickness_value, 3, 2)

        travelSpeed_label = QLabel(loc.TravelSpeed)
        self.travelSpeed_value = QLineEdit("1")  # TODO: set default
        grid.addWidget(travelSpeed_label, 4, 1)
        grid.addWidget(self.travelSpeed_value, 4, 2)

        extruderTemp_label = QLabel(loc.ExtruderTemp)
        self.extruderTemp_value = QLineEdit("200")
        grid.addWidget(extruderTemp_label, 5, 1)
        grid.addWidget(self.extruderTemp_value, 5, 2)

        bedTemp_label = QLabel( loc.BedTemp)
        self.bedTemp_value = QLineEdit("60")
        grid.addWidget(bedTemp_label, 6, 1)
        grid.addWidget(self.bedTemp_value, 6, 2)

        fillDensity_label = QLabel(loc.FillDensity)
        self.fillDensity_value = QLineEdit("20")
        grid.addWidget(fillDensity_label, 7, 1)
        grid.addWidget(self.fillDensity_value, 7, 2)

        wallThickness_label = QLabel(loc.WallThickness)
        self.wallThickness_value = QLineEdit("0.8")
        grid.addWidget(wallThickness_label, 8, 1)
        grid.addWidget(self.wallThickness_value, 8, 2)

        self.modelSwitch_box = QCheckBox(loc.ShowStl)
        self.modelSwitch_box.stateChanged.connect(self.switchModels)
        grid.addWidget(self.modelSwitch_box, 9, 1)

        self.slider_label = QLabel(loc.LayersCount)
        self.layersNumber_label = QLabel()
        grid.addWidget(self.slider_label, 10, 1)
        grid.addWidget(self.layersNumber_label, 10, 2)

        self.pictureSlider = QSlider()
        self.pictureSlider.setOrientation(QtCore.Qt.Horizontal)
        self.pictureSlider.setMinimum(1)
        self.pictureSlider.setValue(1)
        self.pictureSlider.valueChanged.connect(self.changeLayerView)
        grid.addWidget(self.pictureSlider, 11, 1, 1, 2)

        loadModel_button = QPushButton(loc.OpenModel)
        loadModel_button.clicked.connect(self.openFile)
        grid.addWidget(loadModel_button, 15, 1, 1, 2)

        self.slice_button = QPushButton(loc.Slice)
        self.slice_button.clicked.connect(self.sliceSTL)
        grid.addWidget(self.slice_button, 16, 1, 1, 2)

        self.saveGCode_button = QPushButton(loc.SaveGCode)
        self.saveGCode_button.clicked.connect(self.saveGCodeFile)
        grid.addWidget(self.saveGCode_button, 17, 1, 1, 2)

        self.planeActor = utils.createPlaneActor()
        self.render.AddActor(self.planeActor)
        self.setLayout(grid)
        self.stateNothing()
        self.render.ResetCamera()

    def stateNothing(self):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(False)
        self.layersNumber_label.setEnabled(False)
        self.layersNumber_label.setText(" ")
        self.pictureSlider.setEnabled(False)
        self.slice_button.setEnabled(False)
        self.saveGCode_button.setEnabled(False)
        self.currLayerNumber = 0
        self.state = NothingState

    def stateGcode(self, layers_count):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(True)
        self.layersNumber_label.setEnabled(True)
        self.layersNumber_label.setText(str(layers_count))
        self.pictureSlider.setEnabled(True)
        self.pictureSlider.setMaximum(layers_count)
        self.pictureSlider.setSliderPosition(layers_count)
        self.slice_button.setEnabled(False)
        self.saveGCode_button.setEnabled(True)
        self.currLayerNumber = layers_count
        self.state = GCodeState

    def stateStl(self):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(False)
        self.layersNumber_label.setEnabled(False)
        self.layersNumber_label.setText(" ")
        self.pictureSlider.setEnabled(False)
        self.slice_button.setEnabled(True)
        self.saveGCode_button.setEnabled(False)
        self.currLayerNumber = 0
        self.state = StlState

    def stateBoth(self, layers_count):
        self.modelSwitch_box.setEnabled(True)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(True)
        self.layersNumber_label.setEnabled(True)
        self.layersNumber_label.setText(str(layers_count))
        self.pictureSlider.setEnabled(True)
        self.pictureSlider.setMaximum(layers_count)
        self.pictureSlider.setSliderPosition(layers_count)
        self.slice_button.setEnabled(False)
        self.saveGCode_button.setEnabled(True)
        self.currLayerNumber = layers_count
        self.state = BothState

    def loadGCode(self, filename, clean):
        layers, self.rotations, self.lays2rots = gcode.readGCode(filename)
        blocks = utils.makeBlocks(layers)
        self.actors = utils.wrapWithActors(blocks, self.rotations, self.lays2rots)

        if clean:
            self.clearScene()
            self.render.AddActor(self.planeActor)

        self.rotatePlane(self.rotations[-1])
        for actor in self.actors:
            self.render.AddActor(actor)

        if self.state == StlState:
            self.stateBoth(len(self.actors))
        else:
            self.stateGcode(len(self.actors))

        self.openedGCode = filename
        self.render.ResetCamera()
        self.reloadScene()

    def loadSTL(self, filename):
        self.stlActor, self.stlTranslation = utils.createStlActor(filename)

        if self.state != NothingState:
            self.clearScene()
            self.render.AddActor(self.planeActor)
            self.planeActor.SetUserTransform(vtk.vtkTransform())

        self.render.AddActor(self.stlActor)
        self.stateStl()
        self.openedStl = filename
        self.render.ResetCamera()
        self.reloadScene()

    def changeLayerView(self):
        newSliderValue = self.pictureSlider.value()

        self.actors[newSliderValue - 1].GetProperty().SetColor(params.LastLayerColor)
        self.actors[self.currLayerNumber - 1].GetProperty().SetColor(params.LayerColor)

        self.layersNumber_label.setText(str(newSliderValue))

        if newSliderValue < self.currLayerNumber:
            for layer in range(newSliderValue, self.currLayerNumber):
                self.actors[layer].VisibilityOff()
        else:
            for layer in range(self.currLayerNumber, newSliderValue):
                self.actors[layer].VisibilityOn()

        if self.lays2rots[newSliderValue - 1] != self.lays2rots[self.currLayerNumber - 1]:
            currRotation = self.rotations[self.lays2rots[newSliderValue - 1]]
            for block in range(newSliderValue):
                transform = vtk.vtkTransform()
                transform.PostMultiply()
                transform.RotateZ(-self.rotations[self.lays2rots[block]].z_rot)
                transform.PostMultiply()
                transform.RotateX(-self.rotations[self.lays2rots[block]].x_rot)

                transform.PostMultiply()
                transform.RotateX(currRotation.x_rot)
                transform.PostMultiply()
                transform.RotateZ(currRotation.z_rot)
                self.actors[block].SetUserTransform(transform)

            self.rotatePlane(currRotation)
        self.currLayerNumber = newSliderValue
        self.reloadScene()

    def rotatePlane(self, rotation):
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        transform.RotateX(rotation.x_rot)
        transform.PostMultiply()
        transform.RotateZ(rotation.z_rot)
        self.planeActor.SetUserTransform(transform)

    def sliceSTL(self):
        values = {
            "stl": self.openedStl,
            "gcode": params.OutputGCode,
            "thickness": self.thickness_value.text(),
            "originx": self.stlTranslation[0],
            "originy": self.stlTranslation[1],
            "originz": self.stlTranslation[2],
        }
        cmd = params.SliceCommand.format(**values)
        subprocess.check_output(cmd.split(" "))
        self.stlActor.VisibilityOff()
        self.loadGCode(params.OutputGCode, False)

    def clearScene(self):
        self.render.RemoveAllViewProps()

    def reloadScene(self):
        self.render.Modified()
        self.interactor.Render()

    def switchModels(self, state):
        if state == QtCore.Qt.Checked:
            for actor in self.actors:
                actor.VisibilityOff()
            self.stlActor.VisibilityOn()
        else:
            for actor in self.actors:
                actor.VisibilityOn()
            self.stlActor.VisibilityOff()
        self.reloadScene()

    def openFile(self):
        try:
            filename = str(QFileDialog.getOpenFileName(None, "Open STL file", "/home")[0])  # TODO: fix path
            if filename != "":
                fileExt = os.path.splitext(filename)[1].upper()
                if fileExt == ".STL":
                    self.loadSTL(filename)
                elif fileExt == ".GCODE":
                    self.loadGCode(filename, True)
                else:
                    print("This file format isn't supported:", fileExt)
        except IOError as e:
            print("Error during file opening:", e)

    def saveGCodeFile(self):
        try:
            name = str(QFileDialog.getSaveFileName(None, 'Save GCode File')[0])
            if name != "":
                copy2(self.openedGCode, name)
        except IOError as e:
            print("Error during file saving:", e)
