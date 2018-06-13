import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QTextEdit, QGridLayout, QSlider, QCheckBox, QPushButton,
                             QApplication, QFileDialog)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import gcode


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
        colors = vtk.vtkNamedColors()
        self.render = vtk.vtkRenderer()
        self.render.SetBackground(colors.GetColor3d("SlateGray"))
        widget3d.GetRenderWindow().AddRenderer(self.render)
        self.interactor = widget3d.GetRenderWindow().GetInteractor()
        self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()

        self.axesWidget = vtk.vtkOrientationMarkerWidget()
        rgba = [0] * 4
        colors.GetColor("Carrot", rgba)
        self.axesWidget.SetOutlineColor(rgba[0], rgba[1], rgba[2])
        self.axesWidget.SetOrientationMarker(vtk.vtkAxesActor())
        self.axesWidget.SetInteractor(self.interactor)
        self.axesWidget.SetViewport(0.0, 0.0, 0.3, 0.3)
        self.axesWidget.SetEnabled(1)
        self.axesWidget.InteractiveOff()

        grid.addWidget(widget3d, 1, 0, 20, 1)

        # thickness = kingpin.Flag("thickness", "Set the slice thickness.").Short('t').Default("0.2").Float64()
        layerWidth_label = QLabel('Толщина слоя, мм:')
        self.layerWidth_value = QLineEdit("0.2")
        grid.addWidget(layerWidth_label, 3, 1)
        grid.addWidget(self.layerWidth_value, 3, 2)

        # travelSpeed = kingpin.Flag("travel_speed", "Printing travel speed.").Default("9000").Int()
        travelSpeed_label = QLabel('Скорость движения, мм/с:')
        self.travelSpeed_value = QLineEdit("1")  # TODO: set default
        grid.addWidget(travelSpeed_label, 4, 1)
        grid.addWidget(self.travelSpeed_value, 4, 2)

        # extruderTemperature = kingpin.Flag("extruder_temperature", "Extruder temperature in Celsius.").Default(
        #   "200").Int()
        printTemp_label = QLabel(
            "<html><head/><body><p>Температура печати, <span style=\" vertical-align:super;\">о</span>С:</p></body></html>")
        self.printTemp_value = QLineEdit("200")
        grid.addWidget(printTemp_label, 5, 1)
        grid.addWidget(self.printTemp_value, 5, 2)

        # bedTemperature = kingpin.Flag("bed_temperature", "Bed temperature in Celsius.").Default("60").Int()
        bedTemp_label = QLabel(
            "<html><head/><body><p>Температура стола, <span style=\" vertical-align:super;\">о</span>С:</p></body></html>")
        self.bedTemp_value = QLineEdit("60")
        grid.addWidget(bedTemp_label, 6, 1)
        grid.addWidget(self.bedTemp_value, 6, 2)

        # fillDensity = kingpin.Flag("fill_density", "Fill density in percents.").Default("20").Int()
        fillDensity_label = QLabel('Плотность заполнения, %:')
        self.fillDensity_value = QLineEdit("20")
        grid.addWidget(fillDensity_label, 7, 1)
        grid.addWidget(self.fillDensity_value, 7, 2)

        # wallThickness = kingpin.Flag("wall_thickness", "Set the wall thickness.").Default("0.4").Float64()
        wallThickness_label = QLabel('Толщина стенок, мм:')
        self.wallThickness_value = QLineEdit("0.8")
        grid.addWidget(wallThickness_label, 8, 1)
        grid.addWidget(self.wallThickness_value, 8, 2)

        self.setLayout(grid)


    def loadGCode(self, filename):
        gcd = gcode.readGCode(filename)
        actors = gcode.wrapWithActors(gcd)

        self.clearScene()
        for actor in actors:
            self.render.AddActor(actor)
        self.reloadScene()

    def clearScene(self):
        self.render.RemoveAllViewProps()

    def reloadScene(self):
        self.render.ResetCamera()
        self.render.Modified()
        self.interactor.Render()