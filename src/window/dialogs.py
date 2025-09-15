"""Dialog helpers for :mod:`src.window`."""
import os
import os.path as path
from PyQt5.QtWidgets import QFileDialog

from src.settings import sett


def _base_dir():
    base_dir = getattr(sett(), "project_path", "") or os.getcwd()
    if not base_dir or not path.isdir(base_dir):
        base_dir = path.expanduser("~")
    return base_dir


def save_dialog(parent, caption, format="STL (*.stl *.STL);;Gcode (*.gcode)", directory=""):
    base_dir = _base_dir()
    if directory:
        directory = directory if path.isabs(directory) else path.join(base_dir, directory)
    else:
        directory = base_dir
    return QFileDialog.getSaveFileName(parent, caption, directory, format)[0]


def open_dialog(parent, caption, format="STL (*.stl *.STL);;Gcode (*.gcode)", directory=""):
    base_dir = _base_dir()
    if directory:
        directory = directory if path.isabs(directory) else path.join(base_dir, directory)
    else:
        directory = base_dir
    return QFileDialog.getOpenFileName(parent, caption, directory, format)[0]
