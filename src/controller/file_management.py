"""File-related controller mixins."""

import os
import shutil
from os import path
from pathlib import Path
from shutil import copy2
import logging

from PyQt5.QtWidgets import QFileDialog, QMessageBox

from src import gui_utils, locales
from src.gui_utils import showErrorDialog
from src.process import Process
from src.settings import (
    sett,
    load_settings,
    PathBuilder,
    create_temporary_project_files,
    update_last_open_project,
    get_recent_projects,
    delete_temporary_project_files,
)

logger = logging.getLogger(__name__)


class FileManagementMixin:
    """Encapsulates file handling logic for controllers."""

    # Methods below are copied from the legacy ``MainController``
    # to isolate responsibilities.
    def open_file(self):
        try:
            filename = str(self.view.open_dialog(self.view.locale.OpenModel))
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".STL":
                    self.reset_settings()
                    s = sett()
                    stl_full_path = PathBuilder.stl_model_temp()
                    shutil.copyfile(filename, stl_full_path)
                    s.slicing.stl_filename = path.basename(filename)
                    s.slicing.stl_file = path.basename(stl_full_path)
                    self.save_settings("vip")
                    self.update_interface(filename)
                    self.view.model_centering_box.setChecked(False)
                    if os.path.isfile(s.colorizer.copy_stl_file):
                        os.remove(s.colorizer.copy_stl_file)
                    self.load_stl(stl_full_path)
                elif file_ext == ".GCODE":
                    s = sett()
                    self.save_settings("vip")
                    self.load_gcode(filename, False)
                    self.update_interface(filename)
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def save_gcode_file(self):
        try:
            name = str(self.view.save_gcode_dialog())
            if name != "":
                if not name.endswith(".gcode"):
                    name += ".gcode"
                copy2(PathBuilder.gcode_file(), name)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def save_settings_file(self):
        try:
            directory = (
                "Settings_" + os.path.basename(sett().slicing.stl_file).split(".")[0]
            )
            filename = str(
                self.view.save_dialog(
                    self.view.locale.SaveSettings, "YAML (*.yaml *.YAML)", directory
                )
            )
            if filename != "":
                if not (filename.endswith(".yaml") or filename.endswith(".YAML")):
                    filename += ".yaml"
                self.save_settings("vip", filename)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def save_project_files(self, save_path=""):
        if save_path == "":
            self.save_settings("vip", PathBuilder.settings_file())
            if os.path.isfile(PathBuilder.stl_model_temp()):
                shutil.copy2(PathBuilder.stl_model_temp(), PathBuilder.stl_model())
        else:
            self.save_settings("vip", path.join(save_path, "settings.yaml"))
            if os.path.isfile(PathBuilder.stl_model_temp()):
                shutil.copy2(
                    PathBuilder.stl_model_temp(), path.join(save_path, "model.stl")
                )

    def save_project(self):
        try:
            self.save_project_files()
            create_temporary_project_files()
            self.successful_saving_project()
        except IOError as e:
            showErrorDialog("Error during project saving: " + str(e))

    def save_project_as(self):
        project_path = PathBuilder.project_path()
        try:
            save_directory = str(
                QFileDialog.getExistingDirectory(
                    self.view, locales.getLocale().SavingProject
                )
            )
            if not save_directory:
                return
            self.save_project_files(save_directory)
            sett().project_path = save_directory
            self.save_settings("vip", PathBuilder.settings_file())
            create_temporary_project_files()
            delete_temporary_project_files(project_path)
            recent_projects = get_recent_projects()
            update_last_open_project(recent_projects, save_directory)
            self.successful_saving_project()
        except IOError as e:
            sett().project_path = project_path
            self.save_settings("vip")
            showErrorDialog("Error during project saving: " + str(e))

    def successful_saving_project(self):
        message_box = QMessageBox(parent=self.view)
        message_box.setWindowTitle(locales.getLocale().SavingProject)
        message_box.setText(locales.getLocale().ProjectSaved)
        message_box.setIcon(QMessageBox.Information)
        message_box.exec_()

    def load_settings_file(self):
        try:
            filename = str(
                self.view.open_dialog(
                    self.view.locale.LoadSettings, "YAML (*.yaml *.YAML)"
                )
            )
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".YAML":
                    try:
                        old_project_path = sett().project_path
                        load_settings(filename)
                        sett().project_path = old_project_path
                        self.display_settings()
                    except Exception as e:
                        showErrorDialog("Error during reading settings file: " + str(e))
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def display_settings(self):
        self.view.setts.reload()

    def colorize_model(self):
        shutil.copyfile(PathBuilder.stl_model_temp(), PathBuilder.colorizer_stl())
        self.save_settings("vip", PathBuilder.settings_file_temp())
        p = Process(PathBuilder.colorizer_cmd()).wait()
        if p.returncode:
            logging.error(f"error: <{p.stdout}>")
            gui_utils.showErrorDialog(p.stdout)
            return
        lastMove = self.view.stlActor.lastMove
        self.load_stl(PathBuilder.colorizer_stl(), colorize=True)
        self.view.stlActor.lastMove = lastMove
