import logging
import math
import os
from os import path
import subprocess
import time
import sys
from functools import partial
from pathlib import Path
import shutil
from shutil import copy2
from typing import Dict, List, Union
from vtkmodules.vtkCommonMath import vtkMatrix4x4

import vtk
from PyQt5 import QtCore
from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox

from src import gui_utils, locales, qt_utils
from src.figure_editor import PlaneEditor, ConeEditor
from src.gui_utils import (
    showErrorDialog,
    plane_tf,
    read_planes,
    Plane,
    Cone,
    showInfoDialog,
)
from src.process import Process
from src.settings import (
    sett,
    save_settings,
    save_splanes_to_file,
    load_settings,
    get_color,
    PathBuilder,
    create_temporary_project_files,
    update_last_open_project,
    get_recent_projects,
    delete_temporary_project_files,
)
import src.settings as settings

try:
    from src.bug_report import bugReportDialog
except:
    print("bug reporting is unavailable")

# try import of private hardware module
try:
    import src.hardware.service as service
    import src.hardware.calibration as calibration
    import src.hardware.printer as printer
except Exception as e:
    print(f"hardware module is unavailable: {e}")


class MainController:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        # hardware part might be unavailable
        try:
            self.printer = printer.EpitPrinter()
            # embed service tool
            self.servicePanel = service.ServicePanel(view)
            self.servicePanel.setModal(True)
            self.serviceController = service.ServiceController(
                self.servicePanel, service.ServiceModel(self.printer)
            )

            # embed calibration tool
            self.calibrationPanel = calibration.CalibrationPanel(view)
            self.calibrationPanel.setModal(True)
            self.calibrationController = calibration.CalibrationController(
                self.calibrationPanel,
                calibration.CalibrationModel(
                    self.printer, PathBuilder.calibration_file()
                ),
            )
        except:
            print("printer is not initialized")

        # bug reporting might be unavailable
        try:
            self.bugReportDialog = bugReportDialog(self)
        except:
            print("bug reporting is unavailable")
        self._connect_signals()

    def _connect_signals(self):
        self.view.open_action.triggered.connect(self.open_file)
        self.view.save_gcode_action.triggered.connect(partial(self.save_gcode_file))
        self.view.save_sett_action.triggered.connect(self.save_settings_file)
        self.view.save_project_action.triggered.connect(self.save_project)
        self.view.save_project_as_action.triggered.connect(self.save_project_as)
        self.view.load_sett_action.triggered.connect(self.load_settings_file)
        self.view.slicing_info_action.triggered.connect(self.get_slicer_version)
        self.view.check_updates_action.triggered.connect(self.open_updater)

        try:
            self.view.calibration_action.triggered.connect(self.calibration_action_show)
        except:
            self.view.calibration_action.triggered.connect(
                lambda: showInfoDialog(locales.getLocale().ErrorHardwareModule)
            )

        try:
            self.view.bug_report.triggered.connect(self.bugReportDialog.show)
        except:
            self.view.bug_report.triggered.connect(
                lambda: showInfoDialog(locales.getLocale().ErrorBugModule)
            )

        # right panel
        self.view.setts.get_element("printer_path", "add_btn").clicked.connect(
            self.create_printer
        )
        self.view.setts.edit("printer_path").clicked.connect(self.choose_printer_path)

        self.view.model_switch_box.stateChanged.connect(self.view.switch_stl_gcode)
        self.view.model_centering_box.stateChanged.connect(self.view.model_centering)
        self.view.picture_slider.valueChanged.connect(self.change_layer_view)
        self.view.move_button.clicked.connect(self.move_model)
        self.view.place_button.clicked.connect(self.place_model)
        self.view.cancel_action.clicked.connect(partial(self.view.shift_state, True))
        self.view.return_action.clicked.connect(partial(self.view.shift_state, False))
        self.view.load_model_button.clicked.connect(self.open_file)
        self.view.slice3a_button.clicked.connect(partial(self.slice_stl, "3axes"))
        self.view.slice_vip_button.clicked.connect(partial(self.slice_stl, "vip"))
        self.view.save_gcode_button.clicked.connect(self.save_gcode_file)
        self.view.color_model_button.clicked.connect(self.colorize_model)

        # bottom panel
        self.view.add_plane_button.clicked.connect(self.add_splane)
        self.view.add_cone_button.clicked.connect(self.add_cone)
        self.view.edit_figure_button.clicked.connect(self.change_figure_parameters)
        self.view.save_planes_button.clicked.connect(self.save_planes)
        self.view.download_planes_button.clicked.connect(self.download_planes)
        self.view.remove_plane_button.clicked.connect(self.remove_splane)
        self.view.splanes_tree.itemClicked.connect(self.change_splanes_tree)
        self.view.splanes_tree.itemChanged.connect(self.change_figure_check_state)
        self.view.splanes_tree.currentItemChanged.connect(self.change_combo_select)
        self.view.splanes_tree.model().rowsInserted.connect(self.moving_figure)

        self.view.hide_checkbox.stateChanged.connect(self.view.hide_splanes)

        # on close of window we save current planes to project file
        self.view.before_closing_signal.connect(self.save_planes_on_close)
        self.view.save_project_signal.connect(self.save_project)

    def calibration_action_show(self):
        # check that printer is not default, otherwise show information with warning
        if self.current_printer_is_default():
            showInfoDialog(locales.getLocale().DefaultPrinterWarn)

        self.calibrationPanel.show()

    def current_printer_is_default(self):
        if os.path.basename(sett().hardware.printer_dir) == "default":
            return True

        return False

    def save_planes_on_close(self):
        self.save_settings("vip")

    def create_printer(self):
        # query user for printer name and create directory in data/printers/<name> relative to FASP root
        text, ok = QInputDialog.getText(
            self.view,
            locales.getLocale().AddNewPrinter,
            locales.getLocale().ChoosePrinterDirectory,
        )
        if not ok:
            return

        printer_name = text.strip()
        if not printer_name:
            return

        # create directory in data/printers/<name> relative to FASP root
        printer_path = path.join(settings.APP_PATH, "data", "printers", printer_name)

        # check if directory already exists
        if path.exists(printer_path):
            showErrorDialog("Printer with this name already exists")
            return

        # create directory
        os.makedirs(printer_path)

        # copy calibration data from default directory to new printer directory
        default_calibration_file = path.join(
            settings.APP_PATH, "data", "printers", "default", "calibration_data.csv"
        )
        target_calibration_file = path.join(printer_path, "calibration_data.csv")

        shutil.copyfile(default_calibration_file, target_calibration_file)

        # update settings
        sett().hardware.printer_dir = printer_path
        sett().hardware.calibration_file = "calibration_data.csv"
        save_settings()

        # update label with printer path
        self.view.setts.edit("printer_path").setText(os.path.basename(printer_path))

        # update path in calibration model
        try:
            self.calibrationController.updateCalibrationFilepath(
                PathBuilder.calibration_file()
            )
        except AttributeError:
            print("hardware module is unavailable, skip")

        # show info dialog
        showInfoDialog(
            "Printer created successfully, please calibrate before first use"
        )

    def choose_printer_path(self):
        printer_path = QFileDialog.getExistingDirectory(
            self.view,
            locales.getLocale().ChoosePrinterDirectory,
            sett().hardware.printer_dir,
        )

        if printer_path:
            # check if directory contains calibration file
            calibration_file = path.join(printer_path, "calibration_data.csv")
            if not path.exists(calibration_file):
                showErrorDialog(
                    "Directory doesn't contain calibration file. Please choose another directory."
                )
                return

            sett().hardware.printer_dir = printer_path
            # calibration file will be at default location
            sett().hardware.calibration_file = "calibration_data.csv"

            # save settings
            save_settings()

            # update label with printer path
            self.view.setts.edit("printer_path").setText(os.path.basename(printer_path))

            # update path in calibration model
            try:
                self.calibrationController.updateCalibrationFilepath(
                    PathBuilder.calibration_file()
                )
            except AttributeError:
                print("hardware module is unavailable, skip")

    def moving_figure(self, sourceParent, previousRow):
        if sourceParent.row() != -1:
            child = self.view.splanes_tree.topLevelItem(sourceParent.row()).child(0)
            self.view.splanes_tree.topLevelItem(sourceParent.row()).removeChild(child)

            self.view.splanes_tree.insertTopLevelItem(sourceParent.row() + 1, child)
            self.view.splanes_tree.itemIsMoving = False
            self.view.splanes_tree.setCurrentItem(child)

            return

        currentRow = self.view.splanes_tree.currentIndex().row()

        if currentRow != -1:
            previousItem = self.view.splanes_tree.topLevelItem(previousRow)
            previousItemNumber = int(previousItem.text(1))

            if previousItemNumber > 0:
                currentRow = previousItemNumber - 1

            self.view.splanes_tree.setCurrentItem(
                self.view.splanes_tree.topLevelItem(previousRow)
            )

            if previousRow != currentRow:
                if previousRow > currentRow:  # Down
                    self.model.splanes.insert(
                        previousRow + 1, self.model.splanes[currentRow]
                    )
                    del self.model.splanes[currentRow]

                if previousRow < currentRow:  # Up
                    self.model.splanes.insert(
                        previousRow, self.model.splanes[currentRow]
                    )
                    del self.model.splanes[currentRow + 1]

                for i in range(len(self.model.splanes)):
                    self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
                    self.view.splanes_tree.topLevelItem(i).setText(
                        2, self.model.splanes[i].toFile()
                    )

                self.view._recreate_splanes(self.model.splanes)
                self.view.splanes_tree.itemIsMoving = False
                self.view.change_combo_select(
                    self.model.splanes[previousRow], previousRow
                )

    def change_figure_check_state(self, item, column):
        ind = self.view.splanes_tree.indexFromItem(item).row()
        if ind == -1:
            return

        if column == 0:
            if item.checkState(0) == QtCore.Qt.CheckState.Checked:
                self.view.splanes_actors[ind].VisibilityOff()
            else:
                self.view.splanes_actors[ind].VisibilityOn()
            self.view.reload_scene()

    def change_splanes_tree(self, item, column):
        if column == 0:
            return
        self.change_figure_parameters()

    def change_figure_parameters(self):
        self.view.picture_slider.setValue(0)
        self.view.model_switch_box.setChecked(True)
        self.view.hide_checkbox.setChecked(False)
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            self.view.tabs.setCurrentWidget(self.view.tabs.widget(0))
            self.view.tabs.setTabEnabled(1, False)
            return

        self.view.tabs.setCurrentWidget(self.view.tabs.widget(1))
        self.view.tabs.setTabEnabled(1, True)

        if isinstance(self.model.splanes[ind], Plane):
            self.view.parameters_tooling = PlaneEditor(
                self.view.tabs,
                self.update_plane_common,
                self.model.splanes[ind].params(),
                settings_provider=lambda: self.model.figures_setts[ind],
                figure_index=ind,
            )
        elif isinstance(self.model.splanes[ind], Cone):
            self.view.parameters_tooling = ConeEditor(
                self.view.tabs,
                self.update_cone_common,
                self.model.splanes[ind].params(),
                settings_provider=lambda: self.model.figures_setts[ind],
                figure_index=ind,
            )

    def save_planes(self):
        try:
            directory = (
                "Planes_" + os.path.basename(sett().slicing.stl_file).split(".")[0]
            )
            filename = str(
                self.view.save_dialog(
                    self.view.locale.SavePlanes, "TXT (*.txt *.TXT)", directory
                )
            )
            if filename != "":
                if not (filename.endswith(".txt") or filename.endswith(".TXT")):
                    filename += ".txt"
                save_splanes_to_file(self.model.splanes, filename)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def download_planes(self):
        try:
            filename = str(
                self.view.open_dialog(
                    self.view.locale.DownloadPlanes, "TXT (*.txt *.TXT)"
                )
            )
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".TXT":
                    try:
                        self.load_planes_from_file(filename)
                    except:
                        showErrorDialog("Error during reading planes file")
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def load_figure_settings(self):
        # check if we have figures specific settings
        if not hasattr(sett(), "figures"):
            setattr(sett(), "figures", [])

        if len(self.model.splanes) == 0:
            return

        self.model.figures_setts = []

        for idx in range(len(self.model.splanes)):
            # check if we have specific settings for this figure
            if idx > len(sett().figures) - 1:
                sett().figures.append(
                    settings.Settings(
                        {
                            "index": idx,
                            "description": self.model.splanes[idx].toFile(),
                            "settings": settings.Settings({}),
                        }
                    )
                )

            if not hasattr(sett().figures[idx], "settings"):
                setattr(sett().figures[idx], "settings", settings.Settings({}))

            self.model.figures_setts.append(sett().figures[idx].settings)

    def load_planes_from_file(self, filename):
        self.load_planes(read_planes(filename))

    def load_planes(self, splanes):
        if len(splanes) == 0:
            splanes = [Plane(0, 0, [0, 0, 0])] + splanes

        # check if the first figure is plane and if it is not, add it
        if not isinstance(splanes[0], Plane) or splanes[0] != Plane(0, 0, [0, 0, 0]):
            splanes = [Plane(0, 0, [0, 0, 0])] + splanes

        self.model.splanes = splanes
        self.view.hide_checkbox.setChecked(False)
        self.view.reload_splanes(self.model.splanes)
        self.load_figure_settings()

    def change_layer_view(self):
        if not self.model.current_slider_value:
            self.model.current_slider_value = 0

        if self.view.picture_slider.value() == self.model.current_slider_value:
            return

        step = (
            1
            if self.view.picture_slider.value() > self.model.current_slider_value
            else -1
        )

        for i in range(
            self.model.current_slider_value, self.view.picture_slider.value(), step
        ):
            self.model.current_slider_value = self.view.change_layer_view(
                i + step, self.model.current_slider_value, self.model.gcode
            )

        self.view.reload_scene()
        self.view.hide_checkbox.setChecked(True)
        self.view.model_switch_box.setChecked(False)

    def update_wall_thickness(self):
        self.update_dependent_fields(
            self.view.number_wall_lines_value,
            self.view.line_width_value,
            self.view.wall_thickness_value,
        )

    def change_layer_height(self):
        self.update_bottom_thickness()
        self.update_lid_thickness()
        self.update_supports_bottom_thickness()
        self.update_supports_lid_thickness()

    def update_bottom_thickness(self):
        self.update_dependent_fields(
            self.view.number_of_bottom_layers_value,
            self.view.layer_height_value,
            self.view.bottom_thickness_value,
        )

    def update_lid_thickness(self):
        self.update_dependent_fields(
            self.view.number_of_lid_layers_value,
            self.view.layer_height_value,
            self.view.lid_thickness_value,
        )

    def update_supports_bottom_thickness(self):
        self.update_dependent_fields(
            self.view.supports_number_of_bottom_layers_value,
            self.view.layer_height_value,
            self.view.supports_bottom_thickness_value,
        )

    def update_supports_lid_thickness(self):
        self.update_dependent_fields(
            self.view.supports_number_of_lid_layers_value,
            self.view.layer_height_value,
            self.view.supports_lid_thickness_value,
        )

    def update_dependent_fields(self, entry_field_1, entry_field_2, output_field):
        entry_field_1_text = entry_field_1.text().replace(",", ".")
        entry_field_2_text = entry_field_2.text().replace(",", ".")

        if ((not entry_field_1_text) or entry_field_1_text == ".") or (
            (not entry_field_2_text) or entry_field_2_text == "."
        ):
            output_field.setText("0.0")
        else:
            output_field.setText(
                str(round(float(entry_field_1_text) * float(entry_field_2_text), 2))
            )

    def move_model(self):
        self.view.move_stl2()

    def place_model(self):
        self.view.stlActor.ResetColorize()

    def open_file(self):
        try:
            filename = str(self.view.open_dialog(self.view.locale.OpenModel))
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".STL":
                    self.reset_settings()
                    s = sett()
                    # copy stl file to project directory

                    stl_full_path = PathBuilder.stl_model_temp()
                    shutil.copyfile(filename, stl_full_path)
                    # relative path inside project
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
                    # s.slicing.stl_file = filename # TODO optimize
                    self.save_settings("vip")
                    self.load_gcode(filename, False)
                    self.update_interface(filename)
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def reset_settings(self):
        s = sett()
        s.slicing.originx, s.slicing.originy, s.slicing.originz = 0, 0, 0
        s.slicing.rotationx, s.slicing.rotationy, s.slicing.rotationz = 0, 0, 0
        s.slicing.scalex, s.slicing.scaley, s.slicing.scalez = 1, 1, 1
        s.slicing.model_centering = False
        s.slicing.print_time = 0
        s.slicing.consumption_material = 0
        s.slicing.planes_contact_with_nozzle = ""

        # Set 0.0 for the transformation matrix for rotation and translation. Set 1.0 for scaling
        for i in range(4):
            for j in range(4):
                if i == j:
                    setattr(s.slicing.transformation_matrix, f"m{i}{i}", 1.0)
                else:
                    setattr(s.slicing.transformation_matrix, f"m{i}{j}", 0.0)

        self.save_settings("vip")

    def load_stl(self, filename, colorize=False):
        if filename is None or filename == "":
            filename = self.model.opened_stl
        stl_actor = gui_utils.createStlActorInOrigin(filename, colorize)
        self.model.opened_stl = filename
        self.view.load_stl(stl_actor)
        self.view.hide_checkbox.setChecked(True)
        self.view._recreate_splanes(self.model.splanes)

    def load_gcode(self, filename, is_from_stl):
        def work():
            print("start parsing gcode")
            start_time = time.time()
            gc = self.model.load_gcode(filename)
            print("finish parsing gcode")
            end_time = time.time()
            print("spent time for gcode loading: ", end_time - start_time, "s")

            return gc

        gc = qt_utils.progress_dialog(
            locales.getLocale().GCodeLoadingTitle,
            locales.getLocale().GCodeLoadingProgress,
            work,
        )
        blocks = gui_utils.makeBlocks(gc.layers, gc.rotations, gc.lays2rots)
        actors = gui_utils.wrapWithActors(blocks, gc.rotations, gc.lays2rots)

        if len(self.model.splanes) > 0:
            currentItem = int(self.view.splanes_tree.currentItem().text(1)) - 1
        else:
            currentItem = 0

        self.view.load_gcode(actors, is_from_stl, plane_tf(gc.rotations[0]))

        if len(self.model.splanes) > 0:
            self.view._recreate_splanes(self.model.splanes)
            self.view.splanes_actors[currentItem].GetProperty().SetColor(
                get_color(sett().colors.last_layer)
            )
            self.view.splanes_actors[currentItem].GetProperty().SetOpacity(
                sett().common.opacity_last_layer
            )

    def slice_stl(self, slicing_type):
        if slicing_type == "vip" and len(self.model.splanes) == 0:
            showErrorDialog(locales.getLocale().AddOnePlaneError)
            return

        if not self.check_calibration_data_catalog():
            return

        self.save_settings(slicing_type, PathBuilder.settings_file_temp())

        def work():
            start_time = time.time()
            print("start slicing")
            p = Process(PathBuilder.slicing_cmd())
            p.wait()
            print("finished command")
            end_time = time.time()
            print("spent time for slicing: ", end_time - start_time, "s")

            if p.returncode == 2:
                # panic
                return p.stderr
            elif p.returncode == 1:
                # fatal, the error is in the latest line
                error_message = p.stdout.splitlines()[-1]
                if "path is not closed before triangulation" in error_message:
                    return locales.getLocale().WarningPathNotClosed
                else:
                    return error_message

            # no errors
            return ""

        error = qt_utils.progress_dialog(
            locales.getLocale().SlicingTitle,
            locales.getLocale().SlicingProgress,
            work,
        )

        if error:
            logging.error(f"error: <{error}>")
            gui_utils.showErrorDialog(error)
            return

        # load gcode without calibration
        self.view.picture_slider.setValue(0)
        self.load_gcode(PathBuilder.gcodevis_file(), True)
        print("loaded gcode")
        self.update_interface(sett().slicing.stl_filename)

    def check_calibration_data_catalog(self):
        if self.current_printer_is_default():
            locale = locales.getLocale()

            message_box = QMessageBox()
            message_box.setWindowTitle(locale.SelectingCalibrationData)
            message_box.setText(locale.CalibrationDataWarning)
            message_box.addButton(QMessageBox.Yes)
            message_box.addButton(QMessageBox.No)
            message_box.button(QMessageBox.Yes).setText(locale.Continue)
            message_box.button(QMessageBox.No).setText(locale.Cancel)

            reply = message_box.exec()

            if reply == QMessageBox.No:
                return False

        return True

    def get_slicer_version(self):
        proc = Process(sett().slicing.cmd_version).wait()

        if proc.returncode:
            showErrorDialog("Error during getting slicer version:" + str(proc.stdout))
        else:
            showInfoDialog(locales.getLocale().SlicerVersion + proc.stdout)

    def save_settings(self, slicing_type, filename=""):
        s = sett()
        print(
            f"saving settings of stl file {self.model.opened_stl} {s.slicing.stl_file}"
        )
        # s.slicing.stl_file = self.model.opened_stl
        tf = vtk.vtkTransform()
        if self.view.stlActor is not None:
            tf = self.view.stlActor.GetUserTransform()

        s.slicing.originx, s.slicing.originy, s.slicing.originz = tf.GetPosition()
        (
            s.slicing.rotationx,
            s.slicing.rotationy,
            s.slicing.rotationz,
        ) = tf.GetOrientation()
        s.slicing.scalex, s.slicing.scaley, s.slicing.scalez = tf.GetScale()
        s.slicing.slicing_type = slicing_type

        m = vtkMatrix4x4()
        tf.GetMatrix(m)
        for i in range(4):
            for j in range(4):
                setattr(s.slicing.transformation_matrix, f"m{i}{j}", m.GetElement(i, j))

        # save planes to settings
        s.figures = []
        for idx, plane in enumerate(self.model.splanes):
            s.figures.append(
                dict(
                    index=idx,
                    description=plane.toFile(),
                    settings=self.model.figures_setts[idx],
                )
            )

        if filename != "":
            save_settings(filename)

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
                        # TODO: right now to maintain good transfer
                        # we need to copy the project_path setting manually
                        # everything else will work alright
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
        # self.model.opened_stl = s.slicing.stl_file

    # ######################bottom panel

    def add_splane(self):
        self.view.model_switch_box.setChecked(True)
        self.view.hide_checkbox.setChecked(False)
        self.model.add_splane()
        self.view.reload_splanes(self.model.splanes)
        self.change_figure_parameters()

    def add_cone(self):
        self.view.model_switch_box.setChecked(True)
        self.view.hide_checkbox.setChecked(False)
        self.model.add_cone()
        self.view.reload_splanes(self.model.splanes)
        self.change_figure_parameters()

    def remove_splane(self):
        self.view.model_switch_box.setChecked(True)
        self.view.hide_checkbox.setChecked(False)
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return

        if ind == 0:
            showErrorDialog(locales.getLocale().RemoveFirstPlaneError)
            return

        del self.model.splanes[ind]
        del self.model.figures_setts[ind]
        self.view.splanes_tree.takeTopLevelItem(ind)
        self.view.reload_splanes(self.model.splanes)
        if len(self.model.splanes) == 0:
            if (
                self.view.parameters_tooling
                and not self.view.parameters_tooling.isHidden()
            ):
                self.view.parameters_tooling.close()

        self.change_figure_parameters()

    def change_combo_select(self):
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return

        if not self.view.splanes_tree.itemIsMoving:
            if (
                self.view.parameters_tooling
                and not self.view.parameters_tooling.isHidden()
            ):
                self.change_figure_parameters()

            if len(self.model.splanes) > ind:
                self.view.change_combo_select(self.model.splanes[ind], ind)

    def update_plane_common(self, values: Dict[str, Union[float, bool]]):
        center = [values.get("X", 0), values.get("Y", 0), values.get("Z", 0)]
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Plane(
            values.get("Tilt", 0),
            values.get("Rotation", 0),
            center,
            values.get("Smooth", False),
        )
        self.view.update_splane(self.model.splanes[ind], ind)

        for i in range(len(self.model.splanes)):
            self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
            self.view.splanes_tree.topLevelItem(i).setText(
                2, self.model.splanes[i].toFile()
            )

    def update_cone_common(self, values: Dict[str, float]):
        center: List[float] = [0, 0, values.get("Z", 0)]
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Cone(
            values.get("A", 0), tuple(center), values.get("H1", 0), values.get("H2", 15)
        )
        self.view.update_cone(self.model.splanes[ind], ind)

        for i in range(len(self.model.splanes)):
            self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
            self.view.splanes_tree.topLevelItem(i).setText(
                2, self.model.splanes[i].toFile()
            )

    def update_interface(self, filename=""):
        s = sett()

        if not filename:
            self.view.name_stl_file.setText("")
            self.view.setWindowTitle("FASP")
        else:
            name_stl_file = os.path.splitext(os.path.basename(filename))[0]
            file_ext = os.path.splitext(filename)[1].upper()

            self.view.setWindowTitle(name_stl_file + " - FASP")
            self.view.name_stl_file.setText(
                self.view.locale.FileName + name_stl_file + file_ext
            )

        string_print_time = ""

        if s.slicing.print_time > 3600:
            hours = s.slicing.print_time / 3600
            string_print_time += (
                str(math.floor(hours)) + " " + self.view.locale.Hour + ", "
            )

        if s.slicing.print_time > 60:
            minutes = (s.slicing.print_time % 3600) / 60
            string_print_time += (
                str(math.floor(minutes)) + " " + self.view.locale.Minute + ", "
            )

        if s.slicing.print_time > 0:
            seconds = (s.slicing.print_time % 3600) % 60
            string_print_time += (
                str(math.floor(seconds)) + " " + self.view.locale.Second
            )

        self.view.print_time_value.setText(string_print_time)

        # !Temporary shutdown of the counter at too large values
        if s.slicing.print_time > 250000:
            self.view.print_time_value.setText("")

        string_consumption_material = ""
        if s.slicing.consumption_material > 0:
            material_weight = (
                (
                    s.slicing.consumption_material
                    * math.pow(s.hardware.bar_diameter / 2, 2)
                    * math.pi
                )
                * s.hardware.density
                / 1000
            )
            string_consumption_material += (
                str(math.ceil(material_weight)) + " " + self.view.locale.Gram + ", "
            )
            string_consumption_material += (
                str(float("{:.2f}".format(s.slicing.consumption_material / 1000)))
                + " "
                + self.view.locale.Meter
            )

        self.view.consumption_material_value.setText(string_consumption_material)

        if s.slicing.planes_contact_with_nozzle:
            self.view.warning_nozzle_and_table_collision.setText(
                self.view.locale.WarningNozzleAndTableCollision
                + s.slicing.planes_contact_with_nozzle
            )
        else:
            self.view.warning_nozzle_and_table_collision.setText("")

    def open_updater(self):
        subprocess.Popen("./updater")
