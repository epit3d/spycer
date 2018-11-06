import os
import shlex
import subprocess
from pathlib import Path
from shutil import copy2

import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit, QGridLayout, QSlider, QCheckBox, QPushButton, QFileDialog)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import params
from src import debug, gcode, locales, utils

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

        self.locale = locales.getLocale()
        thickness_label = QLabel(self.locale.Thickness)
        self.thickness_value = QLineEdit("0.2")
        grid.addWidget(thickness_label, 2, 1)
        grid.addWidget(self.thickness_value, 2, 2)

        printSpeed_label = QLabel(self.locale.PrintSpeed)
        self.printSpeed_value = QLineEdit("50")
        grid.addWidget(printSpeed_label, 3, 1)
        grid.addWidget(self.printSpeed_value, 3, 2)

        extruderTemp_label = QLabel(self.locale.ExtruderTemp)
        self.extruderTemp_value = QLineEdit("200")
        grid.addWidget(extruderTemp_label, 4, 1)
        grid.addWidget(self.extruderTemp_value, 4, 2)

        bedTemp_label = QLabel(self.locale.BedTemp)
        self.bedTemp_value = QLineEdit("60")
        grid.addWidget(bedTemp_label, 5, 1)
        grid.addWidget(self.bedTemp_value, 5, 2)

        fillDensity_label = QLabel(self.locale.FillDensity)
        self.fillDensity_value = QLineEdit("20")
        grid.addWidget(fillDensity_label, 6, 1)
        grid.addWidget(self.fillDensity_value, 6, 2)

        wallThickness_label = QLabel(self.locale.WallThickness)
        self.wallThickness_value = QLineEdit("0.8")
        grid.addWidget(wallThickness_label, 7, 1)
        grid.addWidget(self.wallThickness_value, 7, 2)

        nozzle_label = QLabel(self.locale.Nozzle)
        self.nozzle_value = QLineEdit("0.4")
        grid.addWidget(nozzle_label, 8, 1)
        grid.addWidget(self.nozzle_value, 8, 2)

        self.modelSwitch_box = QCheckBox(self.locale.ShowStl)
        self.modelSwitch_box.stateChanged.connect(self.switchModels)
        grid.addWidget(self.modelSwitch_box, 9, 1)

        self.slider_label = QLabel(self.locale.LayersCount)
        self.layersNumber_label = QLabel()
        grid.addWidget(self.slider_label, 10, 1)
        grid.addWidget(self.layersNumber_label, 10, 2)

        self.pictureSlider = QSlider()
        self.pictureSlider.setOrientation(QtCore.Qt.Horizontal)
        self.pictureSlider.setMinimum(1)
        self.pictureSlider.setValue(1)
        self.pictureSlider.valueChanged.connect(self.changeLayerView)
        grid.addWidget(self.pictureSlider, 11, 1, 1, 2)

        loadModel1_button = QPushButton("Open out_home.gcode")  # TODO: remove me
        loadModel1_button.clicked.connect(lambda: self.loadGCode("/home/l1va/out_home.gcode", False))
        #grid.addWidget(loadModel1_button, 12, 1, 1, 2)

        self.xPosition_value = QLineEdit("0")
        grid.addWidget(self.xPosition_value, 13, 1)
        self.yPosition_value = QLineEdit("0")
        grid.addWidget(self.yPosition_value, 13, 2)
        self.zPosition_value = QLineEdit("0")
        grid.addWidget(self.zPosition_value, 14, 1)
        self.move_button = QPushButton(self.locale.MoveModel)
        self.move_button.clicked.connect(self.moveModel)
        grid.addWidget(self.move_button, 14, 2, 1, 1)

        loadModel_button = QPushButton(self.locale.OpenModel)
        loadModel_button.clicked.connect(self.openFile)
        grid.addWidget(loadModel_button, 15, 1, 1, 2)

        self.slice3a_button = QPushButton(self.locale.Slice3Axes)
        self.slice3a_button.clicked.connect(lambda: self.sliceSTL("3axes"))
        grid.addWidget(self.slice3a_button, 16, 1, 1, 1)

        # self.slice5aProfile_button = QPushButton(self.locale.Slice5AxesByProfile)
        # self.slice5aProfile_button.clicked.connect(lambda: self.sliceSTL("5axes_by_profile"))
        # grid.addWidget(self.slice5aProfile_button, 15, 1, 1, 2)

        # self.slice5a_button = QPushButton(self.locale.Slice5Axes)
        # self.slice5a_button.clicked.connect(lambda: self.sliceSTL("5axes"))
        # grid.addWidget(self.slice5a_button, 16, 1, 1, 1)

        self.sliceVip_button = QPushButton(self.locale.SliceVip)
        self.sliceVip_button.clicked.connect(lambda: self.sliceSTL("vip"))
        grid.addWidget(self.sliceVip_button, 16, 2, 1, 1)

        self.saveGCode_button = QPushButton(self.locale.SaveGCode)
        self.saveGCode_button.clicked.connect(self.saveGCodeFile)
        grid.addWidget(self.saveGCode_button, 17, 1, 1, 2)

        self.simplifyStl_button = QPushButton(self.locale.SimplifyStl)
        self.simplifyStl_button.clicked.connect(self.simplifyStl)
        grid.addWidget(self.simplifyStl_button, 18, 1, 1, 2)

        self.cutStl_button = QPushButton(self.locale.CutStl)
        self.cutStl_button.clicked.connect(self.cutStl)
        grid.addWidget(self.cutStl_button, 19, 1, 1, 2)

        self.changePlane_button = QPushButton(self.locale.ChangePlane)
        self.changePlane_button.clicked.connect(self.changePlane)
        grid.addWidget(self.changePlane_button, 20, 1, 1, 1)

        if params.Debug:
            debug_button = QPushButton("Debug")
            debug_button.clicked.connect(self.debugMe)
            grid.addWidget(debug_button, 20, 2, 1, 1)

        self.planes = [utils.createPlaneActor(), utils.createPlaneActor2(), utils.createPlaneActorCircle()]
        self.curPlane = 2
        self.planeActor = self.planes[self.curPlane]
        self.planeTransform = vtk.vtkTransform()
        self.render.AddActor(self.planeActor)
        self.setLayout(grid)
        self.stateNothing()
        self.render.ResetCamera()

    def changePlane(self):
        self.curPlane = (self.curPlane + 1) % len(self.planes)
        self.render.RemoveActor(self.planeActor)
        self.planeActor = self.planes[self.curPlane]
        self.planeActor.SetUserTransform(self.planeTransform)
        self.render.AddActor(self.planeActor)
        self.reloadScene()

    def stateNothing(self):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(False)
        self.layersNumber_label.setEnabled(False)
        self.layersNumber_label.setText(" ")
        self.currLayerNumber = 0
        self.pictureSlider.setEnabled(False)
        self.pictureSlider.setSliderPosition(0)
        self.move_button.setEnabled(False)
        self.slice3a_button.setEnabled(False)
        # self.slice5aProfile_button.setEnabled(False)
        # self.slice5a_button.setEnabled(False)
        self.sliceVip_button.setEnabled(False)
        self.saveGCode_button.setEnabled(False)
        self.simplifyStl_button.setEnabled(False)
        self.cutStl_button.setEnabled(False)
        self.state = NothingState

    def stateGcode(self, layers_count):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(True)
        self.layersNumber_label.setEnabled(True)
        self.layersNumber_label.setText(str(layers_count))
        self.currLayerNumber = layers_count
        self.pictureSlider.setEnabled(True)
        self.pictureSlider.setMaximum(layers_count)
        self.pictureSlider.setSliderPosition(layers_count)
        self.move_button.setEnabled(False)
        self.slice3a_button.setEnabled(False)
        # self.slice5aProfile_button.setEnabled(False)
        # self.slice5a_button.setEnabled(False)
        self.sliceVip_button.setEnabled(False)
        self.saveGCode_button.setEnabled(True)
        self.simplifyStl_button.setEnabled(False)
        self.cutStl_button.setEnabled(False)
        self.state = GCodeState

    def stateStl(self):
        self.modelSwitch_box.setEnabled(False)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(False)
        self.layersNumber_label.setEnabled(False)
        self.layersNumber_label.setText(" ")
        self.currLayerNumber = 0
        self.pictureSlider.setEnabled(False)
        self.pictureSlider.setSliderPosition(0)
        self.move_button.setEnabled(True)
        self.slice3a_button.setEnabled(True)
        # self.slice5aProfile_button.setEnabled(True)
        # self.slice5a_button.setEnabled(True)
        self.sliceVip_button.setEnabled(True)
        self.saveGCode_button.setEnabled(False)
        self.simplifyStl_button.setEnabled(True)
        self.cutStl_button.setEnabled(True)
        self.state = StlState

    def stateBoth(self, layers_count):
        self.modelSwitch_box.setEnabled(True)
        self.modelSwitch_box.setChecked(False)
        self.slider_label.setEnabled(True)
        self.layersNumber_label.setEnabled(True)
        self.layersNumber_label.setText(str(layers_count))
        self.currLayerNumber = layers_count
        self.pictureSlider.setEnabled(True)
        self.pictureSlider.setMaximum(layers_count)
        self.pictureSlider.setSliderPosition(layers_count)
        self.move_button.setEnabled(True)
        self.slice3a_button.setEnabled(True)
        # self.slice5aProfile_button.setEnabled(True)
        # self.slice5a_button.setEnabled(True)
        self.sliceVip_button.setEnabled(True)
        self.saveGCode_button.setEnabled(True)
        self.simplifyStl_button.setEnabled(False)
        self.cutStl_button.setEnabled(False)
        self.state = BothState

    def moveModel(self):
        self.stlTranslation = [float(self.xPosition_value.text()), float(self.yPosition_value.text()),
                               float(self.zPosition_value.text())]
        print(self.stlTranslation)
        transform = vtk.vtkTransform()
        transform.Translate(self.stlTranslation[0], self.stlTranslation[1], self.stlTranslation[2])
        self.stlActor.SetUserTransform(transform)
        self.reloadScene()

    def loadGCode(self, filename, addStl):
        layers, self.rotations, self.lays2rots = gcode.readGCode(filename)
        blocks = utils.makeBlocks(layers)
        self.actors = utils.wrapWithActors(blocks, self.rotations, self.lays2rots)

        self.clearScene()
        self.render.AddActor(self.planeActor)
        if addStl:
            self.render.AddActor(self.stlActor)

        self.rotatePlane(self.rotations[-1])
        for actor in self.actors:
            self.render.AddActor(actor)

        if addStl:
            self.stateBoth(len(self.actors))
        else:
            self.stateGcode(len(self.actors))

        self.openedGCode = filename
        self.render.ResetCamera()
        self.reloadScene()

    def loadSTL(self, filename):
        self.stlActor, self.stlTranslation = utils.createStlActorInOrigin(filename)
        print(self.stlTranslation)
        self.xPosition_value.setText(str(self.stlTranslation[0])[:10])
        self.yPosition_value.setText(str(self.stlTranslation[1])[:10])
        self.zPosition_value.setText(str(self.stlTranslation[2])[:10])

        self.clearScene()
        self.render.AddActor(self.planeActor)

        self.render.AddActor(self.stlActor)
        self.stateStl()
        self.openedStl = filename
        self.render.ResetCamera()
        self.reloadScene()

    def simplifyStl(self):
        values = {
            "stl": format_path(self.openedStl),
            "out": params.OutputSimplifiedStl,
            "triangles": params.SimplifyTriangles,
        }
        cmd = params.SimplifyStlCommand.format(**values)
        subprocess.check_output(shlex.split(cmd))
        self.loadSTL(params.OutputSimplifiedStl)

    def cutStl(self):
        values = {
            "stl": format_path(self.openedStl),
            "out1": params.OutputCutStl1,
            "out2": params.OutputCutStl2,
            "pointx": params.CutPointX,
            "pointy": params.CutPointY,
            "pointz": params.CutPointZ,
            "normali": params.CutNormalI,
            "normalj": params.CutNormalJ,
            "normalk": params.CutNormalK,
        }
        cmd = params.CutStlCommand.format(**values)
        subprocess.check_output(shlex.split(cmd))
        self.clearScene()
        self.render.AddActor(self.planeActor)
        actor1, _ = utils.createStlActor(params.OutputCutStl1)
        self.render.AddActor(actor1)
        actor2, _ = utils.createStlActor(params.OutputCutStl2)
        transform = vtk.vtkTransform()
        transform.Translate(params.Cut2Move)
        actor2.SetUserTransform(transform)
        self.render.AddActor(actor2)

        self.stateNothing()
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
                transform.RotateX(-self.rotations[self.lays2rots[block]].x_rot)
                transform.PostMultiply()
                transform.RotateZ(-self.rotations[self.lays2rots[block]].z_rot)

                transform.PostMultiply()
                transform.RotateZ(currRotation.z_rot)
                transform.PostMultiply()
                transform.RotateX(currRotation.x_rot)
                self.actors[block].SetUserTransform(transform)

            self.rotatePlane(currRotation)
        self.currLayerNumber = newSliderValue
        self.reloadScene()

    def rotatePlane(self, rotation):
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        transform.RotateZ(rotation.z_rot)
        transform.PostMultiply()
        transform.RotateX(rotation.x_rot)
        self.planeActor.SetUserTransform(transform)
        self.planeTransform = transform

    def sliceSTL(self, slicing_type):
        values = {
            "stl": format_path(self.openedStl),
            "gcode": params.OutputGCode,
            "originx": self.stlTranslation[0],
            "originy": self.stlTranslation[1],
            "originz": self.stlTranslation[2],

            "thickness": self.thickness_value.text(),
            "wall_thickness": self.wallThickness_value.text(),
            "fill_density": self.fillDensity_value.text(),
            "bed_temperature": self.bedTemp_value.text(),
            "extruder_temperature": self.extruderTemp_value.text(),
            "print_speed": self.printSpeed_value.text(),
            "nozzle": self.nozzle_value.text(),
            "slicing_type": slicing_type,
        }
        cmd = params.SliceCommand.format(**values)
        print(cmd)
        subprocess.check_output(shlex.split(cmd))
        self.stlActor.VisibilityOff()
        self.loadGCode(params.OutputGCode, True)

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
            filename = str(QFileDialog.getOpenFileName(None, self.locale.OpenModel, "/home")[0])  # TODO: fix path
            if filename != "":
                fileExt = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if fileExt == ".STL":
                    self.loadSTL(filename)
                elif fileExt == ".GCODE":
                    self.loadGCode(filename, False)
                else:
                    print("This file format isn't supported:", fileExt)
        except IOError as e:
            print("Error during file opening:", e)

    def saveGCodeFile(self):
        try:
            name = str(QFileDialog.getSaveFileName(None, self.locale.SaveGCode)[0])
            if name != "":
                copy2(self.openedGCode, name)
        except IOError as e:
            print("Error during file saving:", e)

    def debugMe(self):
        debug.readFile(self.render, "/home/l1va/debug.txt",  4)
        # debug.readFile(self.render, "/home/l1va/debug_simplified.txt", "Red", 3)
        self.reloadScene()


def format_path(path):
    if " " in path:
        return '"{}"'.format(path)
    return path
