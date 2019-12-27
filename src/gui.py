import os
import subprocess
from pathlib import Path
from shutil import copy2

import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QTabWidget, QLineEdit, QComboBox, QGridLayout, QSlider, QCheckBox,
                             QPushButton, QFileDialog)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import params
from src import debug, gcode, locales, gui_utils

NothingState = "nothing"
GCodeState = "gcode"
StlState = "stl"
BothState = "both"


class Gui(QWidget):
    def prepareWidgets(self):
        self.setWindowTitle('Spycer')

        self.locale = locales.getLocale()

        main_grid = QGridLayout()
        main_grid.addWidget(self.init3dWidget(), 0, 0, 20, 5)
        main_grid.addLayout(self.initRightPanel(), 0, 5, 20, 2)

        self.bottom_panel = self.initBottomPanel()
        self.bottom_panel.setEnabled(False)
        main_grid.addWidget(self.bottom_panel, 20, 0, 2, 7)

        self.setLayout(main_grid)

        self.planeActor = gui_utils.createPlaneActorCircle()
        self.planeTransform = vtk.vtkTransform()
        self.render.AddActor(self.planeActor)

        self.stateNothing()
        self.render.ResetCamera()

        self.planes = []
        self.planesActors = []

        self.openedStl = "/home/l1va/Downloads/1_odn2.stl"  # TODO: removeme
        self.loadSTL(self.openedStl)
        # self.colorizeModel()

    def init3dWidget(self):
        widget3d = QVTKRenderWindowInteractor()
        widget3d.Initialize()
        widget3d.Start()
        self.render = vtk.vtkRenderer()
        self.render.SetBackground(params.BackgroundColor)
        widget3d.GetRenderWindow().AddRenderer(self.render)
        self.interactor = widget3d.GetRenderWindow().GetInteractor()
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.axesWidget = gui_utils.createAxes(self.interactor)
        return widget3d

    def initRightPanel(self):
        right_panel = QGridLayout()
        right_panel.setSpacing(5)
        right_panel.setColumnStretch(0, 2)

        thickness_label = QLabel(self.locale.Thickness)
        self.thickness_value = QLineEdit("0.2")
        right_panel.addWidget(thickness_label, 2, 1)
        right_panel.addWidget(self.thickness_value, 2, 2)

        printSpeed_label = QLabel(self.locale.PrintSpeed)
        self.printSpeed_value = QLineEdit("50")
        right_panel.addWidget(printSpeed_label, 3, 1)
        right_panel.addWidget(self.printSpeed_value, 3, 2)

        extruderTemp_label = QLabel(self.locale.ExtruderTemp)
        self.extruderTemp_value = QLineEdit("200")
        right_panel.addWidget(extruderTemp_label, 4, 1)
        right_panel.addWidget(self.extruderTemp_value, 4, 2)

        bedTemp_label = QLabel(self.locale.BedTemp)
        self.bedTemp_value = QLineEdit("60")
        right_panel.addWidget(bedTemp_label, 5, 1)
        right_panel.addWidget(self.bedTemp_value, 5, 2)

        fillDensity_label = QLabel(self.locale.FillDensity)
        self.fillDensity_value = QLineEdit("20")
        right_panel.addWidget(fillDensity_label, 6, 1)
        right_panel.addWidget(self.fillDensity_value, 6, 2)

        wallThickness_label = QLabel(self.locale.WallThickness)
        self.wallThickness_value = QLineEdit("0.8")
        right_panel.addWidget(wallThickness_label, 7, 1)
        right_panel.addWidget(self.wallThickness_value, 7, 2)

        nozzle_label = QLabel(self.locale.Nozzle)
        self.nozzle_value = QLineEdit("0.4")
        right_panel.addWidget(nozzle_label, 8, 1)
        right_panel.addWidget(self.nozzle_value, 8, 2)

        self.modelSwitch_box = QCheckBox(self.locale.ShowStl)
        self.modelSwitch_box.stateChanged.connect(self.switchModels)
        right_panel.addWidget(self.modelSwitch_box, 9, 1)

        self.slider_label = QLabel(self.locale.LayersCount)
        self.layersNumber_label = QLabel()
        right_panel.addWidget(self.slider_label, 10, 1)
        right_panel.addWidget(self.layersNumber_label, 10, 2)

        self.pictureSlider = QSlider()
        self.pictureSlider.setOrientation(QtCore.Qt.Horizontal)
        self.pictureSlider.setMinimum(1)
        self.pictureSlider.setValue(1)
        self.pictureSlider.valueChanged.connect(self.changeLayerView)
        right_panel.addWidget(self.pictureSlider, 11, 1, 1, 2)

        self.xPosition_value = QLineEdit("0")
        right_panel.addWidget(self.xPosition_value, 13, 1)
        self.yPosition_value = QLineEdit("0")
        right_panel.addWidget(self.yPosition_value, 13, 2)
        self.zPosition_value = QLineEdit("0")
        right_panel.addWidget(self.zPosition_value, 14, 1)
        self.move_button = QPushButton(self.locale.MoveModel)
        self.move_button.clicked.connect(self.moveModel)
        right_panel.addWidget(self.move_button, 14, 2, 1, 1)

        loadModel_button = QPushButton(self.locale.OpenModel)
        loadModel_button.clicked.connect(self.openFile)
        right_panel.addWidget(loadModel_button, 15, 1, 1, 1)

        self.editPlanes_button = QPushButton("Редактировать")  # TODO: locales
        self.editPlanes_button.clicked.connect(lambda: self.loadSTL(self.openedStl))
        right_panel.addWidget(self.editPlanes_button, 15, 2, 1, 1)

        self.slice3a_button = QPushButton(self.locale.Slice3Axes)
        self.slice3a_button.clicked.connect(lambda: self.sliceSTL("3axes"))
        right_panel.addWidget(self.slice3a_button, 16, 1, 1, 1)

        self.sliceVip_button = QPushButton(self.locale.SliceVip)
        self.sliceVip_button.clicked.connect(lambda: self.sliceSTL("vip"))
        right_panel.addWidget(self.sliceVip_button, 16, 2, 1, 1)

        self.saveGCode_button = QPushButton(self.locale.SaveGCode)
        self.saveGCode_button.clicked.connect(self.saveGCodeFile)
        right_panel.addWidget(self.saveGCode_button, 17, 1, 1, 1)

        self.analyzeModel_button = QPushButton("Анализировать")  # TODO: locales
        self.analyzeModel_button.clicked.connect(self.analyzeModel)
        right_panel.addWidget(self.analyzeModel_button, 17, 2, 1, 1)

        self.colorizeAngle_value = QLineEdit("30")
        right_panel.addWidget(self.colorizeAngle_value, 18, 1)

        self.colorModel_button = QPushButton(self.locale.ColorModel)
        self.colorModel_button.clicked.connect(self.colorizeModel)
        right_panel.addWidget(self.colorModel_button, 18, 2, 1, 1)

        return right_panel

    def initBottomPanel(self):

        bottom_layout = QGridLayout()
        bottom_layout.setSpacing(5)
        bottom_layout.setColumnStretch(7, 1)

        self.addPlane_button = QPushButton("Добавить")
        self.addPlane_button.clicked.connect(self.addPlane)
        bottom_layout.addWidget(self.addPlane_button, 1, 0)

        comboW = QWidget()
        self.combo = QComboBox(comboW)
        self.combo.currentIndexChanged.connect(self.changeComboSelect)
        bottom_layout.addWidget(comboW, 0, 0, 1, 2)

        self.removePlane_button = QPushButton("Удалить")
        self.removePlane_button.clicked.connect(self.removePlane)
        bottom_layout.addWidget(self.removePlane_button, 2, 0)

        self.tilted_checkbox = QCheckBox(self.locale.Tilted)
        self.tilted_checkbox.stateChanged.connect(self.applyPlaneChange)
        bottom_layout.addWidget(self.tilted_checkbox, 0, 3)

        x_label = QLabel("X:")  # TODO: to locales
        bottom_layout.addWidget(x_label, 0, 4)
        self.x_value = QLineEdit("3.0951")
        self.x_value.editingFinished.connect(self.applyEditsChange)
        bottom_layout.addWidget(self.x_value, 0, 5)

        y_label = QLabel("Y:")  # TODO: to locales
        bottom_layout.addWidget(y_label, 1, 4)
        self.y_value = QLineEdit("5.5910")
        self.y_value.editingFinished.connect(self.applyEditsChange)
        bottom_layout.addWidget(self.y_value, 1, 5)

        z_label = QLabel("Z:")  # TODO: to locales
        bottom_layout.addWidget(z_label, 2, 4)
        self.z_value = QLineEdit("89.5414")
        self.z_value.editingFinished.connect(self.applyEditsChange)
        bottom_layout.addWidget(self.z_value, 2, 5)

        rotated_label = QLabel("Повёрнута:")  # TODO: to locales
        bottom_layout.addWidget(rotated_label, 3, 4)
        self.rotated_value = QLineEdit("31.0245")
        self.rotated_value.editingFinished.connect(self.applyEditsChange)
        bottom_layout.addWidget(self.rotated_value, 3, 5)

        self.xSlider = QSlider()
        self.xSlider.setOrientation(QtCore.Qt.Horizontal)
        self.xSlider.setMinimum(-100)
        self.xSlider.setMaximum(100)
        self.xSlider.setValue(1)
        self.xSlider.valueChanged.connect(self.applyPlaneChange)
        bottom_layout.addWidget(self.xSlider, 0, 6, 1, 2)
        self.ySlider = QSlider()
        self.ySlider.setOrientation(QtCore.Qt.Horizontal)
        self.ySlider.setMinimum(-100)
        self.ySlider.setMaximum(100)
        self.ySlider.setValue(1)
        self.ySlider.valueChanged.connect(self.applyPlaneChange)
        bottom_layout.addWidget(self.ySlider, 1, 6, 1, 2)
        self.zSlider = QSlider()
        self.zSlider.setOrientation(QtCore.Qt.Horizontal)
        self.zSlider.setMinimum(0)
        self.zSlider.setMaximum(200)
        self.zSlider.setValue(1)
        self.zSlider.valueChanged.connect(self.applyPlaneChange)
        bottom_layout.addWidget(self.zSlider, 2, 6, 1, 2)
        self.rotSlider = QSlider()
        self.rotSlider.setOrientation(QtCore.Qt.Horizontal)
        self.rotSlider.setMinimum(-180)
        self.rotSlider.setMaximum(180)
        self.rotSlider.setValue(0)
        self.rotSlider.valueChanged.connect(self.applyPlaneChange)
        bottom_layout.addWidget(self.rotSlider, 3, 6, 1, 2)

        # self.applyPlane_button = QPushButton("Применить")  # TODO:
        # self.applyPlane_button.clicked.connect(self.applyPlaneChange)
        # bottom_layout.addWidget(self.applyPlane_button, 2, 2)

        bottom_panel = QWidget()
        bottom_panel.setLayout(bottom_layout)

        return bottom_panel

    def applyEditsChange(self):
        self.xSlider.setValue(float(self.x_value.text()))
        self.ySlider.setValue(float(self.y_value.text()))
        self.zSlider.setValue(float(self.z_value.text()))
        self.rotSlider.setValue(float(self.rotated_value.text()))

    def applyPlaneChange(self):
        self.x_value.setText(str(self.xSlider.value()))
        self.y_value.setText(str(self.ySlider.value()))
        self.z_value.setText(str(self.zSlider.value()))
        self.rotated_value.setText(str(self.rotSlider.value()))

        center = [float(self.xSlider.value()), float(self.ySlider.value()), float(self.zSlider.value())]
        ind = self.combo.currentIndex()
        if ind == -1:
            return
        self.planes[ind] = gui_utils.Plane(self.tilted_checkbox.isChecked(), float(self.rotSlider.value()), center)
        self.drawPlanes()

    def addPlane(self):
        if len(self.planes)==0:
            self.planes.append(gui_utils.Plane(True, 0, [10,10,10]))
        else:
            path = [self.planes[-1].x, self.planes[-1].y, self.planes[-1].z + 10]
            self.planes.append(gui_utils.Plane(False, 0, path))
        self.loadPlanes()

    def removePlane(self):
        ind = self.combo.currentIndex()
        if ind == -1:
            return
        del self.planes[ind]
        self.loadPlanes()

    def changeComboSelect(self):
        ind = self.combo.currentIndex()
        if ind==-1:
            return
        plane = self.planes[ind]
        self.tilted_checkbox.setChecked(plane.tilted)
        self.rotated_value.setText(str(plane.rot))
        self.x_value.setText(str(plane.x))
        self.y_value.setText(str(plane.y))
        self.z_value.setText(str(plane.z))
        self.xSlider.setValue(plane.x)
        self.ySlider.setValue(plane.y)
        self.zSlider.setValue(plane.z)
        self.rotSlider.setValue(plane.rot)
        self.planesActors[ind].GetProperty().SetColor(params.LastLayerColor)
        self.reloadScene()

    def loadPlanes(self):
        #if len(self.planes) == 0:
        #    self.bottom_panel.setEnabled(False)
        #    return

        #self.bottom_panel.setEnabled(True)

        self.combo.clear()
        for i in range(len(self.planes)):
            self.combo.addItem("Плоскость " + str(i + 1))

        self.changeComboSelect()

        self.drawPlanes()

    def drawPlanes(self):  # TODO: optimize
        for p in self.planesActors:
            self.render.RemoveActor(p)
        self.planesActors = []
        for p in self.planes:
            # rot = self.rotations[self.lays2rots[-1]]

            act = gui_utils.createPlaneActorCircleByCenterAndRot([p.x, p.y, p.z], -60 if p.tilted else 0, p.rot)
            # act = utils.createPlaneActorCircleByCenterAndRot([p.x, p.y, p.z], 0,0)
            # print("tilted" if p.tilted else "NOT")
            self.planesActors.append(act)
            self.render.AddActor(act)
        ind = self.combo.currentIndex()
        if ind != -1:
            self.planesActors[ind].GetProperty().SetColor(params.LastLayerColor)
        # print("was draw planes: ",len(self.planes))
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
        self.colorModel_button.setEnabled(False)
        self.editPlanes_button.setEnabled(False)
        # self.slice5aProfile_button.setEnabled(False)
        # self.slice5a_button.setEnabled(False)
        self.sliceVip_button.setEnabled(False)
        self.saveGCode_button.setEnabled(False)
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
        self.colorModel_button.setEnabled(False)
        self.editPlanes_button.setEnabled(True)
        # self.slice5aProfile_button.setEnabled(False)
        # self.slice5a_button.setEnabled(False)
        self.sliceVip_button.setEnabled(False)
        self.saveGCode_button.setEnabled(True)
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
        self.colorModel_button.setEnabled(True)
        self.editPlanes_button.setEnabled(False)
        # self.slice5aProfile_button.setEnabled(True)
        # self.slice5a_button.setEnabled(True)
        self.sliceVip_button.setEnabled(True)
        self.saveGCode_button.setEnabled(False)
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
        self.colorModel_button.setEnabled(True)
        self.editPlanes_button.setEnabled(True)
        # self.slice5aProfile_button.setEnabled(True)
        # self.slice5a_button.setEnabled(True)
        self.sliceVip_button.setEnabled(True)
        self.saveGCode_button.setEnabled(True)
        self.state = BothState

    def moveModel(self):
        self.stlTranslation = [float(self.xPosition_value.text()), float(self.yPosition_value.text()),
                               float(self.zPosition_value.text())]
        print(self.stlTranslation)
        transform = vtk.vtkTransform()
        transform.Translate(self.stlTranslation[0], self.stlTranslation[1],
                            self.stlTranslation[2])
        self.stlActor.SetUserTransform(transform)
        self.reloadScene()

    def loadGCode(self, filename, addStl):
        gode = gcode.readGCode(filename)
        self.gode = gode
        blocks = gui_utils.makeBlocks(gode.layers)
        self.actors = gui_utils.wrapWithActors(blocks, gode.rotations, gode.lays2rots)

        self.clearScene()
        self.render.AddActor(self.planeActor)
        if addStl:
            self.render.AddActor(self.stlActor)

        self.rotatePlane(gode.rotations[-1])
        for actor in self.actors:
            self.render.AddActor(actor)

        #self.loadPlanes()
        self.bottom_panel.setEnabled(False)

        if addStl:
            self.stateBoth(len(self.actors))
        else:
            self.stateGcode(len(self.actors))

        self.openedGCode = filename
        self.render.ResetCamera()
        self.reloadScene()

    def loadSTL(self, filename, method=gui_utils.createStlActorInOrigin):
        self.stlActor, self.stlTranslation, self.stlBounds = method(filename)
        # self.xSlider.setMinimum(self.stlBounds[0])
        # self.xSlider.setMaximum(self.stlBounds[1])
        # self.ySlider.setMinimum(self.stlBounds[2])
        # self.ySlider.setMaximum(self.stlBounds[3])
        # self.zSlider.setMinimum(self.stlBounds[4])
        # self.zSlider.setMaximum(self.stlBounds[5])
        # print(self.stlTranslation)
        self.xPosition_value.setText(str(self.stlTranslation[0])[:10])
        self.yPosition_value.setText(str(self.stlTranslation[1])[:10])
        self.zPosition_value.setText(str(self.stlTranslation[2])[:10])

        self.clearScene()
        self.render.AddActor(self.planeActor)

        self.render.AddActor(self.stlActor)
        self.bottom_panel.setEnabled(True)
        self.loadPlanes()
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

        if self.gode.lays2rots[newSliderValue - 1] != self.gode.lays2rots[self.currLayerNumber - 1]:
            currRotation = self.gode.rotations[self.gode.lays2rots[newSliderValue - 1]]
            for block in range(newSliderValue):
                transform = vtk.vtkTransform()

                transform.PostMultiply()
                transform.RotateX(-self.gode.rotations[self.gode.lays2rots[block]].x_rot)
                transform.PostMultiply()
                transform.RotateZ(-self.gode.rotations[self.gode.lays2rots[block]].z_rot)

                transform.PostMultiply()
                transform.RotateZ(currRotation.z_rot)
                transform.PostMultiply()
                transform.RotateX(currRotation.x_rot)
                self.actors[block].SetUserTransform(transform)

            self.rotatePlane(currRotation)
            for i in range(len(self.planes)):
                self.rotateAnyPlane(self.planesActors[i], self.planes[i], currRotation)
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

    def rotateAnyPlane(self, planeActor, plane, rotation):
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        transform.RotateX(-60 if plane.tilted else 0)
        transform.PostMultiply()
        transform.RotateZ(plane.rot)
        transform.Translate(plane.x, plane.y, plane.z - 0.1)

        transform.PostMultiply()
        transform.RotateZ(rotation.z_rot)
        transform.PostMultiply()
        transform.RotateX(rotation.x_rot)
        planeActor.SetUserTransform(transform)

    def sliceSTL(self, slicing_type):
        values = {
            "stl": format_path(self.openedStl),
            "gcode": params.OutputGCode,
            "originx": self.stlTranslation[0],
            "originy": self.stlTranslation[1],
            "originz": self.stlTranslation[2],
            "rotcx": params.RotationCenter[0],
            "rotcy": params.RotationCenter[1],
            "rotcz": params.RotationCenter[2],

            "thickness": self.thickness_value.text(),
            "wall_thickness": self.wallThickness_value.text(),
            "fill_density": self.fillDensity_value.text(),
            "bed_temperature": self.bedTemp_value.text(),
            "extruder_temperature": self.extruderTemp_value.text(),
            "print_speed": self.printSpeed_value.text(),
            "nozzle": self.nozzle_value.text(),
            "slicing_type": slicing_type,
            "planes_file": params.PlanesFile,
        }
        self.savePlanesToFile()
        cmd = params.SliceCommand.format(**values)
        print(cmd)
        subprocess.check_output(str.split(cmd))
        self.stlActor.VisibilityOff()
        self.loadGCode(params.OutputGCode, True)

    def savePlanesToFile(self):
        with open(params.PlanesFile, 'w') as out:
            for p in self.planes:
                out.write(p.toFile() + '\n')


    def colorizeModel(self):
        values = {
            "stl": format_path(self.openedStl),
            "out": params.ColorizeResult,
            "angle": self.colorizeAngle_value.text(),
        }
        cmd = params.ColorizeStlCommand.format(**values)
        subprocess.check_output(str.split(cmd))
        self.loadSTL(self.openedStl, method=gui_utils.createStlActorInOriginWithColorize)

    def analyzeModel(self):
        values = {
            "stl": format_path(self.openedStl),
            "angle": self.colorizeAngle_value.text(),
            "out": params.AnalyzeResult,
            "originx": self.stlTranslation[0],
            "originy": self.stlTranslation[1],
            "originz": self.stlTranslation[2],
            "rotcx": params.RotationCenter[0],
            "rotcy": params.RotationCenter[1],
            "rotcz": params.RotationCenter[2],
        }
        cmd = params.AnalyzeStlCommand.format(**values)
        subprocess.check_output(str.split(cmd))
        self.planes = gui_utils.read_planes()
        self.bottom_panel.setEnabled(True)
        # self.openedStl = "cuttedSTL.stl"
        self.loadSTL(self.openedStl, method=gui_utils.createStlActorInOrigin)

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
            for layer in range(self.pictureSlider.value()):
                self.actors[layer].VisibilityOn()
            self.stlActor.VisibilityOff()
        self.reloadScene()

    def openFile(self):
        try:
            filename = str(
                QFileDialog.getOpenFileName(None, self.locale.OpenModel, "/home/l1va/Downloads/5axes_3d_printer/test",
                                            "STL (*.stl)")[0])  # TODO: fix path
            if filename != "":
                self.planes = []
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
            name = str(QFileDialog.getSaveFileName(None, self.locale.SaveGCode, "", "Gcode (*.gcode)")[0])
            if name != "":
                if not name.endswith(".gcode"):
                    name += ".gcode"
                copy2(self.openedGCode, name)
        except IOError as e:
            print("Error during file saving:", e)

    # def debugMe(self):
    #     debug.readFile(self.render, "/home/l1va/debug.txt", 4)
    #     # debug.readFile(self.render, "/home/l1va/debug_simplified.txt", "Red", 3)
    #     self.reloadScene()


def format_path(path):
    if " " in path:
        return '"{}"'.format(path)
    return path
