import os
import sys
import tempfile as tmp
from os import path
from PyQt5.QtCore import QSettings
import shutil
import pathlib
import base64
import logging

import yaml
import vtk


class SettingsManager:
    """Encapsulates loading, saving and accessing application settings."""

    def __init__(self, settings=None):
        self._sett = settings

    @property
    def settings(self):
        return self._sett

    def load(self, filename=""):
        old_setts = self._sett
        data = read_settings(filename)
        if data is not None:
            logging.debug("Settings loaded")
            self._sett = Settings(data)

        if old_setts is not None and not old_setts.has_same_attributes(self._sett):
            self._sett = old_setts
            raise Exception("Check the settings file")

        return self._sett

    def save(self, filename=""):
        if not filename:
            if self._sett and getattr(self._sett, "project_path", None):
                app_path = self._sett.project_path
            elif getattr(sys, "frozen", False):
                app_path = path.dirname(sys.executable)
            else:
                app_path = path.join(path.dirname(__file__), "..")

            filename = path.join(app_path, "settings.yaml")

        temp = prepare_temp_settings(self._sett)

        logging.info("saving settings to %s", filename)
        with open(filename, "w") as f:
            f.write(temp)


# default singleton used across the application
settings_manager = SettingsManager()


def sett():
    return settings_manager.settings


def load_settings(filename=""):
    return settings_manager.load(filename)


def save_settings(filename=""):
    return settings_manager.save(filename)

# setup app path
if getattr(sys, "frozen", False):
    APP_PATH = path.dirname(sys.executable)
    # uncomment if you want some protection that nothing would be broken
    # if not path.exists(path.join(app_path, settings_filename)):
    #     bundle_path = sys._MEIPASS
    #     shutil.copyfile(path.join(bundle_path, settings_filename), path.join(app_path, settings_filename))
else:
    # have to add .. because settings.py is under src folder
    APP_PATH = path.join(path.dirname(__file__), "..")


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
    s = sett()
    s.project_path = project_path
    s.slicing.stl_file = ""
    save_settings()


def project_change_check():
    logging.debug("Checking project change")
    save_settings("vip")
    saved_settings = Settings(
        read_settings(str(pathlib.Path(sett().project_path, "settings.yaml")))
    )
    logging.debug("Saved settings:")
    logging.debug(saved_settings)
    logging.debug("Current settings:")
    logging.debug(sett())
    if sett() != saved_settings:
        logging.debug("Saved settings do not match current settings.")
        return False
    if not compare_project_file("model.stl"):
        logging.debug("Saved model.stl does not match current model.stl.")
        return False
    if not compare_figures(saved_settings):
        logging.debug("Saved figures do not match current figures.")
        return False

    return True


def compare_figures(settings):
    current_figures = getattr(sett(), "figures")
    if hasattr(settings, "figures"):
        figures_from_settings = getattr(settings, "figures")
    else:
        figures_from_settings = []

    if len(current_figures) != len(figures_from_settings):
        logging.debug("Number of figures does not match")
        return False

    for i in range(len(current_figures)):
        if current_figures[i]["description"] != figures_from_settings[i].description:
            logging.debug(f"Description of figure {i} does not match")
            return False

        if current_figures[i]["settings"] != figures_from_settings[i].settings:
            logging.debug(f"Settings of figure {i} does not match")
            return False

    return True


def compare_project_file(filename):
    filename = pathlib.Path(sett().project_path, filename)
    filename_temp = get_temp_path(filename)
    return compare_files(filename, filename_temp)


def compare_files(file1_path, file2_path):
    # if either of the files does not exist, return False
    if not os.path.exists(file1_path) or not os.path.exists(file2_path):
        return True

    try:
        with open(file1_path, "rb") as file1:
            data1 = file1.read()
        with open(file2_path, "rb") as file2:
            data2 = file2.read()

        if data1 == data2:
            return True
        else:
            return False

    except FileNotFoundError:
        logging.error("Error during file comparison!")
        return True


def create_temporary_project_files():
    create_temporary_project_file("settings.yaml")
    sett().slicing.stl_file = create_temporary_project_file("model.stl")


def create_temporary_project_file(filename):
    filename_temp = get_temp_path(filename)
    filename_path = str(pathlib.Path(sett().project_path, filename))

    if os.path.exists(filename_path):
        filename_temp_path = str(pathlib.Path(sett().project_path, filename_temp))
        shutil.copy(filename_path, filename_temp_path)
        return filename_temp
    else:
        return ""


def get_temp_path(filename):
    basename, extension = os.path.splitext(filename)
    filename_temp = basename + "_temp" + extension
    return filename_temp


def delete_temporary_project_files(project_path=""):
    delete_project_file("settings_temp.yaml", project_path)
    delete_project_file("model_temp.stl", project_path)


def delete_project_file(filename, project_path=""):
    if project_path == "":
        project_path = sett().project_path

    filename_path = str(pathlib.Path(project_path, filename))
    if os.path.exists(filename_path):
        os.remove(filename_path)


def get_recent_projects():
    settings = QSettings("Epit3D", "Spycer")

    recent_projects = list()

    if settings.contains("recent_projects"):
        recent_projects = settings.value("recent_projects", type=list)

        # filter projects which do not exist
        import pathlib

        recent_projects = [p for p in recent_projects if pathlib.Path(p).exists()]

    return recent_projects


def save_recent_projects(recent_projects):
    settings = QSettings("Epit3D", "Spycer")
    settings.setValue("recent_projects", recent_projects)


def update_last_open_project(recent_projects, project_path):
    project_path = str(project_path)
    # adds recent project to system settings
    if project_path in recent_projects:
        # move the project to the beginning of the list
        move_project_to_top(recent_projects, project_path)
    else:
        # add new project to recent projects
        add_recent_project(recent_projects, project_path)


def move_project_to_top(recent_projects, project_path):
    last_opened_project_index = recent_projects.index(project_path)
    last_opened_project = recent_projects.pop(last_opened_project_index)
    recent_projects.insert(0, last_opened_project)
    save_recent_projects(recent_projects)


def add_recent_project(recent_projects, project_path):
    recent_projects.insert(0, str(project_path))
    save_recent_projects(recent_projects)


def read_settings(filename=""):
    if not filename:
        logging.debug("retrieving settings")
        if getattr(sys, "frozen", False):
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

        # right now let's check that some fields are just None,
        # just because they were not found in the new template
        def check_children(obj):
            for key, value in obj.items():
                if isinstance(value, dict):
                    check_children(value)
                elif value is None:
                    logging.debug(f"Value of {key} is None")

        check_children(data)

    return data

    return None


def prepare_temp_settings(settings):
    temp = yaml.dump(settings)
    temp = temp.replace("!!python/object:src.settings.Settings", "").strip()
    temp = temp.replace("!!python/object/apply:pathlib.PosixPath", "").strip()

    return temp


def save_splanes_to_file(splanes, filename):
    with open(filename, "w") as out:
        for p in splanes:
            out.write(p.toFile() + "\n")


def get_version(settings_filename):
    try:
        with open(settings_filename, "r") as settings_file:
            settings = yaml.full_load(settings_file)

        version = settings["common"]["version"]
        return version
    except Exception as e:
        logging.error("Error reading version")
        return ""


def set_version(settings_filename, version):
    try:
        with open(settings_filename, "r") as settings_file:
            settings = yaml.full_load(settings_file)

        settings["common"]["version"] = version

        with open(settings_filename, "w") as settings_file:
            yaml.dump(settings, settings_file, default_flow_style=False)

    except Exception as e:
        logging.error("Error writing version")


def paths_transfer_in_settings(initial_settings_filename, final_settings_filename):
    with open(initial_settings_filename, "r") as settings_file:
        initial_settings = yaml.full_load(settings_file)

    with open(final_settings_filename, "r") as settings_file:
        final_settings = yaml.full_load(settings_file)

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
                setattr(self, a, [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)

    def __repr__(self):
        return str(self.__dict__)

    def __eq__(self, other):
        if not isinstance(other, Settings):
            return False
        ignore_attributes = [
            "splanes_file",
            "figures",
            "project_path",
            "print_time",
            "consumption_material",
            "planes_contact_with_nozzle",
            # for some reason this is temporary field that is not being updated well
            "stl_file",
            "printer_dir",
        ]

        # try to compare attributes from left to right
        for attr in self.__dict__:
            if attr in ignore_attributes:
                continue
            if not hasattr(other, attr):
                logging.debug(f"Attribute {attr} not found in other")
                return False
            if getattr(self, attr) != getattr(other, attr):
                logging.debug(f"Attribute {attr} does not match")
                return False

        # try to compare attributes from right to left
        for attr in other.__dict__:
            if attr in ignore_attributes:
                continue
            if not hasattr(self, attr):
                logging.debug(f"Attribute {attr} not found in self")
                return False
            if getattr(self, attr) != getattr(other, attr):
                logging.debug(f"Attribute {attr} does not match")
                return False

        return True

    def has_same_attributes(self, other):
        if not isinstance(other, Settings):
            return False

        ignore_attributes = [
            "printer_dir",
            "project_path",
            "splanes_file",
            "figures",
            "print_time",
            "consumption_material",
            "planes_contact_with_nozzle",
            "version",
        ]

        # try to compare attributes from left to right
        for attr in self.__dict__:
            if attr in ignore_attributes:
                continue
            if not hasattr(other, attr):
                logging.warning("Attribute %s not found in other", attr)
                return False

        # try to compare attributes from right to left
        for attr in other.__dict__:
            if attr in ignore_attributes:
                continue
            if not hasattr(self, attr):
                logging.warning("Attribute %s not found in self", attr)
                return False

        return True


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
    def settings_file():
        return path.join(PathBuilder.project_path(), "settings.yaml")

    @staticmethod
    def settings_file_temp():
        return path.join(PathBuilder.project_path(), "settings_temp.yaml")

    @staticmethod
    def settings_file_default():
        return "settings.yaml"

    @staticmethod
    def settings_file_old():
        return path.join(PathBuilder.project_path(), "settings_old.yaml")

    @staticmethod
    def get_cmd_with_path(cmd):
        temp_settings = prepare_temp_settings(sett())
        encoded_temp_settings = base64.b64encode(temp_settings.encode("utf-8")).decode(
            "utf-8"
        )
        return (
            cmd
            + f'"{PathBuilder.settings_file_temp()}"'
            + " --data="
            + f"{encoded_temp_settings}"
        )

    @staticmethod
    def colorizer_cmd():
        return PathBuilder.get_cmd_with_path(sett().colorizer.cmd)

    @staticmethod
    def colorizer_stl():
        return path.join(PathBuilder.project_path(), sett().colorizer.copy_stl_file)

    @staticmethod
    def colorizer_result():
        return path.join(PathBuilder.project_path(), sett().colorizer.result)

    @staticmethod
    def slicing_cmd():
        return PathBuilder.get_cmd_with_path(sett().slicing.cmd)

    @staticmethod
    def gcodevis_file():
        return path.join(
            PathBuilder.project_path(), sett().slicing.gcode_file_without_calibration
        )

    @staticmethod
    def gcode_file():
        return path.join(PathBuilder.project_path(), sett().slicing.gcode_file)

    @staticmethod
    def printer_dir():
        return sett().hardware.printer_dir

    @staticmethod
    def calibration_file():
        return path.join(PathBuilder.printer_dir(), sett().hardware.calibration_file)
