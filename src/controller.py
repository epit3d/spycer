import os
from functools import partial
from pathlib import Path
from shutil import copy2

from PyQt5 import QtCore
import vtk

from src import gui_utils, gcode, locales
from src.gui_utils import showErrorDialog, planeTf, isfloat
from src.locales import Locale


class MainController:
    def __init__(self, view, model):
        self.view = view
        self.model = model
        self._connect_signals()

    def _connect_signals(self):
        # right panel
        self.view.model_switch_box.stateChanged.connect(self.switch_models)
        self.view.picture_slider.valueChanged.connect(self.change_layer_view)
        self.view.move_button.clicked.connect(self.move_model)
        self.view.load_model_button.clicked.connect(self.open_file)
        self.view.edit_planes_button.clicked.connect(partial(self.load_stl, self.model.opened_stl, load_planes=True))
        self.view.slice3a_button.clicked.connect(partial(self.slice_stl, "3axes"))
        self.view.slice_vip_button.clicked.connect(partial(self.slice_stl, "vip"))
        self.view.save_gcode_button.clicked.connect(self.save_gcode_file)
        self.view.analyze_model_button.clicked.connect(self.analyze_model)
        self.view.color_model_button.clicked.connect(self.colorize_model)

        # bottom panel
        self.view.add_plane_button.clicked.connect(self.add_splane)
        self.view.combo_box.currentIndexChanged.connect(self.change_combo_select)
        self.view.remove_plane_button.clicked.connect(self.remove_splane)
        self.view.tilted_checkbox.stateChanged.connect(
            partial(self.apply_slider_change, self.view.rotated_value, self.view.rotSlider))
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

    def switch_models(self, state):
        if state == QtCore.Qt.Checked:
            self.view.show_stl_hide_gcode()
        else:
            self.view.show_gcode_hide_stl()
        self.view.reload_scene()

    def change_layer_view(self):
        self.model.current_slider_value = self.view.change_layer_view(self.model.current_slider_value)

    def move_model(self):
        tf = [float(self.view.x_position_value.text()), float(self.view.y_position_value.text()),
              float(self.view.z_position_value.text())]
        self.model.stl_translation = tf

        vtk_tf = vtk.vtkTransform()
        vtk_tf.Translate(tf[0], tf[1], tf[2])
        self.view.move_stl(vtk_tf)

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

    def load_stl(self, filename, method=gui_utils.createStlActorInOrigin, load_planes=False):
        stl_actor, self.model.stl_translation, _ = method(filename)  # TODO:

        self.model.opened_stl = filename
        self.view.load_stl(stl_actor, self.model.stl_translation)
        if load_planes:
            self.view.load_splanes(self.model.splanes)

    def load_gcode(self, filename, addStl):
        gc = self.model.load_gcode(filename)
        blocks = gui_utils.makeBlocks(gc.layers)
        actors = gui_utils.wrapWithActors(blocks, gc.rotations, gc.lays2rots)

        self.view.load_gcode(actors, addStl, planeTf(gc.rotations[-1]))

    def slice_stl(self, slicing_type):
        pass
        # if slicing_type == "vip" and len(self.model.planes)==0:
        #     showErrorDialog(self.locale.AddOnePlaneError)
        #     return
        # values = {
        #     "stl": format_path(self.openedStl),
        #     "gcode": params.OutputGCode,
        #     "originx": self.stlTranslation[0],
        #     "originy": self.stlTranslation[1],
        #     "originz": self.stlTranslation[2],
        #     "rotcx": params.RotationCenter[0],
        #     "rotcy": params.RotationCenter[1],
        #     "rotcz": params.RotationCenter[2],
        #
        #     "layer_height": self.layer_height_value.text(),
        #     "wall_thickness": self.wallThickness_value.text(),
        #     "fill_density": self.fillDensity_value.text(),
        #     "bed_temperature": self.bedTemp_value.text(),
        #     "extruder_temperature": self.extruderTemp_value.text(),
        #     "print_speed": self.printSpeed_value.text(),
        #     "print_speed_layer1": self.printSpeedLayer1_value.text(),
        #     "print_speed_wall": self.printSpeedWall_value.text(),
        #     "line_width": self.line_width_value.text(),
        #     "filling_type": locales.getLocaleByLang("en").FillingTypeValues[self.filling_type_values.currentIndex()],
        #     "slicing_type": slicing_type,
        #     "planes_file": params.PlanesFile,
        #     "angle": self.colorizeAngle_value.text(),
        #     "retraction_speed": self.retractionSpeed_value.text(),
        #     "retraction_distance": self.retractionDistance_value.text(),
        #     "support_offset": self.supportOffset_value.text(),
        #     "skirt_line_count": self.skirtLineCount_value.text()
        # }
        # self.savePlanesToFile()
        #
        # # Prepare a slicing command line command
        # cmd = params.SliceCommand.format(**values)
        # if self.fanOffLayer1_box.isChecked():
        #     cmd += " --fan_off_layer1"
        # if self.retractionOn_box.isChecked():
        #     cmd += " --retraction_on"
        # if self.supportsOn.isChecked():
        #     cmd += " --supports_on"
        #
        # call_command(cmd)
        # self.stlActor.VisibilityOff()
        # self.loadGCode(params.OutputGCode, True)
        # self.debugMe()

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
        pass
        # values = {
        #     "stl": format_path(self.openedStl),
        #     "angle": self.colorizeAngle_value.text(),
        #     "out": params.AnalyzeResult,
        #     "originx": self.stlTranslation[0],
        #     "originy": self.stlTranslation[1],
        #     "originz": self.stlTranslation[2],
        #     "rotcx": params.RotationCenter[0],
        #     "rotcy": params.RotationCenter[1],
        #     "rotcz": params.RotationCenter[2],
        # }
        # cmd = params.AnalyzeStlCommand.format(**values)
        # call_command(cmd)
        # self.planes = gui_utils.read_planes()
        # self.bottom_panel.setEnabled(True)
        # # self.openedStl = "cuttedSTL.stl"
        # self.loadSTL(self.openedStl, method=gui_utils.createStlActorInOrigin)

    def colorize_model(self):
        pass
        # values = {
        #     "stl": format_path(self.openedStl),
        #     "out": params.ColorizeResult,
        #     "angle": self.colorizeAngle_value.text(),
        # }
        # cmd = params.ColorizeStlCommand.format(**values)
        # call_command(cmd)
        # self.loadSTL(self.openedStl, method=gui_utils.createStlActorInOriginWithColorize)

    ################ bottom panel

    def add_splane(self):
        self.model.add_splane()
        self.view.load_splanes(self.model.splanes)

    def remove_splane(self):
        ind = self.view.combo_box.currentIndex()
        if ind == -1:
            return
        del self.model.splanes[ind]
        self.view.load_splanes(self.model.splanes)

    def change_combo_select(self):
        ind = self.view.combo_box.currentIndex()
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
        ind = self.view.combo_box.currentIndex()
        if ind == -1:
            return
        self.model.splanes[ind] = gui_utils.Plane(self.view.tilted_checkbox.isChecked(),
                                                  float(self.view.rotSlider.value()), center)
        self.view.update_splane(self.model.splanes[ind], ind)
