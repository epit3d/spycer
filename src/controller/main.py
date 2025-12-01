import logging
import math
import os
from os import path
import subprocess
import time
from pathlib import Path
import shutil
from typing import Dict, List, Union
from vtkmodules.vtkCommonMath import vtkMatrix4x4

import vtk
from PyQt5 import QtCore
from PyQt5.QtCore import QUrl
from PyQt5.QtWidgets import QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtGui import QDesktopServices

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
    get_color,
    PathBuilder,
    to_plain_data,
)
import src.settings as settings

from .hardware import create_printer, create_service, create_calibration
from .ui_wiring import connect_signals
from .file_management import FileManagementMixin

logger = logging.getLogger(__name__)

try:
    from src.bug_report import bugReportDialog
except Exception:
    logger.warning("bug reporting is unavailable")


class MainController(FileManagementMixin):
    def __init__(self, view, model, printer=None, service=None, calibration=None):
        self.view = view
        self.model = model

        # hardware part might be unavailable
        self.printer = printer if printer is not None else create_printer()

        if service is not None:
            self.servicePanel, self.serviceController = service
        else:
            self.servicePanel, self.serviceController = create_service(
                view, self.printer
            )

        if calibration is not None:
            self.calibrationPanel, self.calibrationController = calibration
        else:
            self.calibrationPanel, self.calibrationController = create_calibration(
                view, self.printer
            )

        # bug reporting might be unavailable
        try:
            self.bugReportDialog = bugReportDialog(self)
        except Exception:
            logger.warning("bug reporting is unavailable")
        connect_signals(self)

    def calibration_action_show(self):
        if not self.calibrationPanel:
            showInfoDialog(locales.getLocale().ErrorHardwareModule)
            return

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
            logger.warning("hardware module is unavailable, skip")

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
                logger.warning("hardware module is unavailable, skip")

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
                    except Exception as e:
                        showErrorDialog("Error during reading planes file: " + str(e))
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

            if isinstance(sett().figures[idx], dict):
                sett().figures[idx] = settings.Settings(sett().figures[idx])

            if not hasattr(sett().figures[idx], "settings"):
                setattr(sett().figures[idx], "settings", settings.Settings({}))

            try:
                self.model.figures_setts.append(sett().figures[idx].settings)
            except Exception as e:
                showErrorDialog("Error accessing settings: " + str(e))

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
            logger.info("start parsing gcode")
            start_time = time.time()
            gc = self.model.load_gcode(filename)
            logger.info("finish parsing gcode")
            end_time = time.time()
            logger.info("spent time for gcode loading: %s s", end_time - start_time)

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
            logger.info("start slicing")
            p = Process(PathBuilder.slicing_cmd())
            p.wait()
            logger.info("finished command")
            end_time = time.time()
            logger.info("spent time for slicing: %s s", end_time - start_time)

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
        logger.info("loaded gcode")
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

    def show_online_documentation(self):
        # open default browser to the online documentation
        QDesktopServices.openUrl(QUrl("https://docs.epit3d.com"))

    def save_settings(self, slicing_type, filename=""):
        s = sett()
        logger.info(
            "saving settings of stl file %s %s",
            self.model.opened_stl,
            s.slicing.stl_file,
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
                    settings=to_plain_data(self.model.figures_setts[idx]),
                )
            )

        save_settings(filename or None)

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
