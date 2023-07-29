import logging
import math
import os
from os import path
import subprocess
import time
import sys
import src.service as service
import src.calibration as calibration
import src.printer as printer
from functools import partial
from pathlib import Path
import shutil
from shutil import copy2
from typing import Dict, List
from vtkmodules.vtkCommonMath import vtkMatrix4x4
from datetime import datetime
import zipfile

import vtk
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QFileDialog, QMessageBox

from src import gui_utils, locales, qt_utils
from src.figure_editor import PlaneEditor, ConeEditor
from src.gui_utils import showErrorDialog, plane_tf, read_planes, Plane, Cone, showInfoDialog
from src.process import Process
from src.settings import sett, save_settings, load_settings, get_color, PathBuilder
from src.server import send_bug_report


class MainController:
    def __init__(self, view, model):
        self.view = view
        self.model = model

        self.printer = printer.EpitPrinter()
        # embed service tool
        self.servicePanel = service.ServicePanel(view)
        self.servicePanel.setModal(True)
        self.serviceController = service.ServiceController(
            self.servicePanel,
            service.ServiceModel(self.printer)
        )

        # embed calibration tool
        self.calibrationPanel = calibration.CalibrationPanel(view)
        self.calibrationPanel.setModal(True)
        self.calibrationController = calibration.CalibrationController(
            self.calibrationPanel,
            calibration.CalibrationModel(self.printer)
        )

        self.bugReportDialog = bugReportDialog(self)
        self._connect_signals()

    def _connect_signals(self):
        self.view.open_action.triggered.connect(self.open_file)
        self.view.save_gcode_action.triggered.connect(partial(self.save_gcode_file))
        self.view.save_sett_action.triggered.connect(self.save_settings_file)
        self.view.load_sett_action.triggered.connect(self.load_settings_file)
        self.view.slicing_info_action.triggered.connect(self.get_slicer_version)

        self.view.calibration_action.triggered.connect(
            self.calibrationPanel.show
        )
        self.view.bug_report.triggered.connect(
            self.bugReportDialog.show
        )

        # right panel
        self.view.number_wall_lines_value.textChanged.connect(self.update_wall_thickness)
        self.view.line_width_value.textChanged.connect(self.update_wall_thickness)
        self.view.layer_height_value.textChanged.connect(self.change_layer_height)
        self.view.number_of_bottom_layers_value.textChanged.connect(self.update_bottom_thickness)
        self.view.number_of_lid_layers_value.textChanged.connect(self.update_lid_thickness)
        self.view.supports_number_of_bottom_layers_value.textChanged.connect(self.update_supports_bottom_thickness)
        self.view.supports_number_of_lid_layers_value.textChanged.connect(self.update_supports_lid_thickness)
        self.view.model_switch_box.stateChanged.connect(self.view.switch_stl_gcode)
        self.view.model_centering_box.stateChanged.connect(self.view.model_centering)
        self.view.picture_slider.valueChanged.connect(self.change_layer_view)
        self.view.move_button.clicked.connect(self.move_model)
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
        self.view.close_signal.connect(self.save_planes_on_close)

    def save_planes_on_close(self):
        splanes_full_pth = PathBuilder.splanes_file()
        save_splanes_to_file(self.model.splanes, splanes_full_pth)
        sett().slicing.splanes_file = path.basename(splanes_full_pth)
        save_settings()

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

            self.view.splanes_tree.setCurrentItem(self.view.splanes_tree.topLevelItem(previousRow))

            if previousRow != currentRow:
                if previousRow > currentRow: #Down
                    self.model.splanes.insert(previousRow + 1, self.model.splanes[currentRow])
                    del self.model.splanes[currentRow]

                if previousRow < currentRow: #Up
                    self.model.splanes.insert(previousRow, self.model.splanes[currentRow])
                    del self.model.splanes[currentRow + 1]

                for i in range(len(self.model.splanes)):
                    self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
                    self.view.splanes_tree.topLevelItem(i).setText(2, self.model.splanes[i].toFile())

                self.view._recreate_splanes(self.model.splanes)
                self.view.splanes_tree.itemIsMoving = False
                self.view.change_combo_select(self.model.splanes[previousRow], previousRow)

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
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            self.view.tabs.setCurrentWidget(self.view.tabs.widget(0))
            self.view.tabs.setTabEnabled(1, False)
            return

        self.view.tabs.setCurrentWidget(self.view.tabs.widget(1))
        self.view.tabs.setTabEnabled(1, True)

        if isinstance(self.model.splanes[ind], Plane):
            self.view.parameters_tooling = PlaneEditor(self.view.tabs, self.update_plane_common, self.model.splanes[ind].params())
        elif isinstance(self.model.splanes[ind], Cone):
            self.view.parameters_tooling = ConeEditor(self.view.tabs, self.update_cone_common, self.model.splanes[ind].params())

    def save_planes(self):
        try:
            directory = "Planes_" + os.path.basename(sett().slicing.stl_file).split('.')[0]
            filename = str(self.view.save_dialog(self.view.locale.SavePlanes, "TXT (*.txt *.TXT)", directory))
            if filename != "":
                if not (filename.endswith(".txt") or filename.endswith(".TXT")):
                    filename += ".txt"
                save_splanes_to_file(self.model.splanes, filename)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def download_planes(self):
        try:
            filename = str(self.view.open_dialog(self.view.locale.DownloadPlanes,"TXT (*.txt *.TXT)"))
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".TXT":
                    try:
                        self.load_planes(filename)
                    except:
                        showErrorDialog("Error during reading planes file")
                else:
                    showErrorDialog(
                        "This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def load_planes(self, filename):
        self.model.splanes = read_planes(filename)
        self.view.hide_checkbox.setChecked(False)
        self.view.reload_splanes(self.model.splanes)

    def change_layer_view(self):
        self.model.current_slider_value = self.view.change_layer_view(self.model.current_slider_value, self.model.gcode)

    def update_wall_thickness(self):
        self.update_dependent_fields(self.view.number_wall_lines_value, self.view.line_width_value, self.view.wall_thickness_value)

    def change_layer_height(self):
        self.update_bottom_thickness()
        self.update_lid_thickness()
        self.update_supports_bottom_thickness()
        self.update_supports_lid_thickness()

    def update_bottom_thickness(self):
        self.update_dependent_fields(self.view.number_of_bottom_layers_value, self.view.layer_height_value, self.view.bottom_thickness_value)

    def update_lid_thickness(self):
        self.update_dependent_fields(self.view.number_of_lid_layers_value, self.view.layer_height_value, self.view.lid_thickness_value)

    def update_supports_bottom_thickness(self):
        self.update_dependent_fields(self.view.supports_number_of_bottom_layers_value, self.view.layer_height_value, self.view.supports_bottom_thickness_value)
    
    def update_supports_lid_thickness(self):
        self.update_dependent_fields(self.view.supports_number_of_lid_layers_value, self.view.layer_height_value, self.view.supports_lid_thickness_value)

    def update_dependent_fields(self, entry_field_1, entry_field_2, output_field):
        entry_field_1_text = entry_field_1.text().replace(',', '.')
        entry_field_2_text = entry_field_2.text().replace(',', '.')

        if ((not entry_field_1_text) or entry_field_1_text == "." ) or ((not entry_field_2_text) or entry_field_2_text == "."):
            output_field.setText("0.0")
        else:
            output_field.setText(str(round(float(entry_field_1_text) * float(entry_field_2_text), 2)))

    def move_model(self):
        self.view.move_stl2()

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

                    stl_full_path = PathBuilder.stl_model()
                    shutil.copyfile(filename, stl_full_path)
                    # relative path inside project
                    s.slicing.stl_file = path.basename(stl_full_path) 

                    save_settings()
                    self.update_interface(filename)

                    self.view.model_centering_box.setChecked(False)

                    if os.path.isfile(s.colorizer.copy_stl_file):
                        os.remove(s.colorizer.copy_stl_file)

                    self.load_stl(stl_full_path)
                elif file_ext == ".GCODE":
                    s = sett()
                    # s.slicing.stl_file = filename # TODO optimize
                    save_settings()
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

        save_settings()

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
            print('finish parsing gcode')
            end_time = time.time()
            print('spent time for gcode loading: ', end_time - start_time, 's')

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
            self.view.splanes_actors[currentItem].GetProperty().SetColor(get_color(sett().colors.last_layer))
            self.view.splanes_actors[currentItem].GetProperty().SetOpacity(sett().common.opacity_last_layer) 

    def slice_stl(self, slicing_type):
        if slicing_type == "vip" and len(self.model.splanes) == 0:
            showErrorDialog(locales.getLocale().AddOnePlaneError)
            return

        s = sett()
        splanes_full_path = PathBuilder.splanes_file()
        save_splanes_to_file(self.model.splanes, splanes_full_path)
        sett().slicing.splanes_file = path.basename(splanes_full_path)
        self.save_settings(slicing_type)

        def work():
            start_time = time.time()
            print("start slicing")
            p = Process(PathBuilder.slicing_cmd())
            p.wait()
            print("finished command")
            end_time = time.time()
            print('spent time for slicing: ', end_time - start_time, 's')
            
            # goosli sends everything to stdout, returncode is 1 when fatal is called
            return p.stdout if p.returncode else ""

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
        self.load_gcode(PathBuilder.gcodevis_file(), True)
        print("loaded gcode")
        self.update_interface()

    def get_slicer_version(self):
        proc = Process(sett().slicing.cmd_version).wait()
        
        if proc.returncode:
            showErrorDialog("Error during getting slicer version:" + str(proc.stdout))
        else:
            showInfoDialog(locales.getLocale().SlicerVersion + proc.stdout)

    def save_settings(self, slicing_type, filename = ""):
        s = sett()
        print(f"saving settings of stl file {self.model.opened_stl} {s.slicing.stl_file}")
        # s.slicing.stl_file = self.model.opened_stl
        tf = vtk.vtkTransform()
        if self.view.stlActor is not None:
            tf = self.view.stlActor.GetUserTransform()
        s.slicing.originx, s.slicing.originy, s.slicing.originz = tf.GetPosition()
        s.slicing.rotationx, s.slicing.rotationy, s.slicing.rotationz = tf.GetOrientation()
        s.slicing.scalex, s.slicing.scaley, s.slicing.scalez = tf.GetScale()
        s.slicing.layer_height = float(self.view.layer_height_value.text())
        s.slicing.print_speed = float(self.view.print_speed_value.text())
        s.slicing.print_speed_layer1 = float(self.view.print_speed_layer1_value.text())
        s.slicing.print_speed_wall = float(self.view.print_speed_wall_value.text())
        s.slicing.extruder_temperature = float(self.view.extruder_temp_value.text())
        s.slicing.bed_temperature = float(self.view.bed_temp_value.text())
        s.slicing.fill_density = float(self.view.fill_density_value.text())
        s.slicing.wall_thickness = float(self.view.wall_thickness_value.text())
        s.slicing.line_width = float(self.view.line_width_value.text())
        s.slicing.filling_type = locales.getLocaleByLang("en").FillingTypeValues[
            self.view.filling_type_values.currentIndex()]
        s.slicing.retraction_on = self.view.retraction_on_box.isChecked()
        s.slicing.retraction_distance = float(self.view.retraction_distance_value.text())
        s.slicing.retraction_speed = float(self.view.retraction_speed_value.text())
        s.slicing.retract_compensation_amount = float(self.view.retract_compensation_amount_value.text())
        s.slicing.skirt_line_count = int(self.view.skirt_line_count_value.text())
        s.slicing.fan_off_layer1 = self.view.fan_off_layer1_box.isChecked()
        s.slicing.fan_speed = float(self.view.fan_speed_value.text())
        s.slicing.angle = float(self.view.colorize_angle_value.text())
        
        s.slicing.lids_depth = int(self.view.number_of_lid_layers_value.text())
        s.slicing.bottoms_depth = int(self.view.number_of_bottom_layers_value.text())
        
        s.supports.enabled = self.view.supports_on_box.isChecked()
        s.supports.xy_offset = float(self.view.support_xy_offset_value.text())
        s.supports.z_offset_layers = int(float(self.view.support_z_offset_layers_value.text()))
        s.supports.fill_density = float(self.view.support_density_value.text())
        s.supports.fill_type = locales.getLocaleByLang("en").FillingTypeValues[
            self.view.support_fill_type_values.currentIndex()]
        s.supports.priority_z_offset = bool(self.view.support_priority_z_offset_box.isChecked())
        s.supports.lids_depth = int(self.view.supports_number_of_lid_layers_value.text())
        s.supports.bottoms_depth = int(self.view.supports_number_of_bottom_layers_value.text())

        s.slicing.overlapping_infill_percentage = float(self.view.overlapping_infill_value.text())
        s.slicing.material_shrinkage = float(self.view.material_shrinkage_value.text())

        s.slicing.slicing_type = slicing_type

        m = vtkMatrix4x4()
        tf.GetMatrix(m)
        for i in range(4):
            for j in range(4):
                setattr(s.slicing.transformation_matrix, f"m{i}{j}", m.GetElement(i, j))

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
            directory = "Settings_" + os.path.basename(sett().slicing.stl_file).split('.')[0]
            filename = str(self.view.save_dialog(self.view.locale.SaveSettings, "YAML (*.yaml *.YAML)", directory))
            if filename != "":
                if not (filename.endswith(".yaml") or filename.endswith(".YAML")):
                    filename += ".yaml"
                self.save_settings("vip", filename)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def load_settings_file(self):
        try:
            filename = str(self.view.open_dialog(self.view.locale.LoadSettings,"YAML (*.yaml *.YAML)"))
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".YAML":
                    try:
                        load_settings(filename)
                        self.display_settings()
                    except:
                        showErrorDialog("Error during reading settings file")
                else:
                    showErrorDialog(
                        "This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def display_settings(self):
        s = sett()
        self.view.line_width_value.setText(str(s.slicing.line_width))
        self.view.layer_height_value.setText(str(s.slicing.layer_height))
        self.view.wall_thickness_value.setText(str(s.slicing.wall_thickness))
        self.view.number_of_bottom_layers_value.setText(str(s.slicing.bottoms_depth))
        self.view.number_of_lid_layers_value.setText(str(s.slicing.lids_depth))
        self.view.extruder_temp_value.setText(str(s.slicing.extruder_temperature))
        self.view.bed_temp_value.setText(str(s.slicing.bed_temperature))
        self.view.skirt_line_count_value.setText(str(s.slicing.skirt_line_count))
        self.view.fan_speed_value.setText(str(s.slicing.fan_speed))
        if s.slicing.fan_off_layer1:
            self.view.fan_off_layer1_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.view.fan_off_layer1_box.setCheckState(QtCore.Qt.Unchecked)
        self.view.print_speed_value.setText(str(s.slicing.print_speed))
        self.view.print_speed_layer1_value.setText(str(s.slicing.print_speed_layer1))
        self.view.print_speed_wall_value.setText(str(s.slicing.print_speed_wall))
        ind = locales.getLocaleByLang("en").FillingTypeValues.index(s.slicing.filling_type)
        self.view.filling_type_values.setCurrentIndex(ind)
        self.view.fill_density_value.setText(str(s.slicing.fill_density))
        self.view.overlapping_infill_value.setText(str(s.slicing.overlapping_infill_percentage))
        if s.slicing.retraction_on:
            self.view.retraction_on_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.view.retraction_on_box.setCheckState(QtCore.Qt.Unchecked)
        self.view.retraction_distance_value.setText(str(s.slicing.retraction_distance))
        self.view.retraction_speed_value.setText(str(s.slicing.retraction_speed))
        self.view.retract_compensation_amount_value.setText(str(s.slicing.retract_compensation_amount))
        if s.supports.enabled:
            self.view.supports_on_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.view.supports_on_box.setCheckState(QtCore.Qt.Unchecked)
        self.view.support_density_value.setText(str(s.supports.fill_density))
        ind = locales.getLocaleByLang("en").FillingTypeValues.index(s.supports.fill_type)
        self.view.support_fill_type_values.setCurrentIndex(ind)
        self.view.support_xy_offset_value.setText(str(s.supports.xy_offset))
        self.view.support_z_offset_layers_value.setText(str(s.supports.z_offset_layers))
        if s.supports.priority_z_offset:
            self.view.support_priority_z_offset_box.setCheckState(QtCore.Qt.Checked)
        else:
            self.view.support_priority_z_offset_box.setCheckState(QtCore.Qt.Unchecked)
        self.view.supports_number_of_bottom_layers_value.setText(str(s.supports.bottoms_depth))
        self.view.supports_bottom_thickness_value.setText(str(round(s.slicing.layer_height*s.supports.bottoms_depth,2)))
        self.view.supports_number_of_lid_layers_value.setText(str(int(s.supports.lids_depth)))
        self.view.supports_lid_thickness_value.setText(str(round(s.slicing.layer_height*s.supports.lids_depth,2)))
        self.view.colorize_angle_value.setText(str(s.slicing.angle))

    def colorize_model(self):
        shutil.copyfile(PathBuilder.stl_model(),PathBuilder.colorizer_stl())
        splanes_full_path = PathBuilder.splanes_file()
        save_splanes_to_file(self.model.splanes, splanes_full_path)
        sett().slicing.splanes_file = path.basename(splanes_full_path)
        self.save_settings("vip")

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
        self.view.hide_checkbox.setChecked(False)
        self.model.add_splane()
        self.view.reload_splanes(self.model.splanes)
        self.change_figure_parameters()

    def add_cone(self):
        self.view.hide_checkbox.setChecked(False)
        self.model.add_cone()
        self.view.reload_splanes(self.model.splanes)
        self.change_figure_parameters()

    def remove_splane(self):
        self.view.hide_checkbox.setChecked(False)
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        del self.model.splanes[ind]
        self.view.splanes_tree.takeTopLevelItem(ind)
        self.view.reload_splanes(self.model.splanes)
        if len(self.model.splanes) == 0:
            if self.view.parameters_tooling and not self.view.parameters_tooling.isHidden():
                self.view.parameters_tooling.close()

        self.change_figure_parameters()

    def change_combo_select(self):
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return

        if not self.view.splanes_tree.itemIsMoving:
            if self.view.parameters_tooling and not self.view.parameters_tooling.isHidden():
                self.change_figure_parameters()

            if len(self.model.splanes) > ind:
                    self.view.change_combo_select(self.model.splanes[ind], ind)

    def update_plane_common(self, values: Dict[str, float]):
        center = [values.get("X", 0), values.get("Y", 0), values.get("Z", 0)]
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Plane(values.get("Tilt", 0), values.get("Rotation", 0), center)
        self.view.update_splane(self.model.splanes[ind], ind)

        for i in range(len(self.model.splanes)):
            self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
            self.view.splanes_tree.topLevelItem(i).setText(2, self.model.splanes[i].toFile())

    def update_cone_common(self, values: Dict[str, float]):
        center: List[float] = [0, 0, values.get("Z", 0)]
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Cone(values.get("A", 0), tuple(center), values.get("H1", 0), values.get("H2", 15))
        self.view.update_cone(self.model.splanes[ind], ind)

        for i in range(len(self.model.splanes)):
            self.view.splanes_tree.topLevelItem(i).setText(1, str(i + 1))
            self.view.splanes_tree.topLevelItem(i).setText(2, self.model.splanes[i].toFile())

    def update_interface(self, filename = ""):
        s = sett()

        if not filename:
            self.view.name_stl_file.setText("")
            self.view.setWindowTitle("FASP")
        else:
            name_stl_file = os.path.splitext(os.path.basename(filename))[0]
            file_ext = os.path.splitext(filename)[1].upper()

            self.view.setWindowTitle(name_stl_file + " - FASP")
            self.view.name_stl_file.setText(self.view.locale.FileName + name_stl_file + file_ext)

        string_print_time = ""

        if s.slicing.print_time > 3600:
            hours = s.slicing.print_time / 3600
            string_print_time += str(math.floor(hours)) + " " + self.view.locale.Hour + ", "

        if s.slicing.print_time > 60:
            minutes = (s.slicing.print_time % 3600) / 60
            string_print_time += str(math.floor(minutes)) + " " + self.view.locale.Minute + ", "

        if s.slicing.print_time > 0:
            seconds = (s.slicing.print_time % 3600) % 60
            string_print_time += str(math.floor(seconds)) + " " + self.view.locale.Second

        self.view.print_time_value.setText(string_print_time)

        # !Temporary shutdown of the counter at too large values
        if s.slicing.print_time > 250000:
            self.view.print_time_value.setText("")

        string_consumption_material = ""
        if s.slicing.consumption_material > 0:
            material_weight = (s.slicing.consumption_material * math.pow(s.hardware.bar_diameter/2, 2) * math.pi) * s.hardware.density / 1000
            string_consumption_material += str(math.ceil(material_weight)) + " " + self.view.locale.Gram + ", "
            string_consumption_material += str(float("{:.2f}".format(s.slicing.consumption_material/1000))) + " " + self.view.locale.Meter

        self.view.consumption_material_value.setText(string_consumption_material)

        if s.slicing.planes_contact_with_nozzle:
            self.view.warning_nozzle_and_table_collision.setText(self.view.locale.WarningNozzleAndTableCollision + s.slicing.planes_contact_with_nozzle)
        else:
            self.view.warning_nozzle_and_table_collision.setText("")


def save_splanes_to_file(splanes, filename):
    with open(filename, 'w') as out:
        for p in splanes:
            out.write(p.toFile() + '\n')

class bugReportDialog(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(controller.view.locale.SubmittingBugReport)
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        self.description_label = QLabel(controller.view.locale.ErrorDescription)
        layout.addWidget(self.description_label)

        self.error_description = QTextEdit()
        layout.addWidget(self.error_description)
        self.error_description.setMinimumSize(400, 200)

        self.image_list = QLabel()
        layout.addWidget(self.image_list)

        add_image_button = QPushButton(controller.view.locale.AddImage)
        add_image_button.setFixedWidth(207)
        add_image_button.clicked.connect(partial(self.addImage, controller))
        layout.addWidget(add_image_button)

        send_layout = QHBoxLayout()
        send_layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(send_layout)

        send_button = QPushButton(controller.view.locale.Send)
        send_button.setFixedWidth(100)
        send_button.clicked.connect(partial(self.send, controller))
        send_layout.addWidget(send_button)

        cancel_button = QPushButton(controller.view.locale.Cancel)
        cancel_button.setFixedWidth(100)
        cancel_button.clicked.connect(self.cancel)
        send_layout.addWidget(cancel_button)

        self.setLayout(layout)

        self.images = []
        self.temp_images_folder = "temp\\images"

    def addImage(self, controller):
        image_path, _ = QFileDialog.getOpenFileName(self, controller.view.locale.AddingImage, "", "Images (*.png *.jpg)")

        if image_path:
            image_name = os.path.basename(image_path)
            temp_image_path = os.path.join(self.temp_images_folder, image_name)
            shutil.copy2(image_path, temp_image_path)

            if not temp_image_path in self.images:
                self.images.append(temp_image_path)
                self.update_image_names_label()

    def update_image_names_label(self):
        image_names = ', '.join([os.path.basename(image_name) for image_name in self.images])
        self.image_list.setText(image_names)

    def send(self, controller):
        try:
            s = sett()
            splanes_full_path = PathBuilder.splanes_file()
            save_splanes_to_file(controller.model.splanes, splanes_full_path)
            sett().slicing.splanes_file = path.basename(splanes_full_path)
            controller.save_settings("vip")

            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            self.archive_path = f"temp/{current_datetime}.zip"

            self.addFolderToArchive(self.archive_path, PathBuilder.project_path(), "project")
            self.addFolderToArchive(self.archive_path, self.temp_images_folder, "images")

            with zipfile.ZipFile(self.archive_path, 'a') as archive:
                archive.writestr("error_description.txt", self.error_description.toPlainText())

            send_bug_report(self.archive_path)

            self.cleaningTempFiles()
            self.close()

            message_box = QMessageBox(parent=self)
            message_box.setWindowTitle(controller.view.locale.SubmittingBugReport)
            message_box.setText(controller.view.locale.ReportSubmitSuccessfully)
            message_box.setIcon(QMessageBox.Information)
            message_box.exec_()

        except Exception as e:
            self.cleaningTempFiles()
            self.close()

            message_box = QMessageBox(parent=self)
            message_box.setWindowTitle(controller.view.locale.SubmittingBugReport)
            message_box.setText(controller.view.locale.ErrorReport)
            message_box.setIcon(QMessageBox.Critical)
            message_box.exec_()

    def addFolderToArchive(self, archive_path, folder_path, subfolder = ""):
        with zipfile.ZipFile(archive_path, 'a') as archive:
            for path, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(path, file)
                    archive_relative_path = os.path.relpath(file_path, folder_path)
                    if subfolder:
                        archive.write(file_path, os.path.join(subfolder, archive_relative_path))
                    else:
                        archive.write(file_path, archive_relative_path)

    def closeEvent(self, event):
        self.cleaningTempFiles()
        event.accept()

    def cancel(self):
        self.cleaningTempFiles()
        self.close()

    def cleaningTempFiles(self):
        for image_path in self.images:
            os.remove(image_path)
        if self.archive_path:
            os.remove(self.archive_path)
            self.archive_path = ""
        self.images = []
        self.image_list.setText("")
        self.error_description.setText("")