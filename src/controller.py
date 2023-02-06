import logging
import math
import os
import subprocess
import time
import sys
from functools import partial
from pathlib import Path
from shutil import copy2
from typing import Dict, List

import vtk
import shutil
from PyQt5 import QtCore
from PyQt5.QtWidgets import QDesktopWidget

from src import gui_utils, locales
from src.cone_slicing import cross_stl, load_mesh
from src.figure_editor import PlaneEditor, ConeEditor
from src.gcode import GCode, Rotation, Point
from src.gui_utils import showErrorDialog, plane_tf, isfloat, read_planes, Plane, Cone
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
        self.view.model_centering_box.stateChanged.connect(self.view.model_centering)
        self.view.picture_slider.valueChanged.connect(self.change_layer_view)
        self.view.smoothSlice_button.clicked.connect(partial(self.slice_smooth, 0))
        self.view.smoothFlatSlice_button.clicked.connect(partial(self.slice_smooth, 1))
        self.view.move_button.clicked.connect(self.move_model)
        self.view.load_model_button.clicked.connect(self.open_file)
        self.view.edit_planes_button.clicked.connect(partial(self.load_stl, None))
        self.view.slice3a_button.clicked.connect(partial(self.slice_stl, "3axes"))
        self.view.slice_vip_button.clicked.connect(partial(self.slice_stl, "vip"))
        self.view.slice_cone_button.clicked.connect(self.slice_cone)
        self.view.save_gcode_button.clicked.connect(self.save_gcode_file)
        self.view.analyze_model_button.clicked.connect(self.analyze_model)
        self.view.color_model_button.clicked.connect(self.colorize_model)

        # bottom panel
        self.view.add_plane_button.clicked.connect(self.add_splane)
        self.view.add_cone_button.clicked.connect(self.add_cone)
        self.view.edit_figure_button.clicked.connect(self.change_figure_parameters)
        self.view.save_planes_button.clicked.connect(self.save_planes)
        self.view.download_planes_button.clicked.connect(self.download_planes)
        self.view.remove_plane_button.clicked.connect(self.remove_splane)
        self.view.splanes_tree.itemDoubleClicked.connect(self.change_splanes_tree)
        self.view.splanes_tree.itemChanged.connect(self.change_figure_check_state)
        self.view.splanes_tree.currentItemChanged.connect(self.change_combo_select)
        self.view.splanes_tree.model().rowsInserted.connect(self.moving_figure)

        self.view.hide_checkbox.stateChanged.connect(self.view.hide_splanes)

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
            return

        # allow to show only one tooling for all figures
        if self.view.parameters_tooling and not self.view.parameters_tooling.isHidden():
            self.view.parameters_tooling.close()

        if isinstance(self.model.splanes[ind], Plane):
            self.view.parameters_tooling = PlaneEditor(self.update_plane_common, self.model.splanes[ind].params())
        elif isinstance(self.model.splanes[ind], Cone):
            self.view.parameters_tooling = ConeEditor(self.update_cone_common, self.model.splanes[ind].params())

        try:
            main_window_left_pos = self.view.mapToGlobal(QtCore.QPoint(0, 0)).x()
            self.view.parameters_tooling.move(main_window_left_pos,
                                              self.view.height() - self.view.parameters_tooling.height() / 3)
        except:
            # everything could happen, but nothing should be broken
            ...

        self.view.parameters_tooling.show()

    def save_planes(self):
        try:
            filename = str(self.view.save_dialog(self.view.locale.SavePlanes, "TXT (*.txt *.TXT)"))
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
                        self.model.splanes = read_planes(filename)
                        self.view.reload_splanes(self.model.splanes)
                    except:
                        showErrorDialog("Error during reading planes file")
                else:
                    showErrorDialog(
                        "This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def change_layer_view(self):
        self.model.current_slider_value = self.view.change_layer_view(self.model.current_slider_value, self.model.gcode)

    def move_model(self):
        self.view.move_stl2()

    def open_file(self):
        try:
            filename = str(self.view.open_dialog(self.view.locale.OpenModel))
            if filename != "":
                file_ext = os.path.splitext(filename)[1].upper()
                filename = str(Path(filename))
                if file_ext == ".STL":
                    s = sett()
                    s.slicing.originx, s.slicing.originy, s.slicing.originz = 0, 0, 0
                    s.slicing.rotationx, s.slicing.rotationy, s.slicing.rotationz = 0, 0, 0
                    s.slicing.scalex, s.slicing.scaley, s.slicing.scalez = 1, 1, 1
                    s.slicing.model_centering = False
                    s.slicing.print_time = 0
                    s.slicing.consumption_material = 0
                    save_settings()
                    self.update_interface_by_gcode()

                    self.view.model_centering_box.setChecked(False)

                    if os.path.isfile(s.colorizer.copy_stl_file):
                        os.remove(s.colorizer.copy_stl_file)

                    self.load_stl(filename)
                elif file_ext == ".GCODE":
                    self.load_gcode(filename, False)
                    self.update_interface_by_gcode()
                else:
                    showErrorDialog("This file format isn't supported:" + file_ext)
        except IOError as e:
            showErrorDialog("Error during file opening:" + str(e))

    def load_stl(self, filename, colorize=False):
        if filename is None or filename == "":
            filename = self.model.opened_stl
        stl_actor = gui_utils.createStlActorInOrigin(filename, colorize)
        self.model.opened_stl = filename
        self.view.load_stl(stl_actor)

    def load_gcode(self, filename, is_from_stl):
        print("start parsing gcode")
        start_time = time.time()
        gc = self.model.load_gcode(filename)
        print('finish parsing gcode')
        end_time = time.time()
        print('spent time for gcode loading: ', end_time - start_time, 's')
        blocks = gui_utils.makeBlocks(gc.layers, gc.rotations, gc.lays2rots)
        actors = gui_utils.wrapWithActors(blocks, gc.rotations, gc.lays2rots)

        self.view.load_gcode(actors, is_from_stl, plane_tf(gc.rotations[0]))

    def slice_stl(self, slicing_type):
        if slicing_type == "vip" and len(self.model.splanes) == 0:
            showErrorDialog(locales.getLocale().AddOnePlaneError)
            return

        s = sett()
        save_splanes_to_file(self.model.splanes, s.slicing.splanes_file)
        self.save_settings(slicing_type)

        start_time = time.time()
        print("start slicing")
        res = call_command(s.slicing.cmd)
        print("finished command")
        end_time = time.time()
        print('spent time for slicing: ', end_time - start_time, 's')

        if not res:
            return

        self.load_gcode(s.slicing.gcode_file, True)
        print("loaded gcode")
        # self.debugMe()
        self.update_interface_by_gcode()

    def slice_cone(self):
        # print(self.model.splanes)
        self.save_settings("cone")
        if len(self.model.splanes) == 0 or not isinstance(self.model.splanes[0], Cone):
            showErrorDialog(self.view.locale.AddOneConeError)
            return

        cone = self.model.splanes[0]
        # slicing runs somewhere here
        # print(f"slicing is performed for model {self.model.opened_stl}")
        result = cross_stl(load_mesh(self.model.opened_stl),
                           (cone.cone_angle, (cone.x, cone.y, cone.z)))
        # print("result", result)

        new_res = []

        for layer in result:
            new_layer = []
            for [point1, point2] in layer:
                new_layer.append([Point(*point1, 0, 0), Point(*point2, 0, 0)])
            new_res.append(new_layer)

        # result is layer-separated list of segments
        gcode = GCode(new_res, [Rotation(0, 0)], [0] * len(new_res))
        self.model.gcode = gcode
        blocks = gui_utils.makeBlocks(gcode.layers, gcode.rotations, gcode.lays2rots)
        actors = gui_utils.wrapWithActors(blocks, gcode.rotations, gcode.lays2rots)

        self.view.load_gcode(actors, True, 0)

    def slice_smooth(self, flat5d):
        s = sett()
        s.slicing.flat_5d = flat5d
        self.save_settings("smooth")

        ft_cmd = s.slicing.ftetwild_cmd.replace("sett.slicing.stl_file", s.slicing.stl_file)
        call_command(ft_cmd)
        call_command(s.slicing.smooth_cmd)
        self.load_gcode(s.slicing.gcode_file, True)

    def save_settings(self, slicing_type):
        s = sett()
        s.slicing.stl_file = self.model.opened_stl
        tf = vtk.vtkTransform()
        if self.view.stlActor is not None:
            tf = self.view.stlActor.GetUserTransform()
        s.slicing.originx, s.slicing.originy, s.slicing.originz = tf.GetPosition()
        s.slicing.rotationx, s.slicing.rotationy, s.slicing.rotationz = tf.GetOrientation()
        s.slicing.scalex, s.slicing.scaley, s.slicing.scalez = tf.GetScale()
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

        s.slicing.overlapping_infill_percentage = float(self.view.overlapping_infill_value.text())

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
        shutil.copyfile(s.slicing.stl_file, s.colorizer.copy_stl_file)
        save_splanes_to_file(self.model.splanes, s.slicing.splanes_file)
        call_command(s.colorizer.cmd)
        lastMove = self.view.stlActor.lastMove
        self.load_stl(s.colorizer.copy_stl_file, colorize=True)
        self.view.stlActor.lastMove = lastMove
        self.model.opened_stl = s.slicing.stl_file


    # ######################bottom panel

    def add_splane(self):
        self.model.add_splane()
        self.view.reload_splanes(self.model.splanes)

    def add_cone(self):
        self.model.add_cone()
        self.view.reload_splanes(self.model.splanes)

    def remove_splane(self):
        ind = self.view.splanes_tree.currentIndex().row()
        if ind == -1:
            return
        del self.model.splanes[ind]
        self.view.splanes_tree.takeTopLevelItem(ind)
        self.view.reload_splanes(self.model.splanes)
        if len(self.model.splanes) == 0:
            if self.view.parameters_tooling and not self.view.parameters_tooling.isHidden():
                self.view.parameters_tooling.close()

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

    # def debugMe(self):
    #     debug.readFile(self.render, "/home/l1va/debug.txt", 4)
    #     # debug.readFile(self.render, "/home/l1va/debug_simplified.txt", "Red", 3)
    #     self.reloadScene()

    def update_interface_by_gcode(self):
        s = sett()
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

        self.view.print_time_value.setText(self.view.locale.PrintTime + string_print_time)

        string_consumption_material = ""
        if s.slicing.consumption_material > 0:
            material_weight = (s.slicing.consumption_material * math.pow(s.hardware.bar_diameter/2, 2) * math.pi) * s.hardware.density / 1000
            string_consumption_material += str(math.ceil(material_weight)) + " " + self.view.locale.Gram + ", "
            string_consumption_material += str(float("{:.2f}".format(s.slicing.consumption_material/1000))) + " " + self.view.locale.Meter

        self.view.consumption_material_value.setText(self.view.locale.ConsumptionMaterial + string_consumption_material)

def call_command(cmd) -> bool:
    try:
        cmds = cmd.split(" ")
        # print(cmds)
        subprocess.check_output(cmds, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as er:
        print("Error:", sys.exc_info())
        print("Error2:", er.output)
        logging.error(str(sys.exc_info()))
        gui_utils.showErrorDialog(repr(er.output))
        return False
    except:
        print("Error:", sys.exc_info())
        logging.error(str(sys.exc_info()))
        # print("Error2:", er.output)
        gui_utils.showErrorDialog(str(sys.exc_info()))
        return False
    
    # return positive that we can load new gcode from file and it for sure will be new
    return True


def save_splanes_to_file(splanes, filename):
    with open(filename, 'w') as out:
        for p in splanes:
            out.write(p.toFile() + '\n')
