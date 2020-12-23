import os
import shlex
import subprocess
import sys
from pathlib import Path

from shutil import copy2

import vtk
from PyQt5 import QtCore
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QTabWidget, QLineEdit, QComboBox, QGridLayout, QSlider, QCheckBox,
                             QPushButton, QFileDialog, QScrollArea, QGroupBox)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

import params
from src import debug, gcode, locales, gui_utils
from src.gui_utils import isfloat, showErrorDialog




class Gui(QWidget):
    def __init__(self):
        super().__init__()


























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



    def savePlanesToFile(self):
        with open(params.PlanesFile, 'w') as out:
            for p in self.planes:
                out.write(p.toFile() + '\n')











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
