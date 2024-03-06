import os
import sys
import tempfile as tmp
from os import path
import shutil
import pathlib

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

def get_color_rgb(color_name):
    color_rgba = get_color(color_name)

    r = int(color_rgba[0] * 255)
    g = int(color_rgba[1] * 255)
    b = int(color_rgba[2] * 255)

    rgb = (r, g, b)

    return rgb

def copy_project_files(project_path: str):
    load_settings()
    global _sett
    _sett.project_path = project_path
    save_settings()

def project_change_check():
    save_settings("vip")
    saved_settings = Settings(read_settings(str(pathlib.Path(sett().project_path, "settings.yaml"))))
    if sett() != saved_settings:
        return False
    if not compare_project_file("model.stl"):
        return False
    if not compare_project_file("planes.txt"):
        return False

    return True

def compare_project_file(filename):
    filename = pathlib.Path(sett().project_path, filename)
    filename_temp = get_temp_path(filename)
    return compare_files(filename, filename_temp)

def compare_files(file1_path, file2_path):
    try:
        with open(file1_path, 'r', encoding='utf-8') as file1:
            data1 = file1.read()
        with open(file2_path, 'r', encoding='utf-8') as file2:
            data2 = file2.read()
        
        if data1 == data2:
            return True
        else:
            return False

    except FileNotFoundError:
        print("Error during file comparison!")
        return True

def create_temporary_project_files():
    create_temporary_project_file("settings.yaml")
    sett().slicing.stl_file = create_temporary_project_file("model.stl")
    sett().slicing.splanes_file = create_temporary_project_file("planes.txt")

def create_temporary_project_file(filename):
    filename_temp = get_temp_path(filename)
    filename_path = str(pathlib.Path(sett().project_path, filename))

    if os.path.exists(filename_path):
        model_temp_path = str(pathlib.Path(sett().project_path, filename_temp))
        shutil.copy(filename_path, model_temp_path)
        return filename_temp
    else:
        return ""

def overwrite_project_file(filename):
    filename_path = str(pathlib.Path(sett().project_path, filename))
    filename_temp = get_temp_path(filename)
    filename_temp_path = str(pathlib.Path(sett().project_path, filename_temp))

    if os.path.exists(filename_path) and os.path.exists(filename_temp_path):
        os.remove(filename_path)
        os.rename(filename_temp_path, filename_path)

def get_temp_path(filename):
    basename, extension = os.path.splitext(filename)
    filename_temp = basename + "_temp" + extension
    return filename_temp

def delete_project_files():
    delete_project_file("settings_temp.yaml")
    delete_project_file("model_temp.stl")
    delete_project_file("planes_temp.txt")

def delete_project_file(filename):
    filename_path = str(pathlib.Path(sett().project_path, filename))
    if os.path.exists(filename_path):
        os.remove(filename_path)

def load_settings(filename=""):
    data = read_settings(filename)
    if data != None:
        global _sett
        _sett = Settings(data)

    print(f'after loading stl_file is {_sett.slicing.stl_file}')

def read_settings(filename=""):
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
        return data

    return None

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

    temp = prepare_temp_settings(_sett)

    print(f'saving settings to {filename}')
    with open(filename, 'w') as f:
        f.write(temp)

def prepare_temp_settings(_sett):
    temp = yaml.dump(_sett)
    temp = temp.replace("!!python/object:src.settings.Settings", "").strip()
    temp = temp.replace("!!python/object/apply:pathlib.PosixPath", "").strip()

    return temp

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

def set_version(settings_filename, version):
    try:
        with open(settings_filename, "r") as settings_file:
            settings = yaml.safe_load(settings_file)

        settings["common"]["version"] = version

        with open(settings_filename, "w") as settings_file:
            yaml.dump(settings, settings_file, default_flow_style=False)

    except Exception as e:
        print("Error writing version")

def paths_transfer_in_settings(initial_settings_filename, final_settings_filename):
    with open(initial_settings_filename, "r") as settings_file:
        initial_settings = yaml.safe_load(settings_file)

    with open(final_settings_filename, "r") as settings_file:
        final_settings = yaml.safe_load(settings_file)

        compare_settings(initial_settings, final_settings)

        with open(final_settings_filename, "w") as settings_file:
            yaml.dump(final_settings, settings_file, default_flow_style=False)

def compare_settings(initial_settings, final_settings):
    for key in set(final_settings):
        if key in initial_settings:
            if isinstance(final_settings[key], dict):
                compare_settings(initial_settings[key], final_settings[key])
            else:
                if not initial_settings[key] is None:
                    final_settings[key] = initial_settings[key]

class Settings(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a,
                        [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)

    def __eq__(self, other):
        if not isinstance(other, Settings):
            return False
        ignore_attributes = ['splanes_file']
        return all(getattr(self, attr) == getattr(other, attr) for attr in self.__dict__ if attr not in ignore_attributes)

class PathBuilder:
    # class to build paths to files and folders

    @staticmethod
    def project_path():
        return sett().project_path
    
    @staticmethod
    def stl_model():
        return path.join(PathBuilder.project_path(), "model.stl")
    
    @staticmethod
    def stl_model_temp():
        return path.join(PathBuilder.project_path(), "model_temp.stl")

    @staticmethod
    def splanes_file():
        return path.join(PathBuilder.project_path(), "planes.txt")
    
    @staticmethod
    def splanes_file_temp():
        return path.join(PathBuilder.project_path(), "planes_temp.txt")

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