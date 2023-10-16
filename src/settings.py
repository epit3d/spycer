import os
import sys
import tempfile as tmp
from os import path
import shutil

import yaml
import vtk

_sett = None  # do not forget to load_settings() at start

# setup app path
if getattr(sys, 'frozen', False):
    APP_PATH = path.dirname(sys.executable)
    # uncomment if you want some protection that nothing would be broken
    # if not path.exists(path.join(app_path, settings_filename)):
    #     bundle_path = sys._MEIPASS
    #     shutil.copyfile(path.join(bundle_path, settings_filename), path.join(app_path, settings_filename))
else:
    # have to add .. because settings.py is under src folder
    APP_PATH = path.join(path.dirname(__file__), "..")


def sett():
    return _sett


_colors = {}  # Available colors: https://en.wikipedia.org/wiki/File:SVG_Recognized_color_keyword_names.svg
_vtk_colors = vtk.vtkNamedColors()


def get_color(key):
    if key in _colors:
        return _colors[key]
    val = _vtk_colors.GetColor3d(key)
    _colors[key] = val
    return val


def copy_project_files(project_path: str):
    load_settings()
    global _sett
    _sett.project_path = project_path
    save_settings()

def load_settings(filename=""):
    if not filename:
        print('retrieving settings')
        if getattr(sys, 'frozen', False):
            app_path = path.dirname(sys.executable)
            # uncomment if you want some protection that nothing would be broken
            # if not path.exists(path.join(app_path, settings_filename)):
            #     bundle_path = sys._MEIPASS
            #     shutil.copyfile(path.join(bundle_path, settings_filename), path.join(app_path, settings_filename))
        else:
            # have to add .. because settings.py is under src folder
            app_path = path.join(path.dirname(__file__), "..")

        settings_filename = "settings.yaml"
        filename = path.join(app_path, settings_filename)

    with open(filename) as f:
        data = yaml.safe_load(f)
        global _sett
        _sett = Settings(data)

    print(f'after loading stl_file is {_sett.slicing.stl_file}')


def save_settings(filename=""):
    if not filename:
        if _sett.project_path:
            app_path = _sett.project_path
        elif getattr(sys, 'frozen', False):
            app_path = path.dirname(sys.executable)
        else:
            # have to add .. because settings.py is under src folder
            app_path = path.join(path.dirname(__file__), "..")

        settings_filename = "settings.yaml"
        filename = path.join(app_path, settings_filename)

    temp = yaml.dump(_sett)
    temp = temp.replace("!!python/object:src.settings.Settings", "").strip()
    temp = temp.replace("!!python/object/apply:pathlib.PosixPath", "").strip()

    print(f'saving settings to {filename}')
    with open(filename, 'w') as f:
        f.write(temp)

def save_splanes_to_file(splanes, filename):
    with open(filename, 'w') as out:
        for p in splanes:
            out.write(p.toFile() + '\n')

def get_version(settings_filename):
    try:
        with open(settings_filename, "r") as settings_file:
            settings = yaml.safe_load(settings_file)

        version = settings["common"]["version"]
        return version
    except Exception as e:
        print("Error reading version")
        return ""

def paths_transfer_in_settings(initial_settings_filename, final_settings_filename):
    with open(initial_settings_filename, "r") as settings_file:
        initial_settings = yaml.safe_load(settings_file)

    with open(final_settings_filename, "r") as settings_file:
        final_settings = yaml.safe_load(settings_file)

        for k, v in initial_settings.items():
            if k in final_settings:
                final_settings[k] = v

        with open(final_settings_filename, "w") as settings_file:
            yaml.dump(final_settings, settings_file, default_flow_style=False)

class Settings(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a,
                        [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)

class PathBuilder:
    # class to build paths to files and folders

    @staticmethod
    def project_path():
        return sett().project_path
    
    @staticmethod
    def stl_model():
        return path.join(PathBuilder.project_path(), "model.stl")
    
    @staticmethod
    def splanes_file():
        return path.join(PathBuilder.project_path(), "planes.txt")
    
    @staticmethod
    def settings_file():
        return path.join(PathBuilder.project_path(), "settings.yaml")
    
    @staticmethod
    def settings_file_default():
        return "settings.yaml"

    @staticmethod
    def settings_file_old():
        return path.join(PathBuilder.project_path(), "settings_old.yaml")

    @staticmethod
    def colorizer_cmd():
        return sett().colorizer.cmd + f'"{PathBuilder.settings_file()}"'
    
    @staticmethod
    def colorizer_stl():
        return path.join(PathBuilder.project_path(), sett().colorizer.copy_stl_file)
    
    @staticmethod
    def colorizer_result():
        return path.join(PathBuilder.project_path(), sett().colorizer.result)
    
    @staticmethod
    def slicing_cmd():
        return sett().slicing.cmd + f'"{PathBuilder.settings_file()}"'
    
    @staticmethod
    def gcodevis_file():
        return path.join(PathBuilder.project_path(), sett().slicing.gcode_file_without_calibration)
    
    @staticmethod
    def gcode_file():
        return path.join(PathBuilder.project_path(), sett().slicing.gcode_file)
    
    @staticmethod
    def printer_dir():
        return sett().hardware.printer_dir

    @staticmethod
    def calibration_file():
        return path.join(PathBuilder.printer_dir(), sett().hardware.calibration_file)