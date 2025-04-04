from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtWidgets import (
    QWidget,
    QLabel,
    QLineEdit,
    QGridLayout,
    QCheckBox,
    QPushButton,
    QComboBox,
    QStyle,
    QSpinBox,
    QDoubleSpinBox,
    QToolBox,
    QSizePolicy,
)

from src import locales
from src.settings import sett, APP_PATH, Settings, read_settings
from src.qt_utils import ClickableLineEdit, LineEdit

import os.path as path
import logging
import re

# Regular expression to find floats. Match groups are the whole string, the
# whole coefficient, the decimal part of the coefficient, and the exponent
# part.
_float_re = re.compile(r"(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)")


def valid_float_string(string):
    match = _float_re.search(string)
    return match.groups()[0] == string if match else False


class FloatValidator(QtGui.QValidator):
    def validate(self, string, position):
        if valid_float_string(string):
            return self.State.Acceptable
        if string == "" or string[position - 1] in "e.-+":
            return self.State.Intermediate
        return self.State.Invalid

    def fixup(self, text):
        match = _float_re.search(text)
        return match.groups()[0] if match else ""


class SettingsWidget(QToolBox):
    """
    Settings widget defines a way to create a widget with chosen number of settings inside
    """

    col2_cells = 4
    validatorLocale = QtCore.QLocale("Englishs")
    intValidator = QtGui.QIntValidator(0, 9000)

    doubleValidator = QtGui.QDoubleValidator(0.00, 9000.00, 2)
    doubleValidator.setLocale(validatorLocale)

    doublePercentValidator = QtGui.QDoubleValidator(0.00, 9000.00, 2)
    doublePercentValidator.setLocale(validatorLocale)

    parameters = [
        "printer_path",
        "uninterrupted_print",
        "m10_cut_distance",
        "line_width",
        "layer_height",
        "number_wall_lines",
        "number_of_bottom_layers",
        "number_of_lids_layers",
        "extruder_temp",
        "bed_temp",
        "skirt_line_count",
        "fan_speed",
        "fan_off_layer1",
        "print_speed",
        "print_speed_layer1",
        "print_speed_wall",
        "filling_type",
        "fill_density",
        "minimum_fill_area",
        "overlap_infill",
        "retraction_on",
        "retraction_distance",
        "retraction_speed",
        "retraction_compensation",
        "material_shrinkage",
        "flow_rate",  # Коэффициент потока расплава
        "pressure_advance_on",
        "pressure_advance",
        "random_layer_start",
        "is_wall_outside_in",
        "auto_fan_enabled",
        "auto_fan_area",
        "auto_fan_speed",
        # TODO: add separate dummy setting to mark the beginning of supports settings
        "supports_on",
        "support_density",
        "support_fill_type",
        "support_xy_offset",
        "support_z_offset",
        "support_priority_zoffset",
        "support_number_of_bottom_layers",
        "support_number_of_lid_layers",
        "support_create_walls",
        "critical_angle",
    ]

    GROUPING = {
        "model": [
            "printer_path",
            "layer_height",
            "line_width",
            "number_wall_lines",
            "number_of_bottom_layers",
            "number_of_lids_layers",
            "is_wall_outside_in",
            "supports_on",
            "support_density",
            "support_z_offset",
            "support_priority_zoffset",
            "support_xy_offset",
            "support_number_of_bottom_layers",
            "support_number_of_lid_layers",
            "support_create_walls",
            "critical_angle",
            "skirt_line_count",
        ],
        "material": [
            "extruder_temp",
            "bed_temp",
            "fan_speed",
            "fan_off_layer1",
            "auto_fan_enabled",
            "auto_fan_area",
            "auto_fan_speed",
            "retraction_on",
            "retraction_distance",
            "retraction_speed",
            "retraction_compensation",
            "pressure_advance_on",
            "pressure_advance",
            "material_shrinkage",
            "uninterrupted_print",
            "m10_cut_distance",
            "print_speed",
            "print_speed_layer1",
            "print_speed_wall",
            "filling_type",
            "support_fill_type",
            "fill_density",
            "minimum_fill_area",
            "overlap_infill",
            "random_layer_start",
            "flow_rate",
        ],
    }

    # extra parameters are only used for a small widget with parameters for each figure specifically
    # also in corresponding branch "setting" key should point to the correct setting
    extra_sett_parameters = [
        "filling_type",
        "fill_density",
        "fan_speed",
    ]

    def __init__(
        self,
        parent=None,
        settings_provider: callable = None,
        use_grouping=True,
    ):
        super(SettingsWidget, self).__init__(parent)

        assert settings_provider is not None, "Settings provider is required"

        self.sett = settings_provider

        # TODO: Load the bundled settings
        self.bundled_settings = Settings(read_settings(filename=None))

        self.locale: locales.Locale = locales.getLocale()
        # create panels depending on the alignment of the widget
        self.use_grouping = use_grouping
        if self.use_grouping:
            from PyQt5.QtWidgets import QScrollArea

            self.layouts = {}
            for group in self.GROUPING.keys():
                page = QWidget()
                page.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
                page.setObjectName(group)
                layout = QGridLayout(page)
                layout.setVerticalSpacing(10)
                layout.setHorizontalSpacing(10)
                layout.setContentsMargins(10, 10, 10, 10)
                layout.setColumnStretch(1, 1)
                layout.setColumnStretch(3, 1)
                layout.setColumnStretch(4, 1)
                self.layouts[group] = layout

                scroll = QScrollArea()
                scroll.setWidget(page)
                scroll.setWidgetResizable(True)
                self.addItem(
                    scroll,
                    self.locale.GroupNames.get(group, f"{group.capitalize()} settings"),
                )
        else:
            page1 = QWidget()
            page1.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            page1.setObjectName("page1")

            self.layouts = {
                "default": QGridLayout(page1),
            }

            for k, v in self.layouts.items():
                from PyQt5.QtWidgets import QLayout

                v.setSizeConstraint(QLayout.SetFixedSize)
                v.setVerticalSpacing(10)
                v.setHorizontalSpacing(10)
                v.setContentsMargins(10, 10, 10, 10)
                v.setColumnStretch(1, 1)
                v.setColumnStretch(3, 1)
                v.setColumnStretch(4, 1)
            from PyQt5.QtWidgets import QScrollArea

            scroll = QScrollArea()
            scroll.setWidget(page1)
            scroll.setWidgetResizable(True)
            self.addItem(scroll, self.locale.Settings)

        self.__rows = {}

        self.__elements = {}
        self.__order = []  # order of keys in the panel from top to bottom

        self.__current_row = 1

        self.translation = {
            "printer_path": self.locale.PrinterName,
            "uninterrupted_print": self.locale.UninterruptedPrint,
            "m10_cut_distance": self.locale.M10CutDistance,
            "line_width": self.locale.LineWidth,
            "layer_height": self.locale.LayerHeight,
            "number_wall_lines": self.locale.NumberWallLines,
            "number_of_bottom_layers": self.locale.NumberOfBottomLayers,
            "number_of_lids_layers": self.locale.NumberOfLidLayers,
            "extruder_temp": self.locale.ExtruderTemp,
            "bed_temp": self.locale.BedTemp,
            "skirt_line_count": self.locale.SkirtLineCount,
            "fan_speed": self.locale.FanSpeed,
            "fan_off_layer1": self.locale.FanOffLayer1,
            "print_speed": self.locale.PrintSpeed,
            "print_speed_layer1": self.locale.PrintSpeedLayer1,
            "print_speed_wall": self.locale.PrintSpeedWall,
            "filling_type": self.locale.FillingType,
            "fill_density": self.locale.FillDensity,
            "minimum_fill_area": self.locale.MinimumFillArea,
            "overlap_infill": self.locale.OverlappingInfillPercentage,
            "retraction_on": self.locale.Retraction,
            "retraction_distance": self.locale.RetractionDistance,
            "retraction_speed": self.locale.RetractionSpeed,
            "retraction_compensation": self.locale.RetractCompensationAmount,
            "material_shrinkage": self.locale.MaterialShrinkage,
            "random_layer_start": self.locale.RandomLayerStart,
            "is_wall_outside_in": self.locale.IsWallsOutsideIn,
            # TODO: add separate dummy setting to mark the beginning of supports settings
            "supports_on": self.locale.SupportsOn,
            "support_density": self.locale.SupportDensity,
            "support_fill_type": self.locale.FillingType,
            "support_xy_offset": self.locale.SupportXYOffset,
            "support_z_offset": self.locale.SupportZOffsetLayers,
            "support_priority_zoffset": self.locale.SupportPriorityZOffset,
            "support_number_of_bottom_layers": self.locale.NumberOfBottomLayers,
            "support_number_of_lid_layers": self.locale.NumberOfLidLayers,
        }

    def get_panel_name(self, sett_name: str):
        # given a name of the setting, return the panel where we should append it
        if not self.use_grouping:
            return "default"

        for group, params in self.GROUPING.items():
            if sett_name in params:
                return group

        # we should have found the group
        raise ValueError(f"Group for {sett_name} not found")

    def get_panel(self, sett_name: str):
        return self.layouts[self.get_panel_name(sett_name)]

    def panel_next_row(self, sett_name: str):
        # given a name of the setting, get what is the next row in the panel, increment and return so we add it to the grid
        panel_name = self.get_panel_name(sett_name)

        if panel_name not in self.__rows:
            self.__rows[panel_name] = 1
        else:
            self.__rows[panel_name] += 1
        return self.__rows[panel_name]

    def panel_current_row(self, sett_name: str):
        # given a name of the setting, get what is the current row in the panel, return it
        panel_name = self.get_panel_name(sett_name)
        if panel_name not in self.__rows:
            self.__rows[panel_name] = 1
        return self.__rows[panel_name]

    def reload(self):
        # reloads all settings from the sett
        # right now we do it by deleting previous elements
        # and creating new ones with the same order

        # TODO: a little bit of copying, but it's ok for now
        def get_row_widgets(key, row_idx):
            widgets = []
            panel = self.get_panel(key)
            for i in range(7):  # TODO: move to constant
                item = panel.itemAtPosition(row_idx, i)
                if item is None:
                    continue
                if len(widgets) != 0 and item.widget() == widgets[-1]:
                    continue

                widgets.append((item.widget(), i))
            return widgets

        def remove_row(key, row_idx):
            panel = self.get_panel(key)
            dlt_row = get_row_widgets(key, row_idx)
            for _, col_idx in dlt_row:
                panel.itemAtPosition(row_idx, col_idx).widget().deleteLater()

            # find key by row index
            key = None
            for k in self.__elements:
                if self.__elements[k]["row_idx"] == row_idx:
                    key = k
                    break

            # remove key from elements
            del self.__elements[key]

        for key in self.__order:
            try:
                row_idx = self.__elements[key]["row_idx"]
                remove_row(row_idx)
            except KeyError:
                print(f"Key {key} not found in elements")
                pass

        self.__current_row = 1
        copied_order = self.__order.copy()
        self.__elements = {}
        self.__order = []
        for key in copied_order:
            self = self.with_sett(key)

    @property
    def cur_row(self):
        return self.__current_row

    @property
    def next_row(self):
        self.__current_row += 1
        return self.__current_row

    def edit(self, name: str):
        """
        Return editable element associated with the given name
        """
        assert name in self.__elements, f"There is no LineEdit for {name}"

        return self.__elements[name]["edit"]

    def spinbox(self, name: str):
        """
        Return spinbox element associated with the given name
        """
        assert name in self.__elements, f"There is no SpinBox/DoubleSpinBox for {name}"

        return self.__elements[name]["spinbox"]

    def checkbox(self, name: str):
        """
        Return checkbox element associated with the given name
        """
        if name not in self.__elements:
            raise KeyError(f"There is no checkbox for {name}")

        return self.__elements[name]["checkbox"]

    def values(self, name: str):
        """
        Return combobox element associated with the given name
        """
        if name not in self.__elements:
            raise KeyError(f"There is no combobox for {name}")

        return self.__elements[name]["values"]

    def get_element(self, name: str, key: str):
        """
        Return element associated with the given name and key
        """
        if name not in self.__elements:
            raise KeyError(f"There is no element for {name}")

        if key not in self.__elements[name]:
            raise KeyError(f"There is no element for {key}")

        return self.__elements[name][key]

    def with_all(self):
        for param in self.parameters:
            self.with_sett(param)
        return self

    def with_delete(self):
        """
        Adds delete button to each setting on the right
        """

        def del_sett(name: str):
            # given name with dot separation, remove from settings
            attrs = name.split(".")
            top_level = self.sett()
            for attr in attrs[:-1]:
                if not hasattr(top_level, attr):
                    return
                top_level = getattr(top_level, attr)

            delattr(top_level, attrs[-1])

        self.btns = []

        for key in self.__elements:
            row_idx = self.__elements[key]["row_idx"]
            panel = self.get_panel(key)

            # check whether this row already has delete button
            if panel.itemAtPosition(row_idx, 6) is not None:
                continue

            delete_btn = QPushButton()
            self.btns += [delete_btn]
            # set icon
            delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))
            # set background color
            delete_btn.setStyleSheet("background-color: red;")

            def get_row_widgets(row_idx):
                widgets = []
                for i in range(7):  # TODO: move to constant
                    item = panel.itemAtPosition(row_idx, i)
                    if item is None:
                        continue
                    if len(widgets) != 0 and item.widget() == widgets[-1]:
                        continue

                    widgets.append((item.widget(), i))
                return widgets

            def remove_row(row_idx):
                dlt_row = get_row_widgets(row_idx)
                for _, col_idx in dlt_row:
                    panel.itemAtPosition(row_idx, col_idx).widget().deleteLater()

                # find key by row index
                key = None
                for k in self.__elements:
                    if self.__elements[k]["row_idx"] == row_idx:
                        key = k
                        break

                # remove key from elements
                del_sett(self.__elements[key]["setting"])
                del self.__elements[key]

            delete_btn.clicked.connect(lambda _, row_idx=row_idx: remove_row(row_idx))

            # TODO: set btn index constant
            panel.addWidget(delete_btn, row_idx, 6)

        return self

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

    def ensure_sett(self, name: str):
        """
        ensure_sett creates sufficient attributes for the given setting name

        Args:
            name (str): setting name separated by dots: e.g. hardware.printer_path

        For the given name we update attributes of settings so that it becomes accessible by
        the given name. If the name is already added, we return the current instance.

        Example:
            self.ensure_sett("hardware.printer_path")
            self.sett().hardware.printer_path

        """
        attrs = name.split(".")

        # TODO: right here global top should be something different,
        # I suppose inside this widget we should load kinda
        # global settings object with the original bundled data
        # global_top = sett()
        global_top = self.bundled_settings
        top_level = self.sett()
        for idx, attr in enumerate(attrs):
            if not hasattr(top_level, attr):
                if idx != len(attrs) - 1:
                    setattr(top_level, attr, Settings({}))
                else:
                    # we have to add default settings from the main ones
                    try:
                        default = getattr(global_top, attr)
                    except AttributeError:
                        default = None
                    setattr(top_level, attr, default)

            top_level = getattr(top_level, attr)
            global_top = getattr(global_top, attr)

    def __smart_float(self, value: str):
        if not value:
            return 0.0

        try:
            return float(value.replace(",", "."))
        except ValueError:
            return 0.0

    def from_settings(self, setts: Settings):
        # given settings structure, create a widget with its parameters
        # currently works with limited number of settings

        if not setts:
            return self

        def has_setting(name: str):
            attrs = name.split(".")
            top_level = setts
            for attr in attrs:
                if not hasattr(top_level, attr):
                    return False
                top_level = getattr(top_level, attr)

            return True

        if has_setting("slicing.filling_type"):
            self.with_sett("filling_type")
        if has_setting("slicing.fill_density"):
            self.with_sett("fill_density")
        if has_setting("slicing.fan_speed"):
            self.with_sett("fan_speed")
        # TODO: this list should be increased with the growth of extra parameters

        return self

    def with_sett(self, name: str):
        # check whether the given name is already added
        if name in self.__elements:
            return self

        self.__order.append(name)

        # given setting name get the panel where we should add it
        panel = self.get_panel(name)
        panel_cur_row = lambda: self.panel_current_row(name)
        panel_next_row = lambda: self.panel_next_row(name)

        # we match the given name with each setting and add it to the layout
        if name == "printer_path":
            # self.ensure_sett("hardware.printer_path")

            printer_basename = ""
            try:
                printer_basename = path.basename(self.sett().hardware.printer_dir)
                if self.sett().hardware.printer_dir == "" or not path.isdir(
                    self.sett().hardware.printer_dir
                ):
                    # empty directory
                    raise ValueError("Choose default printer")

                logging.info(
                    f"hardware printer path is {self.sett().hardware.printer_dir}"
                )
            except ValueError:
                # set default path to printer config
                self.sett().hardware.printer_dir = path.join(
                    APP_PATH, "data", "printers", "default"
                )
                logging.info(
                    f"hardware printer path is default: {self.sett().hardware.printer_dir}"
                )
                printer_basename = path.basename(self.sett().hardware.printer_dir)

            printer_path_edit = ClickableLineEdit(printer_basename)
            printer_path_edit.setReadOnly(True)

            printer_add_btn = QPushButton("+")
            printer_add_btn.setToolTip(self.locale.AddNewPrinter)

            label = QLabel(self.locale.PrinterName)
            panel.addWidget(label, panel_next_row(), 1)
            panel.addWidget(printer_add_btn, panel_cur_row(), 2)
            panel.addWidget(printer_path_edit, panel_cur_row(), 3, 1, 3)

            self.__elements[name] = {
                "label": label,
                "edit": printer_path_edit,
                "add_btn": printer_add_btn,
                "sett_path": "hardware.printer_dir",
            }
        elif name == "uninterrupted_print":
            self.ensure_sett("uninterrupted_print.enabled")

            uninterrupted_print = QLabel(self.locale.UninterruptedPrint)
            uninterrupted_print_box = QCheckBox()
            if sett().uninterrupted_print.enabled:
                uninterrupted_print_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(QLabel(self.locale.UninterruptedPrint), panel_next_row(), 1)
            panel.addWidget(
                uninterrupted_print_box, panel_cur_row(), 2, 1, self.col2_cells
            )

            # on check on this box, we should restrict fill type to zigzag only
            def on_uninterrupted_print_change():
                self.sett().uninterrupted_print.enabled = (
                    uninterrupted_print_box.isChecked()
                )

                isUninterrupted = uninterrupted_print_box.isChecked()

                self.values("filling_type").setEnabled(not isUninterrupted)
                self.checkbox("retraction_on").setEnabled(not isUninterrupted)
                self.edit("retraction_distance").setEnabled(not isUninterrupted)
                self.edit("retraction_speed").setEnabled(not isUninterrupted)
                self.edit("retraction_compensation").setEnabled(not isUninterrupted)

                if isUninterrupted:
                    zigzag_idx = locales.getLocaleByLang("en").FillingTypeValues.index(
                        "ZigZag"
                    )
                    self.values("filling_type").setCurrentIndex(zigzag_idx)
                    self.checkbox("retraction_on").setChecked(False)

            uninterrupted_print_box.stateChanged.connect(on_uninterrupted_print_change)

            self.__elements[name] = {
                "label": uninterrupted_print,
                "checkbox": uninterrupted_print_box,
            }

        elif name == "m10_cut_distance":
            self.ensure_sett("uninterrupted_print.cut_distance")

            m10_cut_distance = QLabel(self.locale.M10CutDistance)
            m10_cut_distance_value = QDoubleSpinBox()
            m10_cut_distance_value.setMinimum(0.0)
            m10_cut_distance_value.setMaximum(9999.0)
            m10_cut_distance_value.validator = FloatValidator()
            try:
                m10_cut_distance_value.setValue(sett().uninterrupted_print.cut_distance)
            except:
                m10_cut_distance_value.setValue(0.0)
            panel.addWidget(m10_cut_distance, panel_next_row(), 1)
            panel.addWidget(
                m10_cut_distance_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                sett().uninterrupted_print.cut_distance = m10_cut_distance_value.value()

            m10_cut_distance_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": m10_cut_distance,
                "spinbox": m10_cut_distance_value,
            }

        elif name == "line_width":
            self.ensure_sett("slicing.line_width")

            line_width = QLabel(self.locale.LineWidth)
            line_width_value = QDoubleSpinBox()
            line_width_value.setMinimum(0.0)
            line_width_value.setMaximum(9999.0)
            line_width_value.validator = FloatValidator()
            panel.addWidget(line_width, panel_next_row(), 1)
            panel.addWidget(line_width_value, panel_cur_row(), 2, 1, self.col2_cells)
            try:
                line_width_value.setValue(self.sett().slicing.line_width)
            except:
                line_width_value.setValue(0.0)
            line_width_value.valueChanged.connect(self.__update_wall_thickness)

            def on_change():
                self.sett().slicing.line_width = line_width_value.value()

            line_width_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": line_width,
                "spinbox": line_width_value,
            }

        elif name == "layer_height":
            self.ensure_sett("slicing.layer_height")

            layer_height = QLabel(self.locale.LayerHeight)
            layer_height_value = QDoubleSpinBox()
            layer_height_value.setValue(self.sett().slicing.layer_height)
            layer_height_value.setMinimum(0.0)
            layer_height_value.setMaximum(9999.0)
            layer_height_value.validator = FloatValidator()
            layer_height_value.valueChanged.connect(self.__change_layer_height)
            panel.addWidget(layer_height, panel_next_row(), 1)
            panel.addWidget(layer_height_value, panel_cur_row(), 2, 1, self.col2_cells)

            try:
                layer_height_value.setValue(self.sett().slicing.layer_height)
            except:
                layer_height_value.setValue(0.0)

            def on_change():
                self.sett().slicing.layer_height = layer_height_value.value()

            layer_height_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": layer_height,
                "spinbox": layer_height_value,
            }

        elif name == "number_wall_lines":
            self.ensure_sett("slicing.wall_thickness")

            number_wall_lines_label = QLabel(self.locale.NumberWallLines)
            if self.sett().slicing.line_width > 0:
                number_wall_lines = int(
                    self.sett().slicing.wall_thickness / self.sett().slicing.line_width
                )
            else:
                number_wall_lines = 0

            number_wall_lines_value = QSpinBox()
            number_wall_lines_value.setMinimum(0)
            number_wall_lines_value.setMaximum(9999)
            number_wall_lines_value.setValue(number_wall_lines)
            number_wall_lines_value.valueChanged.connect(self.__update_wall_thickness)

            panel.addWidget(number_wall_lines_label, panel_next_row(), 1)
            panel.addWidget(number_wall_lines_value, panel_cur_row(), 2)

            wall_thickness_label = QLabel(self.locale.WallThickness)
            wall_thickness_value = QDoubleSpinBox()
            wall_thickness_value.setValue(float(self.sett().slicing.wall_thickness))
            wall_thickness_value.setButtonSymbols(QSpinBox.NoButtons)
            wall_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)
            panel.addWidget(wall_thickness_label, panel_cur_row(), 3)
            panel.addWidget(wall_thickness_value, panel_cur_row(), 4)
            panel.addWidget(millimeter_label, panel_cur_row(), 5)

            def on_change():
                self.sett().slicing.wall_thickness = wall_thickness_value.value()

            number_wall_lines_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_wall_lines_label,
                "spinbox": number_wall_lines_value,
                "wall_thickness_label": wall_thickness_label,
                "wall_thickness_value": wall_thickness_value,
            }

        elif name == "number_of_bottom_layers":
            self.ensure_sett("slicing.bottoms_depth")

            number_of_bottom_layers_label = QLabel(self.locale.NumberOfBottomLayers)
            number_of_bottom_layers_value = QSpinBox()
            number_of_bottom_layers_value.setMinimum(0)
            number_of_bottom_layers_value.setMaximum(9999)
            number_of_bottom_layers_value.setValue(
                int(self.sett().slicing.bottoms_depth)
            )
            number_of_bottom_layers_value.valueChanged.connect(
                self.__update_bottom_thickness
            )

            panel.addWidget(number_of_bottom_layers_label, panel_next_row(), 1)
            panel.addWidget(number_of_bottom_layers_value, panel_cur_row(), 2)

            bottom_thickness_label = QLabel(self.locale.BottomThickness)
            bottom_thickness_value = QDoubleSpinBox()
            bottom_thickness_value.setValue(
                round(
                    self.sett().slicing.bottoms_depth
                    * self.sett().slicing.layer_height,
                    2,
                )
            )
            bottom_thickness_value.setButtonSymbols(QSpinBox.NoButtons)
            bottom_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            panel.addWidget(bottom_thickness_label, panel_cur_row(), 3)
            panel.addWidget(bottom_thickness_value, panel_cur_row(), 4)
            panel.addWidget(millimeter_label, panel_cur_row(), 5)

            def on_change():
                self.sett().slicing.bottoms_depth = (
                    number_of_bottom_layers_value.value()
                )

            number_of_bottom_layers_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_of_bottom_layers_label,
                "spinbox": number_of_bottom_layers_value,
                "bottom_thickness_label": bottom_thickness_label,
                "bottom_thickness_value": bottom_thickness_value,
            }

        elif name == "number_of_lids_layers":
            self.ensure_sett("slicing.lids_depth")

            number_of_lids_layers_label = QLabel(self.locale.NumberOfLidLayers)
            number_of_lids_layers_value = QSpinBox()
            number_of_lids_layers_value.setMinimum(0)
            number_of_lids_layers_value.setMaximum(9999)
            number_of_lids_layers_value.setValue(int(self.sett().slicing.lids_depth))
            number_of_lids_layers_value.valueChanged.connect(
                self.__update_lid_thickness
            )

            panel.addWidget(number_of_lids_layers_label, panel_next_row(), 1)
            panel.addWidget(number_of_lids_layers_value, panel_cur_row(), 2)

            lid_thickness_label = QLabel(self.locale.LidsThickness)
            lid_thickness_value = QDoubleSpinBox()
            lid_thickness_value.setValue(
                float(
                    round(
                        self.sett().slicing.lids_depth
                        * self.sett().slicing.layer_height,
                        2,
                    )
                )
            )
            lid_thickness_value.setButtonSymbols(QDoubleSpinBox.NoButtons)
            lid_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            panel.addWidget(lid_thickness_label, panel_cur_row(), 3)
            panel.addWidget(lid_thickness_value, panel_cur_row(), 4)
            panel.addWidget(millimeter_label, panel_cur_row(), 5)

            def on_change():
                self.sett().slicing.lids_depth = number_of_lids_layers_value.value()

            number_of_lids_layers_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_of_lids_layers_label,
                "spinbox": number_of_lids_layers_value,
                "lid_thickness_label": lid_thickness_label,
                "lid_thickness_value": lid_thickness_value,
            }

        elif name == "extruder_temp":
            self.ensure_sett("slicing.extruder_temperature")

            extruder_temp_label = QLabel(self.locale.ExtruderTemp)
            extruder_temp_value = QSpinBox()
            extruder_temp_value.setMinimum(0)
            extruder_temp_value.setMaximum(9999)
            extruder_temp_value.setValue(int(self.sett().slicing.extruder_temperature))
            panel.addWidget(extruder_temp_label, panel_next_row(), 1)
            panel.addWidget(extruder_temp_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.extruder_temperature = extruder_temp_value.value()

            extruder_temp_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": extruder_temp_label,
                "spinbox": extruder_temp_value,
            }

        elif name == "bed_temp":
            self.ensure_sett("slicing.bed_temperature")

            bed_temp_label = QLabel(self.locale.BedTemp)
            bed_temp_value = QSpinBox()
            bed_temp_value.setMinimum(0)
            bed_temp_value.setMaximum(9999)
            bed_temp_value.setValue(int(self.sett().slicing.bed_temperature))
            panel.addWidget(bed_temp_label, panel_next_row(), 1)
            panel.addWidget(bed_temp_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.bed_temperature = bed_temp_value.text()

            bed_temp_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": bed_temp_label,
                "spinbox": bed_temp_value,
            }

        elif name == "skirt_line_count":
            self.ensure_sett("slicing.skirt_line_count")

            skirt_line_count_label = QLabel(self.locale.SkirtLineCount)
            skirt_line_count_value = QSpinBox()
            skirt_line_count_value.setMinimum(0)
            skirt_line_count_value.setMaximum(9999)
            skirt_line_count_value.setValue(int(self.sett().slicing.skirt_line_count))
            panel.addWidget(skirt_line_count_label, panel_next_row(), 1)
            panel.addWidget(
                skirt_line_count_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.skirt_line_count = skirt_line_count_value.value()

            skirt_line_count_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": skirt_line_count_label,
                "spinbox": skirt_line_count_value,
            }

        elif name == "fan_speed":
            self.ensure_sett("slicing.fan_speed")

            fan_speed_label = QLabel(self.locale.FanSpeed)
            fan_speed_value = QSpinBox()
            fan_speed_value.setMinimum(0)
            fan_speed_value.setMaximum(9999)
            fan_speed_value.setValue(int(self.sett().slicing.fan_speed))
            panel.addWidget(fan_speed_label, panel_next_row(), 1)
            panel.addWidget(fan_speed_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.fan_speed = fan_speed_value.value()

            fan_speed_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": fan_speed_label,
                "spinbox": fan_speed_value,
                "setting": "slicing.fan_speed",
            }

        elif name == "fan_off_layer1":
            self.ensure_sett("slicing.fan_off_layer1")

            fan_off_layer1_label = QLabel(self.locale.FanOffLayer1)
            fan_off_layer1_box = QCheckBox()
            if self.sett().slicing.fan_off_layer1:
                fan_off_layer1_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(fan_off_layer1_label, panel_next_row(), 1)
            panel.addWidget(fan_off_layer1_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.fan_off_layer1 = fan_off_layer1_box.isChecked()

            fan_off_layer1_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": fan_off_layer1_label,
                "checkbox": fan_off_layer1_box,
            }

        elif name == "print_speed":
            self.ensure_sett("slicing.print_speed")

            print_speed_label = QLabel(self.locale.PrintSpeed)
            print_speed_value = QSpinBox()
            print_speed_value.setMinimum(0)
            print_speed_value.setMaximum(9999)
            print_speed_value.setValue(int(self.sett().slicing.print_speed))
            panel.addWidget(print_speed_label, panel_next_row(), 1)
            panel.addWidget(print_speed_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.print_speed = print_speed_value.value()

            print_speed_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_label,
                "spinbox": print_speed_value,
            }

        elif name == "print_speed_layer1":
            self.ensure_sett("slicing.print_speed_layer1")

            print_speed_layer1_label = QLabel(self.locale.PrintSpeedLayer1)
            print_speed_layer1_value = QSpinBox()
            print_speed_layer1_value.setMinimum(0)
            print_speed_layer1_value.setMaximum(9999)
            print_speed_layer1_value.setValue(
                int(self.sett().slicing.print_speed_layer1)
            )
            panel.addWidget(print_speed_layer1_label, panel_next_row(), 1)
            panel.addWidget(
                print_speed_layer1_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.print_speed_layer1 = (
                    print_speed_layer1_value.value()
                )

            print_speed_layer1_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_layer1_label,
                "spinbox": print_speed_layer1_value,
            }

        elif name == "print_speed_wall":
            self.ensure_sett("slicing.print_speed_wall")

            print_speed_wall_label = QLabel(self.locale.PrintSpeedWall)
            print_speed_wall_value = QSpinBox()
            print_speed_wall_value.setMinimum(0)
            print_speed_wall_value.setMaximum(9999)
            print_speed_wall_value.setValue(int(self.sett().slicing.print_speed_wall))
            panel.addWidget(print_speed_wall_label, panel_next_row(), 1)
            panel.addWidget(
                print_speed_wall_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.print_speed_wall = print_speed_wall_value.value()

            print_speed_wall_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_wall_label,
                "spinbox": print_speed_wall_value,
            }

        elif name == "filling_type":
            self.ensure_sett("slicing.filling_type")

            filling_type_label = QLabel(self.locale.FillingType)
            filling_type_values = QComboBox()
            filling_type_values.addItems(self.locale.FillingTypeValues)
            filling_type_values.setCurrentIndex(
                locales.getLocaleByLang("en").FillingTypeValues.index(
                    self.sett().slicing.filling_type
                )
            )
            panel.addWidget(filling_type_label, panel_next_row(), 1)
            panel.addWidget(filling_type_values, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.filling_type = locales.getLocaleByLang(
                    "en"
                ).FillingTypeValues[filling_type_values.currentIndex()]

            filling_type_values.currentIndexChanged.connect(on_change)

            self.__elements[name] = {
                "label": filling_type_label,
                "values": filling_type_values,
                "setting": "slicing.filling_type",
            }

        elif name == "fill_density":
            self.ensure_sett("slicing.fill_density")

            fill_density_label = QLabel(self.locale.FillDensity)
            fill_density_value = QSpinBox()
            fill_density_value.setMinimum(0)
            fill_density_value.setMaximum(100)
            fill_density_value.setValue(int(self.sett().slicing.fill_density))
            panel.addWidget(fill_density_label, panel_next_row(), 1)
            panel.addWidget(fill_density_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.fill_density = fill_density_value.value()

            fill_density_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": fill_density_label,
                "spinbox": fill_density_value,
                "setting": "slicing.fill_density",
            }

        elif name == "minimum_fill_area":
            self.ensure_sett("slicing.minimum_fill_area")

            minimum_fill_area_label = QLabel(self.locale.MinimumFillArea)

            minimum_fill_area_value = QDoubleSpinBox()
            minimum_fill_area_value.setMinimum(0.0)
            minimum_fill_area_value.setMaximum(9999.0)
            minimum_fill_area_value.validator = FloatValidator()

            panel.addWidget(minimum_fill_area_label, panel_next_row(), 1)
            panel.addWidget(
                minimum_fill_area_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.minimum_fill_area = minimum_fill_area_value.value()

            minimum_fill_area_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": minimum_fill_area_label,
                "spinbox": minimum_fill_area_value,
            }

        elif name == "overlap_infill":
            self.ensure_sett("slicing.overlapping_infill_percentage")

            overlap_infill_label = QLabel(self.locale.OverlappingInfillPercentage)
            overlap_infill_value = QSpinBox()
            overlap_infill_value.setMinimum(0)
            overlap_infill_value.setMaximum(100)
            overlap_infill_value.setValue(
                int(self.sett().slicing.overlapping_infill_percentage)
            )
            panel.addWidget(overlap_infill_label, panel_next_row(), 1)
            panel.addWidget(
                overlap_infill_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.overlapping_infill_percentage = (
                    overlap_infill_value.value()
                )

            overlap_infill_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": overlap_infill_label,
                "spinbox": overlap_infill_value,
            }

        elif name == "retraction_on":
            self.ensure_sett("slicing.retraction_on")

            rls_on_label = QLabel(self.locale.Retraction)
            rls_on_box = QCheckBox()
            if self.sett().slicing.retraction_on:
                rls_on_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(rls_on_label, panel_next_row(), 1)
            panel.addWidget(rls_on_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.retraction_on = rls_on_box.isChecked()

            rls_on_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": rls_on_label,
                "checkbox": rls_on_box,
            }

        elif name == "retraction_distance":
            self.ensure_sett("slicing.retraction_distance")

            retraction_distance_label = QLabel(self.locale.RetractionDistance)
            retraction_distance_value = QDoubleSpinBox()
            retraction_distance_value.setMinimum(0.0)
            retraction_distance_value.setMaximum(9999.0)
            retraction_distance_value.validator = FloatValidator()
            try:
                retraction_distance_value.setValue(
                    self.sett().slicing.retraction_distance
                )
            except:
                retraction_distance_value.setValue(0.0)
            panel.addWidget(retraction_distance_label, panel_next_row(), 1)
            panel.addWidget(
                retraction_distance_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retraction_distance = (
                    retraction_distance_value.value()
                )

            retraction_distance_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_distance_label,
                "spinbox": retraction_distance_value,
            }

        elif name == "retraction_speed":
            self.ensure_sett("slicing.retraction_speed")

            retraction_speed_label = QLabel(self.locale.RetractionSpeed)
            retraction_speed_value = QSpinBox()
            retraction_speed_value.setMinimum(0)
            retraction_speed_value.setMaximum(9999)
            retraction_speed_value.setValue(int(self.sett().slicing.retraction_speed))
            panel.addWidget(retraction_speed_label, panel_next_row(), 1)
            panel.addWidget(
                retraction_speed_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retraction_speed = retraction_speed_value.value()

            retraction_speed_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_speed_label,
                "spinbox": retraction_speed_value,
            }

        elif name == "retraction_compensation":
            self.ensure_sett("slicing.retract_compensation_amount")

            retraction_compensation_label = QLabel(
                self.locale.RetractCompensationAmount
            )
            retraction_compensation_value = QDoubleSpinBox()
            retraction_compensation_value.setMinimum(0.0)
            retraction_compensation_value.setMaximum(9999.0)
            retraction_compensation_value.validator = FloatValidator()
            panel.addWidget(retraction_compensation_label, panel_next_row(), 1)
            panel.addWidget(
                retraction_compensation_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retract_compensation_amount = (
                    retraction_compensation_value.value()
                )

            retraction_compensation_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_compensation_label,
                "spinbox": retraction_compensation_value,
            }

        elif name == "material_shrinkage":
            self.ensure_sett("slicing.material_shrinkage")

            material_shrinkage_label = QLabel(self.locale.MaterialShrinkage)
            material_shrinkage_value = QDoubleSpinBox()
            material_shrinkage_value.setMinimum(0.0)
            material_shrinkage_value.setMaximum(9999.0)
            material_shrinkage_value.setValue(self.sett().slicing.material_shrinkage)
            panel.addWidget(material_shrinkage_label, panel_next_row(), 1)
            panel.addWidget(
                material_shrinkage_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.material_shrinkage = (
                    material_shrinkage_value.value()
                )

            material_shrinkage_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": material_shrinkage_label,
                "spinbox": material_shrinkage_value,
            }

        elif name == "random_layer_start":
            self.ensure_sett("slicing.random_layer_start")

            rls_on_label = QLabel(self.locale.RandomLayerStart)
            rls_on_box = QCheckBox()
            if self.sett().slicing.random_layer_start:
                rls_on_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(rls_on_label, panel_next_row(), 1)
            panel.addWidget(rls_on_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.random_layer_start = rls_on_box.isChecked()

            rls_on_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": rls_on_label,
                "checkbox": rls_on_box,
            }
        elif name == "is_wall_outside_in":
            self.ensure_sett("slicing.is_wall_outside_in")

            wall_outside_in_label = QLabel(self.locale.IsWallsOutsideIn)
            wall_outside_in_box = QCheckBox()
            if self.sett().slicing.is_wall_outside_in:
                wall_outside_in_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(wall_outside_in_label, panel_next_row(), 1)
            panel.addWidget(wall_outside_in_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.is_wall_outside_in = wall_outside_in_box.isChecked()

            wall_outside_in_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": wall_outside_in_label,
                "checkbox": wall_outside_in_box,
            }
        elif name == "flow_rate":
            self.ensure_sett("slicing.flow_rate")

            flow_rate_label = QLabel(self.locale.FlowRate)
            flow_rate_value = QDoubleSpinBox()
            flow_rate_value.setMinimum(0.0)
            flow_rate_value.setMaximum(9999.0)
            flow_rate_value.setValue(self.sett().slicing.flow_rate)
            panel.addWidget(flow_rate_label, panel_next_row(), 1)
            panel.addWidget(flow_rate_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                value = flow_rate_value.value()
                # value should be between 45 and 150 percent
                if 45 <= value <= 150:
                    flow_rate_value.setStyleSheet("")  # Reset to default style
                    flow_rate_value.setToolTip("")
                else:
                    flow_rate_value.setStyleSheet(
                        "background-color: lightcoral; color: black;"
                    )
                    flow_rate_value.setToolTip(
                        self.locale.ValueInBetween.format(45, 150)
                    )
                self.sett().slicing.flow_rate = value

            flow_rate_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": flow_rate_label,
                "spinbox": flow_rate_value,
            }

        elif name == "pressure_advance_on":
            self.ensure_sett("slicing.pressure_advance_on")

            pressure_advance_on_label = QLabel(self.locale.PressureAdvance)
            pressure_advance_on_box = QCheckBox()
            if self.sett().slicing.pressure_advance_on:
                pressure_advance_on_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(pressure_advance_on_label, panel_next_row(), 1)
            panel.addWidget(
                pressure_advance_on_box, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.pressure_advance_on = (
                    pressure_advance_on_box.isChecked()
                )

            pressure_advance_on_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": pressure_advance_on_label,
                "checkbox": pressure_advance_on_box,
            }

        elif name == "pressure_advance":
            self.ensure_sett("slicing.pressure_advance")

            pressure_advance_label = QLabel(self.locale.PressureAdvanceValue)
            pressure_advance_value = QDoubleSpinBox()
            pressure_advance_value.setMinimum(0.01)
            pressure_advance_value.setMaximum(1.0)
            pressure_advance_value.setValue(self.sett().slicing.pressure_advance)
            # between 0.01 and 0.9, default is 0.45
            panel.addWidget(pressure_advance_label, panel_next_row(), 1)
            panel.addWidget(
                pressure_advance_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                value = pressure_advance_value.value()
                # value should be between 0.01 and 0.9
                if 0.01 <= value <= 0.9:
                    pressure_advance_value.setStyleSheet("")
                    pressure_advance_value.setToolTip("")
                else:
                    pressure_advance_value.setStyleSheet(
                        "background-color: lightcoral; color: black;"
                    )
                    pressure_advance_value.setToolTip(
                        self.locale.ValueInBetween.format(0.01, 0.9)
                    )
                self.sett().slicing.pressure_advance = value

            pressure_advance_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": pressure_advance_label,
                "spinbox": pressure_advance_value,
            }

        elif name == "supports_on":
            self.ensure_sett("supports.enabled")
            # supports_label = QLabel(self.locale.SupportsSettings)

            # supports on
            supports_on_label = QLabel(self.locale.SupportsOn)
            supports_on_box = QCheckBox()
            if self.sett().supports.enabled:
                supports_on_box.setCheckState(QtCore.Qt.Checked)

            # self.panel.addWidget(supports_label, self.next_row, 1)

            panel.addWidget(supports_on_label, panel_next_row(), 1)
            panel.addWidget(supports_on_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().supports.enabled = supports_on_box.isChecked()

            supports_on_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                # "group_label": supports_label,
                "label": supports_on_label,
                "checkbox": supports_on_box,
            }

        elif name == "support_density":
            self.ensure_sett("supports.fill_density")

            support_density_label = QLabel(self.locale.SupportDensity)
            support_density_value = QSpinBox()
            support_density_value.setMinimum(0)
            support_density_value.setMaximum(100)
            support_density_value.setValue(int(self.sett().supports.fill_density))
            panel.addWidget(support_density_label, panel_next_row(), 1)
            panel.addWidget(
                support_density_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.fill_density = support_density_value.value()

            support_density_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_density_label,
                "spinbox": support_density_value,
            }

        elif name == "support_fill_type":
            self.ensure_sett("supports.fill_type")

            support_fill_type_label = QLabel(self.locale.FillingType)
            support_fill_type_values = QComboBox()
            support_fill_type_values.addItems(self.locale.FillingTypeValues)
            support_fill_type_values.setCurrentIndex(
                locales.getLocaleByLang("en").FillingTypeValues.index(
                    self.sett().supports.fill_type
                )
            )
            panel.addWidget(support_fill_type_label, panel_next_row(), 1)
            panel.addWidget(
                support_fill_type_values, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.fill_type = locales.getLocaleByLang(
                    "en"
                ).FillingTypeValues[support_fill_type_values.currentIndex()]

            support_fill_type_values.currentIndexChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_fill_type_label,
                "values": support_fill_type_values,
            }

        elif name == "support_xy_offset":
            self.ensure_sett("supports.xy_offset")

            support_xy_offset_label = QLabel(self.locale.SupportXYOffset)
            support_xy_offset_value = QDoubleSpinBox()
            support_xy_offset_value.setMinimum(0.0)
            support_xy_offset_value.setMaximum(9999.0)
            support_xy_offset_value.validator = FloatValidator()
            try:
                support_xy_offset_value.setValue(self.sett().supports.xy_offset)
            except:
                support_xy_offset_value.setValue(0.0)
            panel.addWidget(support_xy_offset_label, panel_next_row(), 1)
            panel.addWidget(
                support_xy_offset_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.xy_offset = support_xy_offset_value.value()

            support_xy_offset_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_xy_offset_label,
                "spinbox": support_xy_offset_value,
            }

        elif name == "support_z_offset":
            self.ensure_sett("supports.z_offset_layers")

            support_z_offset_label = QLabel(self.locale.SupportZOffsetLayers)
            support_z_offset_value = QSpinBox()
            support_z_offset_value.setMinimum(0)
            support_z_offset_value.setMaximum(9999)
            support_z_offset_value.setValue(int(self.sett().supports.z_offset_layers))
            panel.addWidget(support_z_offset_label, panel_next_row(), 1)
            panel.addWidget(
                support_z_offset_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.z_offset_layers = support_z_offset_value.value()

            support_z_offset_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_z_offset_label,
                "spinbox": support_z_offset_value,
            }

        elif name == "support_priority_zoffset":
            self.ensure_sett("supports.priority_z_offset")

            support_priority_zoffset_label = QLabel(self.locale.SupportPriorityZOffset)
            support_priorityz_offset_box = QCheckBox()
            if self.sett().supports.priority_z_offset:
                support_priorityz_offset_box.setCheckState(QtCore.Qt.Checked)

            panel.addWidget(support_priority_zoffset_label, panel_next_row(), 1)
            panel.addWidget(
                support_priorityz_offset_box, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.priority_z_offset = (
                    support_priorityz_offset_box.isChecked()
                )

            support_priorityz_offset_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_priority_zoffset_label,
                "checkbox": support_priorityz_offset_box,
            }

        elif name == "support_number_of_bottom_layers":
            self.ensure_sett("supports.bottoms_depth")

            support_number_of_bottom_layers_label = QLabel(
                self.locale.NumberOfBottomLayers
            )
            support_number_of_bottom_layers_value = QSpinBox()
            support_number_of_bottom_layers_value.setMinimum(0)
            support_number_of_bottom_layers_value.setMaximum(9999)
            support_number_of_bottom_layers_value.setValue(
                int(self.sett().supports.bottoms_depth)
            )
            support_number_of_bottom_layers_value.valueChanged.connect(
                self.__update_supports_bottom_thickness
            )
            panel.addWidget(support_number_of_bottom_layers_label, panel_next_row(), 1)
            panel.addWidget(support_number_of_bottom_layers_value, panel_cur_row(), 2)

            bottom_thickness_label = QLabel(self.locale.BottomThickness)
            bottom_thickness_value = QDoubleSpinBox()
            bottom_thickness_value.setValue(
                round(
                    self.sett().supports.bottoms_depth
                    * self.sett().slicing.layer_height,
                    2,
                )
            )
            bottom_thickness_value.setButtonSymbols(QSpinBox.NoButtons)
            bottom_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            panel.addWidget(bottom_thickness_label, panel_cur_row(), 3)
            panel.addWidget(bottom_thickness_value, panel_cur_row(), 4)
            panel.addWidget(millimeter_label, panel_cur_row(), 5)

            def on_change():
                self.sett().supports.bottoms_depth = (
                    support_number_of_bottom_layers_value.value()
                )

            support_number_of_bottom_layers_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_number_of_bottom_layers_label,
                "spinbox": support_number_of_bottom_layers_value,
                "bottom_thickness_label": bottom_thickness_label,
                "bottom_thickness_value": bottom_thickness_value,
            }

        elif name == "support_number_of_lid_layers":
            self.ensure_sett("supports.lids_depth")

            support_number_of_lid_layers_label = QLabel(self.locale.NumberOfLidLayers)
            support_number_of_lid_layers_value = QSpinBox()
            support_number_of_lid_layers_value.setMinimum(0)
            support_number_of_lid_layers_value.setMaximum(9999)
            support_number_of_lid_layers_value.setValue(
                int(self.sett().supports.lids_depth)
            )
            support_number_of_lid_layers_value.valueChanged.connect(
                self.__update_supports_lid_thickness
            )
            panel.addWidget(support_number_of_lid_layers_label, panel_next_row(), 1)
            panel.addWidget(support_number_of_lid_layers_value, panel_cur_row(), 2)

            lid_thickness_label = QLabel(self.locale.LidsThickness)
            lid_thickness_value = QDoubleSpinBox()
            lid_thickness_value.setValue(
                round(
                    self.sett().supports.lids_depth * self.sett().slicing.layer_height,
                    2,
                )
            )
            lid_thickness_value.setButtonSymbols(QSpinBox.NoButtons)
            lid_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            panel.addWidget(lid_thickness_label, panel_cur_row(), 3)
            panel.addWidget(lid_thickness_value, panel_cur_row(), 4)
            panel.addWidget(millimeter_label, panel_cur_row(), 5)

            def on_change():
                self.sett().supports.lids_depth = (
                    support_number_of_lid_layers_value.value()
                )

            support_number_of_lid_layers_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_number_of_lid_layers_label,
                "spinbox": support_number_of_lid_layers_value,
                "lid_thickness_label": lid_thickness_label,
                "lid_thickness_value": lid_thickness_value,
            }
        elif name == "critical_angle":
            self.ensure_sett("slicing.angle")

            angle_label = QLabel(self.locale.CriticalWallOverhangAngle)
            angle_value = QDoubleSpinBox()
            angle_value.setMinimum(0.0)
            angle_value.setMaximum(90.0)
            angle_value.validator = FloatValidator()
            try:
                angle_value.setValue(self.sett().slicing.angle)
            except:
                angle_value.setValue(0.0)

            panel.addWidget(angle_label, panel_next_row(), 1)
            panel.addWidget(angle_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.angle = angle_value.value()

            angle_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": angle_label,
                "spinbox": angle_value,
            }
        elif name == "support_create_walls":
            self.ensure_sett("supports.create_walls")

            create_walls_label = QLabel(self.locale.ShouldCreateWalls)
            create_walls_box = QCheckBox()
            if self.sett().supports.create_walls:
                create_walls_box.setCheckState(QtCore.Qt.Checked)
            panel.addWidget(create_walls_label, panel_next_row(), 1)
            panel.addWidget(create_walls_box, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().supports.create_walls = create_walls_box.isChecked()

            create_walls_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": create_walls_label,
                "checkbox": create_walls_box,
            }
        elif name == "auto_fan_enabled":
            self.ensure_sett("slicing.auto_fan.enabled")

            auto_fan_enabled_label = QLabel(self.locale.AutoFanEnabled)
            auto_fan_enabled_box = QCheckBox()
            if self.sett().slicing.auto_fan.enabled:
                auto_fan_enabled_box.setCheckState(QtCore.Qt.Checked)

            panel.addWidget(auto_fan_enabled_label, panel_next_row(), 1)
            panel.addWidget(
                auto_fan_enabled_box, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.auto_fan.enabled = auto_fan_enabled_box.isChecked()

            auto_fan_enabled_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": auto_fan_enabled_label,
                "checkbox": auto_fan_enabled_box,
            }
        elif name == "auto_fan_area":
            self.ensure_sett("slicing.auto_fan.area")

            auto_fan_area_label = QLabel(self.locale.AutoFanArea)

            auto_fan_area_value = QDoubleSpinBox()
            auto_fan_area_value.setMinimum(0.0)
            auto_fan_area_value.setMaximum(9999.0)
            auto_fan_area_value.validator = FloatValidator()
            try:
                auto_fan_area_value.setValue(self.sett().slicing.auto_fan.area)
            except:
                auto_fan_area_value.setValue(0.0)

            # auto_fan_area_value = LineEdit(str(self.sett().slicing.auto_fan.area))
            # auto_fan_area_value.setValidator(self.intValidator)
            panel.addWidget(auto_fan_area_label, panel_next_row(), 1)
            panel.addWidget(auto_fan_area_value, panel_cur_row(), 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.auto_fan.area = auto_fan_area_value.value()

            auto_fan_area_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": auto_fan_area_label,
                "spinbox": auto_fan_area_value,
            }
        elif name == "auto_fan_speed":
            self.ensure_sett("slicing.auto_fan.fan_speed")

            auto_fan_speed_label = QLabel(self.locale.AutoFanSpeed)
            auto_fan_speed_value = QSpinBox()
            auto_fan_speed_value.setMinimum(0)
            auto_fan_speed_value.setMaximum(9999)
            auto_fan_speed_value.setValue(int(self.sett().slicing.auto_fan.fan_speed))
            panel.addWidget(auto_fan_speed_label, panel_next_row(), 1)
            panel.addWidget(
                auto_fan_speed_value, panel_cur_row(), 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.auto_fan.fan_speed = auto_fan_speed_value.value()

            auto_fan_speed_value.valueChanged.connect(on_change)

            self.__elements[name] = {
                "label": auto_fan_speed_label,
                "spinbox": auto_fan_speed_value,
            }

        # add row index for element
        self.__elements[name]["row_idx"] = panel_cur_row()

        return self

    def __update_dependent_fields(self, spinbox1, spinbox2, spinbox_output):
        # take value from spinbox1 and spinbox2, multiply them and set the result to spinbox_output
        value1 = spinbox1.value()
        value2 = spinbox2.value()

        spinbox_output.setValue(float(value1 * value2))

    def __update_wall_thickness(self):
        """Callback to update wall thickness when number of wall lines or line width changes."""
        try:
            self.__update_dependent_fields(
                self.spinbox("number_wall_lines"),
                self.spinbox("line_width"),
                self.get_element("number_wall_lines", "wall_thickness_value"),
            )
        except KeyError:
            pass

    def __update_bottom_thickness(self):
        """Callback to update bottom thickness when number of bottom layers or layer height changes."""
        try:
            self.__update_dependent_fields(
                self.spinbox("number_of_bottom_layers"),
                self.spinbox("layer_height"),
                self.get_element("number_of_bottom_layers", "bottom_thickness_value"),
            )
        except KeyError:
            pass

    def __update_lid_thickness(self):
        """Callback to update lid thickness when number of lid layers or layer height changes."""
        try:
            self.__update_dependent_fields(
                self.spinbox("number_of_lids_layers"),
                self.spinbox("layer_height"),
                self.get_element("number_of_lids_layers", "lid_thickness_value"),
            )
        except KeyError:
            pass

    def __update_supports_bottom_thickness(self):
        """Callback to update bottom thickness when number of bottom layers or layer height changes."""
        try:
            self.__update_dependent_fields(
                self.spinbox("support_number_of_bottom_layers"),
                self.spinbox("layer_height"),
                self.get_element(
                    "support_number_of_bottom_layers", "bottom_thickness_value"
                ),
            )
        except KeyError:
            pass

    def __update_supports_lid_thickness(self):
        """Callback to update lid thickness when number of lid layers or layer height changes."""
        try:
            self.__update_dependent_fields(
                self.spinbox("support_number_of_lid_layers"),
                self.spinbox("layer_height"),
                self.get_element("support_number_of_lid_layers", "lid_thickness_value"),
            )
        except KeyError:
            pass

    def __change_layer_height(self):
        """Callback to update wall thickness, bottom thickness and lid thickness when layer height changes."""
        try:
            self.__update_bottom_thickness()
            self.__update_lid_thickness()
            self.__update_supports_bottom_thickness()
            self.__update_supports_lid_thickness()
        except KeyError:
            pass
