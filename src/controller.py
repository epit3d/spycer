import os
import subprocess
import sys
from functools import partial
from pathlib import Path
from shutil import copy2

from PyQt5 import QtCore
import vtk

from src import gui_utils, locales
from src.gui_utils import showErrorDialog, plane_tf, isfloat
from src.settings import sett, save_settings


class MainController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self._connect_signals()

    def _connect_signals(self):
        self.view.open_action.triggered.connect(self.open_file)
        self.view.save_sett_action.triggered.connect(partial(self.save_settings, "vip"))
        self.view.contacts_about_action.triggered.connect(self.view.about_dialog)

        # right panel
        self.view.model_switch_box.stateChanged.connect(self.view.switch_stl_gcode)
        self.view.picture_slider.valueChanged.connect(self.change_layer_view)
        self.view.smoothSlice_button.clicked.connect(self.slice_smooth)
        self.view.move_button.clicked.connect(self.move_model)
        self.view.load_model_button.clicked.connect(self.open_file)
        self.view.edit_planes_button.clicked.connect(partial(self.load_stl, None))
        self.view.slice3a_button.clicked.connect(partial(self.slice_stl, "3axes"))
        self.view.slice_vip_button.clicked.connect(partial(self.slice_stl, "vip"))
        self.view.save_gcode_button.clicked.connect(self.save_gcode_file)
        self.view.analyze_model_button.clicked.connect(self.analyze_model)
        self.view.color_model_button.clicked.connect(self.colorize_model)

        # bottom panel
        self.view.add_plane_button.clicked.connect(self.add_splane)
        self.view.splanes_list.currentItemChanged.connect(self.change_combo_select)
        self.view.remove_plane_button.clicked.connect(self.remove_splane)
        self.view.tilted_checkbox.stateChanged.connect(
            partial(self.apply_slider_change, self.view.rotated_value, self.view.rotSlider))
        self.view.hide_checkbox.stateChanged.connect(self.view.hide_splanes)
        self.view.x_value.editingFinished.connect(
            partial(self.apply_field_change, self.view.x_value, self.view.xSlider))
        self.view.y_value.editingFinished.connect(
            partial(self.apply_field_change, self.view.y_value, self.view.ySlider))
        self.view.z_value.editingFinished.connect(
            partial(self.apply_field_change, self.view.z_value, self.view.zSlider))
        self.view.rotated_value.editingFinished.connect(
            partial(self.apply_field_change, self.view.rotated_value, self.view.rotSlider))
        self.view.xSlider.valueChanged.connect(partial(self.apply_slider_change, self.view.x_value, self.view.xSlider))
        self.view.ySlider.valueChanged.connect(partial(self.apply_slider_change, self.view.y_value, self.view.ySlider))
        self.view.zSlider.valueChanged.connect(partial(self.apply_slider_change, self.view.z_value, self.view.zSlider))
        self.view.rotSlider.valueChanged.connect(
            partial(self.apply_slider_change, self.view.rotated_value, self.view.rotSlider))

    def change_layer_view(self):
        self.model.current_slider_value = self.view.change_layer_view(self.model.current_slider_value, self.model.gcode)

    def move_model(self):
        self.view.move_stl2()

    def open_file(self):
        try:
            filename = str(self.view.open_dialog())
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".STL":
                    self.load_stl(filename)
                elif file_ext == ".GCODE":
                    self.load_gcode(filename, False)
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def load_stl(self, filename, colorize=False):
        if filename is None or filename is "":
            filename = self.model.opened_stl
        stl_actor, self.model.stl_translation, _ = gui_utils.createStlActorInOrigin(filename, colorize)

        self.model.opened_stl = filename
        self.view.load_stl(stl_actor, self.model.stl_translation)

    def load_gcode(self, filename, is_from_stl):
        gc = self.model.load_gcode(filename)
        blocks = gui_utils.makeBlocks(gc.layers)
        actors = gui_utils.wrapWithActors(blocks, gc.rotations, gc.lays2rots)

        self.view.load_gcode(actors, is_from_stl, plane_tf(gc.rotations[-1]))

    def slice_stl(self, slicing_type):
        if slicing_type == "vip" and len(self.model.splanes) == 0:
            showErrorDialog(locales.getLocale().AddOnePlaneError)
            return

        s = sett()
        save_splanes_to_file(self.model.splanes, s.slicing.splanes_file)
        self.save_settings(slicing_type)

        call_command(s.slicing.cmd)

        self.load_gcode(s.slicing.gcode_file, True)
        # self.debugMe()

    def slice_smooth(self):
        s = sett()
        self.save_settings("smooth")

        ft_cmd = s.slicing.ftetwild_cmd.replace("sett.slicing.stl_file", s.slicing.stl_file)
        call_command(ft_cmd)
        call_command(s.slicing.smooth_cmd)
        self.load_gcode(s.slicing.gcode_file, True)

    def save_settings(self, slicing_type):
        s = sett()
        s.slicing.stl_file = self.model.opened_stl
        s.slicing.originx = self.model.stl_translation[0]
        s.slicing.originy = self.model.stl_translation[1]
        s.slicing.originz = self.model.stl_translation[2]
        s.slicing.layer_height = float(self.view.layer_height_value.text())
        s.slicing.print_speed = int(self.view.print_speed_value.text())
        s.slicing.print_speed_layer1 = int(self.view.print_speed_layer1_value.text())
        s.slicing.print_speed_wall = int(self.view.print_speed_wall_value.text())
        s.slicing.extruder_temperature = int(self.view.extruder_temp_value.text())
        s.slicing.bed_temperature = int(self.view.bed_temp_value.text())
        s.slicing.fill_density = int(self.view.fill_density_value.text())
        s.slicing.wall_thickness = float(self.view.wall_thickness_value.text())
        s.slicing.line_width = float(self.view.line_width_value.text())
        s.slicing.filling_type = locales.getLocaleByLang("en").FillingTypeValues[
            self.view.filling_type_values.currentIndex()]
        s.slicing.retraction_on = self.view.retraction_on_box.isChecked()
        s.slicing.retraction_distance = float(self.view.retraction_distance_value.text())
        s.slicing.retraction_speed = int(self.view.retraction_speed_value.text())
        s.slicing.support_offset = float(self.view.support_offset_value.text())
        s.slicing.skirt_line_count = int(self.view.skirt_line_count_value.text())
        s.slicing.fan_off_layer1 = self.view.fan_off_layer1_box.isChecked()
        s.slicing.fan_speed = int(self.view.fan_speed_value.text())
        s.slicing.supports_on = self.view.supports_on_box.isChecked()
        s.slicing.angle = int(self.view.colorize_angle_value.text())

        s.slicing.slicing_type = slicing_type

        save_settings()

    def save_gcode_file(self):
        try:
            name = str(self.view.save_gcode_dialog())
            if name != "":
                if not name.endswith(".gcode"):
                    name += ".gcode"
                copy2(self.model.opened_gcode, name)
        except IOError as e:
            showErrorDialog("Error during file saving:" + str(e))

    def analyze_model(self):
        self.save_settings("vip")

        s = sett()
        call_command(s.analyzer.cmd)
        self.model.planes = gui_utils.read_planes(s.analyzer.result)
        self.load_stl(self.model.opened_stl)

    def colorize_model(self):
        self.save_settings("vip")

        s = sett()
        call_command(s.colorizer.cmd)
        self.load_stl(self.model.opened_stl, colorize=True)

    # ######################bottom panel

    def add_splane(self):
        self.model.add_splane()
        self.view.reload_splanes(self.model.splanes)

    def remove_splane(self):
        ind = self.view.splanes_list.currentRow()
        if ind == -1:
            return
        del self.model.splanes[ind]
        self.view.reload_splanes(self.model.splanes)

    def change_combo_select(self):
        ind = self.view.splanes_list.currentRow()
        if ind == -1:
            return
        self.view.change_combo_select(self.model.splanes[ind], ind)

    def apply_field_change(self, field, slider):
        if isfloat(field.text()):
            slider.setValue(float(field.text()))
        else:
            field.setText(str(slider.value()))
            showErrorDialog(locales.getLocale().FloatParsingError)
        self.update_splane_common()

    def apply_slider_change(self, field, slider):
        field.setText(str(slider.value()))
        self.update_splane_common()

    def update_splane_common(self):
        center = [float(self.view.x_value.text()), float(self.view.y_value.text()), float(self.view.z_value.text())]
        ind = self.view.splanes_list.currentRow()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Plane(self.view.tilted_checkbox.isChecked(),
                                                  float(self.view.rotSlider.value()), center)
        self.view.update_splane(self.model.splanes[ind], ind)

    # def debugMe(self):
    #     debug.readFile(self.render, "/home/l1va/debug.txt", 4)
    #     # debug.readFile(self.render, "/home/l1va/debug_simplified.txt", "Red", 3)
    #     self.reloadScene()


def call_command(cmd):
    try:
        cmds = cmd.split(" ")
        # print(cmds)
        subprocess.check_output(cmds, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as er:
        print("Error:", sys.exc_info())
        print("Error2:", er.output)
        gui_utils.showErrorDialog(repr(er.output))


def save_splanes_to_file(splanes, filename):
    with open(filename, 'w') as out:
        for p in splanes:
            out.write(p.toFile() + '\n')
