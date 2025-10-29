from pathlib import Path
from typing import Any
import sys
from PyQt5.QtCore import QSettings
import shutil
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

    def load(self, filename: Path | str | None = None):
        old_setts = self._sett
        data = read_settings(filename)
        if data is not None:
            logging.debug("Settings loaded")
            self._sett = Settings(data)

        if old_setts is not None and not old_setts.has_same_attributes(self._sett):
            self._sett = old_setts
            raise Exception("Check the settings file")

        return self._sett

    def save(self, filename: Path | str | None = None):
        if not filename:
            if self._sett and getattr(self._sett, "project_path", None):
                app_path = Path(self._sett.project_path)
            elif getattr(sys, "frozen", False):
                app_path = Path(sys.executable).parent
            else:
                app_path = Path(__file__).resolve().parent.parent

            filename = app_path / "settings.yaml"
        else:
            filename = Path(filename)

        temp = prepare_temp_settings(self._sett)

        logging.info("saving settings to %s", filename)
        with filename.open("w") as f:
            f.write(temp)


# default singleton used across the application
settings_manager = SettingsManager()


def sett():
    return settings_manager.settings


def load_settings(filename: Path | str | None = None):
    return settings_manager.load(filename)


def save_settings(filename: Path | str | None = None):
    return settings_manager.save(filename)


# setup app path
if getattr(sys, "frozen", False):
    APP_PATH = Path(sys.executable).parent
    # uncomment if you want some protection that nothing would be broken
    # if not (app_path / settings_filename).exists():
    #     bundle_path = sys._MEIPASS
    #     shutil.copyfile(Path(bundle_path, settings_filename), app_path / settings_filename)
else:
    # have to add .. because settings.py is under src folder
    APP_PATH = Path(__file__).resolve().parent.parent


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
        read_settings(Path(sett().project_path) / "settings.yaml")
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
    filename = Path(sett().project_path) / filename
    filename_temp = get_temp_path(filename)
    return compare_files(filename, filename_temp)


def compare_files(file1_path: Path | str, file2_path: Path | str) -> bool:
    path1 = Path(file1_path) if file1_path else None
    path2 = Path(file2_path) if file2_path else None

    # return False if either path is missing or the file does not exist
    if not path1 or not path2:
        return False
    if not path1.exists() or not path2.exists():
        return False

    try:
        with path1.open("rb") as file1:
            data1 = file1.read()
        with path2.open("rb") as file2:
            data2 = file2.read()

        return data1 == data2

    except FileNotFoundError:
        logging.error("Error during file comparison!")
        return False


def create_temporary_project_files():
    create_temporary_project_file("settings.yaml")
    sett().slicing.stl_file = create_temporary_project_file("model.stl")


def create_temporary_project_file(filename):
    filename_temp = get_temp_path(filename)
    filename_path = Path(sett().project_path) / filename

    if filename_path.exists():
        filename_temp_path = Path(sett().project_path) / filename_temp
        shutil.copy(filename_path, filename_temp_path)
        return str(filename_temp)
    return ""


def get_temp_path(filename):
    p = Path(filename)
    return p.with_name(f"{p.stem}_temp{p.suffix}")


def delete_temporary_project_files(project_path=""):
    delete_project_file("settings_temp.yaml", project_path)
    delete_project_file("model_temp.stl", project_path)


def delete_project_file(filename, project_path=""):
    if project_path == "":
        project_path = sett().project_path

    filename_path = Path(project_path) / filename
    if filename_path.exists():
        filename_path.unlink()


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


def read_settings(filename: Path | str | None = None):
    if not filename:
        logging.debug("retrieving settings")
        if getattr(sys, "frozen", False):
            app_path = Path(sys.executable).parent
            # uncomment if you want some protection that nothing would be broken
            # if not (app_path / settings_filename).exists():
            #     bundle_path = sys._MEIPASS
            #     shutil.copyfile(Path(bundle_path, settings_filename), app_path / settings_filename)
        else:
            # have to add .. because settings.py is under src folder
            app_path = Path(__file__).resolve().parent.parent

        settings_filename = "settings.yaml"
        filename = app_path / settings_filename
    else:
        filename = Path(filename)

    with filename.open() as f:
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


def to_plain_data(value: Any):
    """Convert ``Settings`` instances and nested structures to plain Python data."""

    if isinstance(value, Settings):
        return {key: to_plain_data(val) for key, val in value.__dict__.items()}
    if isinstance(value, dict):
        return {key: to_plain_data(val) for key, val in value.items()}
    if isinstance(value, list):
        return [to_plain_data(item) for item in value]
    if isinstance(value, tuple):
        return [to_plain_data(item) for item in value]
    if isinstance(value, Path):
        return str(value)

    return value


def prepare_temp_settings(settings):
    plain_settings = to_plain_data(settings) if settings is not None else {}

    return yaml.safe_dump(plain_settings, sort_keys=False)


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
    except Exception:
        logging.error("Error reading version")
        return ""


def set_version(settings_filename, version):
    try:
        with open(settings_filename, "r") as settings_file:
            settings = yaml.full_load(settings_file)

        settings["common"]["version"] = version

        with open(settings_filename, "w") as settings_file:
            yaml.dump(settings, settings_file, default_flow_style=False)

    except Exception:
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
                if initial_settings[key] is not None:
                    final_settings[key] = initial_settings[key]


class Settings(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)

    def to_dict(self):
        return to_plain_data(self)

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
        return Path(sett().project_path)

    @staticmethod
    def stl_model():
        return PathBuilder.project_path() / "model.stl"

    @staticmethod
    def stl_model_temp():
        return PathBuilder.project_path() / "model_temp.stl"

    @staticmethod
    def settings_file():
        return PathBuilder.project_path() / "settings.yaml"

    @staticmethod
    def settings_file_temp():
        return PathBuilder.project_path() / "settings_temp.yaml"

    @staticmethod
    def settings_file_default():
        return Path("settings.yaml")

    @staticmethod
    def settings_file_old():
        return PathBuilder.project_path() / "settings_old.yaml"

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
        return PathBuilder.project_path() / sett().colorizer.copy_stl_file

    @staticmethod
    def colorizer_result():
        return PathBuilder.project_path() / sett().colorizer.result

    @staticmethod
    def slicing_cmd():
        return PathBuilder.get_cmd_with_path(sett().slicing.cmd)

    @staticmethod
    def gcodevis_file():
        return (
            PathBuilder.project_path() / sett().slicing.gcode_file_without_calibration
        )

    @staticmethod
    def gcode_file():
        return PathBuilder.project_path() / sett().slicing.gcode_file

    @staticmethod
    def printer_dir():
        return Path(sett().hardware.printer_dir)

    @staticmethod
    def calibration_file():
        return PathBuilder.printer_dir() / sett().hardware.calibration_file
