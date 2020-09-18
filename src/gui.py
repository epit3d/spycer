import os
import shlex
import subprocess
import sys
from pathlib import Path

from shutil import copy2

import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QTabWidget, QLineEdit, QComboBox, QGridLayout, QSlider, QCheckBox,
                             QPushButton, QFileDialog, QScrollArea, QGroupBox)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import params
from src import debug, gcode, locales, gui_utils
from src.gui_utils import isfloat, showErrorDialog

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
        main_grid.addWidget(self.initRightPanel(), 0, 5, 20, 2)

        self.bottom_panel = self.initBottomPanel()
        self.bottom_panel.setEnabled(False)
        main_grid.addWidget(self.bottom_panel, 20, 0, 2, 7)

        self.setLayout(main_grid)

        self.planeActor = gui_utils.createPlaneActorCircle()
        self.planeTransform = vtk.vtkTransform()
        self.render.AddActor(self.planeActor)

        self.boxActors = gui_utils.createBoxActors()
        for b in self.boxActors:
            self.render.AddActor(b)

        self.stateNothing()
        self.render.ResetCamera()

        self.planes = []
        self.planesActors = []

        # self.openedStl = "/home/l1va/Downloads/1_odn2.stl"  # TODO: removeme
        # self.loadSTL(self.openedStl)
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

        # Front-end development at its best
        self.cur_row = 1

        def get_next_row():
            self.cur_row += 1
            return self.cur_row

        def get_cur_row():
            return self.cur_row

        layer_height_label = QLabel(self.locale.LayerHeight)
        self.layer_height_value = QLineEdit("0.2")
        right_panel.addWidget(layer_height_label, get_next_row(), 1)
        right_panel.addWidget(self.layer_height_value, get_cur_row(), 2)

        printSpeed_label = QLabel(self.locale.PrintSpeed)
        self.printSpeed_value = QLineEdit("50")
        right_panel.addWidget(printSpeed_label, get_next_row(), 1)
        right_panel.addWidget(self.printSpeed_value, get_cur_row(), 2)

        printSpeedLayer1_label = QLabel(self.locale.PrintSpeedLayer1)
        self.printSpeedLayer1_value = QLineEdit("50")
        right_panel.addWidget(printSpeedLayer1_label, get_next_row(), 1)
        right_panel.addWidget(self.printSpeedLayer1_value, get_cur_row(), 2)

        printSpeedWall_label = QLabel(self.locale.PrintSpeedWall)
        self.printSpeedWall_value = QLineEdit("50")
        right_panel.addWidget(printSpeedWall_label, get_next_row(), 1)
        right_panel.addWidget(self.printSpeedWall_value, get_cur_row(), 2)

        extruderTemp_label = QLabel(self.locale.ExtruderTemp)
        self.extruderTemp_value = QLineEdit("200")
        right_panel.addWidget(extruderTemp_label, get_next_row(), 1)
        right_panel.addWidget(self.extruderTemp_value, get_cur_row(), 2)

        bedTemp_label = QLabel(self.locale.BedTemp)
        self.bedTemp_value = QLineEdit("60")
        right_panel.addWidget(bedTemp_label, get_next_row(), 1)
        right_panel.addWidget(self.bedTemp_value, get_cur_row(), 2)

        fillDensity_label = QLabel(self.locale.FillDensity)
        self.fillDensity_value = QLineEdit("20")
        right_panel.addWidget(fillDensity_label, get_next_row(), 1)
        right_panel.addWidget(self.fillDensity_value, get_cur_row(), 2)

        wallThickness_label = QLabel(self.locale.WallThickness)
        self.wallThickness_value = QLineEdit("0.8")
        right_panel.addWidget(wallThickness_label, get_next_row(), 1)
        right_panel.addWidget(self.wallThickness_value, get_cur_row(), 2)

        line_width_label = QLabel(self.locale.LineWidth)
        self.line_width_value = QLineEdit("0.4")
        right_panel.addWidget(line_width_label, get_next_row(), 1)
        right_panel.addWidget(self.line_width_value, get_cur_row(), 2)

        filling_type_label = QLabel(self.locale.FillingType)
        right_panel.addWidget(filling_type_label, get_next_row(), 1)
        # todo fix displaying shifting (feature is below)
        right_panel.addWidget(self.line_width_value, get_cur_row(), 2)
        filling_type_valuesW = QWidget()
        self.filling_type_values = QComboBox(filling_type_valuesW)
        self.filling_type_values.addItems(self.locale.FillingTypeValues)
        right_panel.addWidget(filling_type_valuesW, get_cur_row(), 2)

        ### RETRACTION UI ###
        retractionOn_label = QLabel(self.locale.Retraction)
        self.retractionOn_box = QCheckBox()
        right_panel.addWidget(retractionOn_label, get_next_row(), 1)
        right_panel.addWidget(self.retractionOn_box, get_cur_row(), 2)

        retractionDistance_label = QLabel(self.locale.RetractionDistance)
        self.retractionDistance_value = QLineEdit("0")
        right_panel.addWidget(retractionDistance_label, get_next_row(), 1)
        right_panel.addWidget(self.retractionDistance_value, get_cur_row(), 2)

        retractionSpeed_label = QLabel(self.locale.RetractionSpeed)
        self.retractionSpeed_value = QLineEdit("0")
        right_panel.addWidget(retractionSpeed_label, get_next_row(), 1)
        right_panel.addWidget(self.retractionSpeed_value, get_cur_row(), 2)
        ###

        supportOffset_label = QLabel(self.locale.SupportOffset)
        self.supportOffset_value = QLineEdit("1.0")
        right_panel.addWidget(supportOffset_label, get_next_row(), 1)
        right_panel.addWidget(self.supportOffset_value, get_cur_row(), 2)

        skirtLineCount_label = QLabel(self.locale.SkirtLineCount)
        self.skirtLineCount_value = QLineEdit("3")
        right_panel.addWidget(skirtLineCount_label, get_next_row(), 1)
        right_panel.addWidget(self.skirtLineCount_value, get_cur_row(), 2)

        self.fanOffLayer1_box = QCheckBox(self.locale.FanOffLayer1)
        right_panel.addWidget(self.fanOffLayer1_box, get_next_row(), 1)

        self.modelSwitch_box = QCheckBox(self.locale.ShowStl)
        self.modelSwitch_box.stateChanged.connect(self.switchModels)
        right_panel.addWidget(self.modelSwitch_box, get_next_row(), 1)

        self.supportsOn = QCheckBox(self.locale.SupportsOn)
        right_panel.addWidget(self.supportsOn, get_next_row(), 1)

        self.slider_label = QLabel(self.locale.LayersCount)
        self.layersNumber_label = QLabel()
        right_panel.addWidget(self.slider_label, get_next_row(), 1)
        right_panel.addWidget(self.layersNumber_label, get_cur_row(), 2)

        self.pictureSlider = QSlider()
        self.pictureSlider.setOrientation(QtCore.Qt.Horizontal)
        self.pictureSlider.setMinimum(1)
        self.pictureSlider.setValue(1)
        self.pictureSlider.valueChanged.connect(self.changeLayerView)
        right_panel.addWidget(self.pictureSlider, get_next_row(), 1, 1, 2)

        self.xPosition_value = QLineEdit("0")
        right_panel.addWidget(self.xPosition_value, get_next_row(), 1)
        self.yPosition_value = QLineEdit("0")
        right_panel.addWidget(self.yPosition_value, get_cur_row(), 2)
        self.zPosition_value = QLineEdit("0")
        right_panel.addWidget(self.zPosition_value, get_next_row(), 1)
        self.move_button = QPushButton(self.locale.MoveModel)
        self.move_button.clicked.connect(self.moveModel)
        right_panel.addWidget(self.move_button, get_cur_row(), 2, 1, 1)

        loadModel_button = QPushButton(self.locale.OpenModel)
        loadModel_button.clicked.connect(self.openFile)
        right_panel.addWidget(loadModel_button, get_next_row(), 1, 1, 1)

        self.editPlanes_button = QPushButton(self.locale.EditPlanes)
        self.editPlanes_button.clicked.connect(lambda: self.loadSTL(self.openedStl))
        right_panel.addWidget(self.editPlanes_button, get_cur_row(), 2, 1, 1)

        self.slice3a_button = QPushButton(self.locale.Slice3Axes)
        self.slice3a_button.clicked.connect(lambda: self.sliceSTL("3axes"))
        right_panel.addWidget(self.slice3a_button, get_next_row(), 1, 1, 1)

        self.sliceVip_button = QPushButton(self.locale.SliceVip)
        self.sliceVip_button.clicked.connect(lambda: self.sliceSTL("vip"))
        right_panel.addWidget(self.sliceVip_button, get_cur_row(), 2, 1, 1)

        self.saveGCode_button = QPushButton(self.locale.SaveGCode)
        self.saveGCode_button.clicked.connect(self.saveGCodeFile)
        right_panel.addWidget(self.saveGCode_button, get_next_row(), 1, 1, 1)

        self.analyzeModel_button = QPushButton(self.locale.Analyze)
        self.analyzeModel_button.clicked.connect(self.analyzeModel)
        right_panel.addWidget(self.analyzeModel_button, get_cur_row(), 2, 1, 1)

        self.colorizeAngle_value = QLineEdit("30")
        right_panel.addWidget(self.colorizeAngle_value, get_next_row(), 1)

        self.colorModel_button = QPushButton(self.locale.ColorModel)
        self.colorModel_button.clicked.connect(self.colorizeModel)
        right_panel.addWidget(self.colorModel_button, get_cur_row(), 2, 1, 1)

        mygroupbox = QGroupBox('Settings')
        mygroupbox.setLayout(right_panel)
        scroll = QScrollArea()
        scroll.setWidget(mygroupbox)
        scroll.setWidgetResizable(True)
        #scroll.setFixedHeight(400)
        #layout = QVBoxLayout()

        return scroll

    def initBottomPanel(self):

        bottom_layout = QGridLayout()
        bottom_layout.setSpacing(5)
        bottom_layout.setColumnStretch(7, 1)

        self.addPlane_button = QPushButton(self.locale.AddPlane)
        self.addPlane_button.clicked.connect(self.addPlane)
        bottom_layout.addWidget(self.addPlane_button, 1, 0)

        comboW = QWidget()
        self.combo = QComboBox(comboW)
        self.combo.currentIndexChanged.connect(self.changeComboSelect)
        bottom_layout.addWidget(comboW, 0, 0, 1, 2)

        self.removePlane_button = QPushButton(self.locale.DeletePlane)
        self.removePlane_button.clicked.connect(self.removePlane)
        bottom_layout.addWidget(self.removePlane_button, 2, 0)

        self.tilted_checkbox = QCheckBox(self.locale.Tilted)
        self.tilted_checkbox.stateChanged.connect(lambda: self.applySliderChange(self.rotated_value, self.rotSlider))
        bottom_layout.addWidget(self.tilted_checkbox, 0, 3)

        x_label = QLabel("X:")
        bottom_layout.addWidget(x_label, 0, 4)
        self.x_value = QLineEdit("3.0951")
        self.x_value.editingFinished.connect(lambda: self.applyFieldChange(self.x_value, self.xSlider))
        bottom_layout.addWidget(self.x_value, 0, 5)

        y_label = QLabel("Y:")
        bottom_layout.addWidget(y_label, 1, 4)
        self.y_value = QLineEdit("5.5910")
        self.y_value.editingFinished.connect(lambda: self.applyFieldChange(self.y_value, self.ySlider))
        bottom_layout.addWidget(self.y_value, 1, 5)

        z_label = QLabel("Z:")
        bottom_layout.addWidget(z_label, 2, 4)
        self.z_value = QLineEdit("89.5414")
        self.z_value.editingFinished.connect(lambda: self.applyFieldChange(self.z_value, self.zSlider))
        bottom_layout.addWidget(self.z_value, 2, 5)

        rotated_label = QLabel(self.locale.Rotated)
        bottom_layout.addWidget(rotated_label, 3, 4)
        self.rotated_value = QLineEdit("31.0245")
        self.rotated_value.editingFinished.connect(lambda: self.applyFieldChange(self.rotated_value, self.rotSlider))
        bottom_layout.addWidget(self.rotated_value, 3, 5)

        self.xSlider = QSlider()
        self.xSlider.setOrientation(QtCore.Qt.Horizontal)
        self.xSlider.setMinimum(-100)
        self.xSlider.setMaximum(100)
        self.xSlider.setValue(1)
        self.xSlider.valueChanged.connect(lambda: self.applySliderChange(self.x_value, self.xSlider))
        bottom_layout.addWidget(self.xSlider, 0, 6, 1, 2)
        self.ySlider = QSlider()
        self.ySlider.setOrientation(QtCore.Qt.Horizontal)
        self.ySlider.setMinimum(-100)
        self.ySlider.setMaximum(100)
        self.ySlider.setValue(1)
        self.ySlider.valueChanged.connect(lambda: self.applySliderChange(self.y_value, self.ySlider))
        bottom_layout.addWidget(self.ySlider, 1, 6, 1, 2)
        self.zSlider = QSlider()
        self.zSlider.setOrientation(QtCore.Qt.Horizontal)
        self.zSlider.setMinimum(0)
        self.zSlider.setMaximum(200)
        self.zSlider.setValue(1)
        self.zSlider.valueChanged.connect(lambda: self.applySliderChange(self.z_value, self.zSlider))
        bottom_layout.addWidget(self.zSlider, 2, 6, 1, 2)
        self.rotSlider = QSlider()
        self.rotSlider.setOrientation(QtCore.Qt.Horizontal)
        self.rotSlider.setMinimum(-180)
        self.rotSlider.setMaximum(180)
        self.rotSlider.setValue(0)
        self.rotSlider.valueChanged.connect(lambda: self.applySliderChange(self.rotated_value, self.rotSlider))
        bottom_layout.addWidget(self.rotSlider, 3, 6, 1, 2)

        bottom_panel = QWidget()
        bottom_panel.setLayout(bottom_layout)

        return bottom_panel

    def applyFieldChange(self, field, slider):
        if isfloat(field.text()):
            slider.setValue(float(field.text()))
        else:
            field.setText(str(slider.value()))
            showErrorDialog(self.locale.FloatParsingError)
        self.applyPlaneChangeCommon()

    def applySliderChange(self, field, slider):
        field.setText(str(slider.value()))
        self.applyPlaneChangeCommon()

    def applyPlaneChangeCommon(self):
        center = [float(self.x_value.text()), float(self.y_value.text()), float(self.z_value.text())]
        ind = self.combo.currentIndex()
        if ind == -1:
            return
        self.planes[ind] = gui_utils.Plane(self.tilted_checkbox.isChecked(), float(self.rotSlider.value()), center)
        self.drawPlanes()

    def addPlane(self):
        if len(self.planes) == 0:
            self.planes.append(gui_utils.Plane(True, 0, [10, 10, 10]))
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
        if ind == -1:
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
        # if len(self.planes) == 0:
        #    self.bottom_panel.setEnabled(False)
        #    return

        # self.bottom_panel.setEnabled(True)

        self.combo.clear()
        for i in range(len(self.planes)):
            self.combo.addItem("Плоскость " + str(i + 1))

        self.drawPlanes()

        self.changeComboSelect()

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
        if addStl:
            self.render.AddActor(self.stlActor)

        self.rotatePlane(gode.rotations[-1])
        for actor in self.actors:
            self.render.AddActor(actor)

        # self.loadPlanes()
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
        self.xPosition_value.setText(str(self.stlTranslation[0])[:10])
        self.yPosition_value.setText(str(self.stlTranslation[1])[:10])
        self.zPosition_value.setText(str(self.stlTranslation[2])[:10])

        self.clearScene()

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
                # revert prev rotation firstly and then apply current
                tf = gui_utils.prepareTransform(self.gode.rotations[self.gode.lays2rots[block]], currRotation)
                self.actors[block].SetUserTransform(tf)

            self.rotatePlane(currRotation)
            # for i in range(len(self.planes)):
            #     self.rotateAnyPlane(self.planesActors[i], self.planes[i], currRotation)
        self.currLayerNumber = newSliderValue
        self.reloadScene()

    def rotatePlane(self, rotation):
        transform = vtk.vtkTransform()
        transform.PostMultiply()
        transform.Translate(-params.RotationCenter[0], -params.RotationCenter[1], -params.RotationCenter[2])
        transform.PostMultiply()
        transform.RotateZ(rotation.z_rot)
        transform.PostMultiply()
        transform.RotateX(rotation.x_rot)
        transform.PostMultiply()
        transform.Translate(params.RotationCenter[0], params.RotationCenter[1], params.RotationCenter[2])
        self.planeActor.SetUserTransform(transform)
        self.planeTransform = transform

    # def rotateAnyPlane(self, planeActor, plane, rotation):
    #     transform = vtk.vtkTransform()
    #     transform.PostMultiply()
    #     transform.RotateX(-60 if plane.tilted else 0)
    #     transform.PostMultiply()
    #     transform.RotateZ(plane.rot)
    #     transform.Translate(plane.x, plane.y, plane.z - 0.1)
    #
    #     transform.PostMultiply()
    #     transform.RotateZ(rotation.z_rot)
    #     transform.PostMultiply()
    #     transform.RotateX(rotation.x_rot)
    #     planeActor.SetUserTransform(transform)

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

            "layer_height": self.layer_height_value.text(),
            "wall_thickness": self.wallThickness_value.text(),
            "fill_density": self.fillDensity_value.text(),
            "bed_temperature": self.bedTemp_value.text(),
            "extruder_temperature": self.extruderTemp_value.text(),
            "print_speed": self.printSpeed_value.text(),
            "print_speed_layer1": self.printSpeedLayer1_value.text(),
            "print_speed_wall": self.printSpeedWall_value.text(),
            "line_width": self.line_width_value.text(),
            "filling_type": locales.getLocaleByLang("en").FillingTypeValues[self.filling_type_values.currentIndex()],
            "slicing_type": slicing_type,
            "planes_file": params.PlanesFile,
            "angle": self.colorizeAngle_value.text(),
            "retraction_speed": self.retractionSpeed_value.text(),
            "retraction_distance": self.retractionDistance_value.text(),
            "support_offset": self.supportOffset_value.text(),
            "skirt_line_count": self.skirtLineCount_value.text()
        }
        self.savePlanesToFile()

        # Prepare a slicing command line command
        cmd = params.SliceCommand.format(**values)
        if self.fanOffLayer1_box.isChecked():
            cmd += " --fan_off_layer1"
        if self.retractionOn_box.isChecked():
            cmd += " --retraction_on"
        if self.supportsOn.isChecked():
            cmd += " --supports_on"

        call_command(cmd)
        self.stlActor.VisibilityOff()
        self.loadGCode(params.OutputGCode, True)
        #self.debugMe()

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
        call_command(cmd)
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
        call_command(cmd)
        self.planes = gui_utils.read_planes()
        self.bottom_panel.setEnabled(True)
        # self.openedStl = "cuttedSTL.stl"
        self.loadSTL(self.openedStl, method=gui_utils.createStlActorInOrigin)

    def clearScene(self):
        self.render.RemoveAllViewProps()
        self.render.AddActor(self.planeActor)
        for b in self.boxActors:
            self.render.AddActor(b)

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

    def debugMe(self):
        debug.readFile(self.render, "/home/l1va/debug.txt", 4)
        # debug.readFile(self.render, "/home/l1va/debug_simplified.txt", "Red", 3)
        self.reloadScene()


def call_command(cmd):
    try:
        cmds = shlex.split(cmd)
        print(cmds)
        subprocess.check_output(cmds)
    except subprocess.CalledProcessError as er:
        print("Error:", sys.exc_info())
        gui_utils.showErrorDialog(repr(er.output))


def format_path(path):
    if " " in path:
        return '"{}"'.format(path)
    return path
