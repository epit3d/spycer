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
)

from src import locales
from src.settings import sett, APP_PATH, Settings
from src.qt_utils import ClickableLineEdit, LineEdit

import os.path as path
import logging


class SettingsWidget(QWidget):
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
        "overlap_infill",
        "retraction_on",
        "retraction_distance",
        "retraction_speed",
        "retraction_compensation",
        "material_shrinkage",
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

    # extra parameters are only used for a small widget with parameters for each figure specifically
    extra_sett_parameters = [
        "filling_type",
        "fill_density",
    ]

    def __init__(self, parent=None, settings_provider: callable = None):
        super(SettingsWidget, self).__init__(parent)

        assert settings_provider is not None, "Settings provider is required"

        self.sett = settings_provider

        self.panel = QGridLayout()
        self.panel.setSpacing(5)
        self.panel.setColumnStretch(1, 1)
        self.panel.setColumnStretch(3, 1)
        self.panel.setColumnStretch(4, 1)

        self.setLayout(self.panel)

        self.__elements = {}

        self.locale: locales.Locale = locales.getLocale()

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
            "overlap_infill": self.locale.OverlappingInfillPercentage,
            "retraction_on": self.locale.Retraction,
            "retraction_distance": self.locale.RetractionDistance,
            "retraction_speed": self.locale.RetractionSpeed,
            "retraction_compensation": self.locale.RetractCompensationAmount,
            "material_shrinkage": self.locale.MaterialShrinkage,
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

            # check whether this row already has delete button
            if self.panel.itemAtPosition(row_idx, 6) is not None:
                continue

            delete_btn = QPushButton()
            self.btns += [delete_btn]
            # set icon
            delete_btn.setIcon(self.style().standardIcon(QStyle.SP_DialogCloseButton))

            def get_row_widgets(row_idx):
                widgets = []
                for i in range(7):  # TODO: move to constant
                    item = self.panel.itemAtPosition(row_idx, i)
                    if item is None:
                        continue
                    if len(widgets) != 0 and item.widget() == widgets[-1]:
                        continue

                    widgets.append((item.widget(), i))
                return widgets

            def remove_row(row_idx):
                dlt_row = get_row_widgets(row_idx)
                for _, col_idx in dlt_row:
                    self.panel.itemAtPosition(row_idx, col_idx).widget().deleteLater()

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
            self.panel.addWidget(delete_btn, row_idx, 6)

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

        global_top = sett()
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
        # TODO: this list should be increased with the growth of extra parameters

        return self

    def with_sett(self, name: str):
        # check whether the given name is already added
        if name in self.__elements:
            return self

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
            self.panel.addWidget(label, self.next_row, 1)
            self.panel.addWidget(printer_add_btn, self.cur_row, 2)
            self.panel.addWidget(printer_path_edit, self.cur_row, 3, 1, 3)

            self.__elements[name] = {
                "label": label,
                "edit": printer_path_edit,
                "add_btn": printer_add_btn,
            }
        elif name == "uninterrupted_print":
            self.ensure_sett("uninterrupted_print.enabled")

            uninterrupted_print = QLabel(self.locale.UninterruptedPrint)
            uninterrupted_print_box = QCheckBox()
            if sett().uninterrupted_print.enabled:
                uninterrupted_print_box.setCheckState(QtCore.Qt.Checked)
            self.panel.addWidget(
                QLabel(self.locale.UninterruptedPrint), self.next_row, 1
            )
            self.panel.addWidget(
                uninterrupted_print_box, self.cur_row, 2, 1, self.col2_cells
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
            m10_cut_distance_value = QLineEdit()
            m10_cut_distance_value.setText(str(sett().uninterrupted_print.cut_distance))
            m10_cut_distance_value.setValidator(self.doubleValidator)
            self.panel.addWidget(m10_cut_distance, self.next_row, 1)
            self.panel.addWidget(
                m10_cut_distance_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                sett().uninterrupted_print.cut_distance = self.__smart_float(
                    m10_cut_distance_value.text()
                )

            m10_cut_distance_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": m10_cut_distance,
                "edit": m10_cut_distance_value,
            }

        elif name == "line_width":
            self.ensure_sett("slicing.line_width")

            line_width = QLabel(self.locale.LineWidth)
            line_width_value = QLineEdit()
            line_width_value.setText(str(self.sett().slicing.line_width))
            line_width_value.setValidator(self.doubleValidator)
            line_width_value.textChanged.connect(self.__update_wall_thickness)
            self.panel.addWidget(line_width, self.next_row, 1)
            self.panel.addWidget(line_width_value, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.line_width = self.__smart_float(
                    line_width_value.text()
                )

            line_width_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": line_width,
                "edit": line_width_value,
            }

        elif name == "layer_height":
            self.ensure_sett("slicing.layer_height")

            layer_height = QLabel(self.locale.LayerHeight)
            layer_height_value = QLineEdit()
            layer_height_value.setText(str(self.sett().slicing.layer_height))
            layer_height_value.setValidator(self.doubleValidator)
            layer_height_value.textChanged.connect(self.__change_layer_height)
            self.panel.addWidget(layer_height, self.next_row, 1)
            self.panel.addWidget(
                layer_height_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.layer_height = self.__smart_float(
                    layer_height_value.text()
                )

            layer_height_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": layer_height,
                "edit": layer_height_value,
            }

        elif name == "number_wall_lines":
            self.ensure_sett("slicing.wall_thickness")

            number_wall_lines_label = QLabel(self.locale.NumberWallLines)
            if self.sett().slicing.line_width > 0:
                number_wall_lines_value = int(
                    self.sett().slicing.wall_thickness / self.sett().slicing.line_width
                )
            else:
                number_wall_lines_value = 0

            number_wall_lines_value = LineEdit(str(number_wall_lines_value))
            number_wall_lines_value.setValidator(self.intValidator)

            number_wall_lines_value.textChanged.connect(self.__update_wall_thickness)

            self.panel.addWidget(number_wall_lines_label, self.next_row, 1)
            self.panel.addWidget(number_wall_lines_value, self.cur_row, 2)

            wall_thickness_label = QLabel(self.locale.WallThickness)
            wall_thickness_value = LineEdit(str(self.sett().slicing.wall_thickness))
            wall_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)
            self.panel.addWidget(wall_thickness_label, self.cur_row, 3)
            self.panel.addWidget(wall_thickness_value, self.cur_row, 4)
            self.panel.addWidget(millimeter_label, self.cur_row, 5)

            def on_change():
                self.sett().slicing.wall_thickness = self.__smart_float(
                    wall_thickness_value.text()
                )

            number_wall_lines_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_wall_lines_label,
                "edit": number_wall_lines_value,
                "wall_thickness_label": wall_thickness_label,
                "wall_thickness_value": wall_thickness_value,
            }

        elif name == "number_of_bottom_layers":
            self.ensure_sett("slicing.bottoms_depth")

            number_of_bottom_layers_label = QLabel(self.locale.NumberOfBottomLayers)
            number_of_bottom_layers_value = LineEdit(
                str(self.sett().slicing.bottoms_depth)
            )
            number_of_bottom_layers_value.setValidator(self.intValidator)
            number_of_bottom_layers_value.textChanged.connect(
                self.__update_bottom_thickness
            )

            self.panel.addWidget(number_of_bottom_layers_label, self.next_row, 1)
            self.panel.addWidget(number_of_bottom_layers_value, self.cur_row, 2)

            bottom_thickness_label = QLabel(self.locale.BottomThickness)
            bottom_thickness_value = LineEdit(
                str(
                    round(
                        self.sett().slicing.bottoms_depth
                        * self.sett().slicing.layer_height,
                        2,
                    ),
                )
            )
            bottom_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            self.panel.addWidget(bottom_thickness_label, self.cur_row, 3)
            self.panel.addWidget(bottom_thickness_value, self.cur_row, 4)
            self.panel.addWidget(millimeter_label, self.cur_row, 5)

            def on_change():
                self.sett().slicing.bottoms_depth = self.__smart_float(
                    number_of_bottom_layers_value.text()
                )

            number_of_bottom_layers_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_of_bottom_layers_label,
                "edit": number_of_bottom_layers_value,
                "bottom_thickness_label": bottom_thickness_label,
                "bottom_thickness_value": bottom_thickness_value,
            }

        elif name == "number_of_lids_layers":
            self.ensure_sett("slicing.lids_depth")

            number_of_lids_layers_label = QLabel(self.locale.NumberOfLidLayers)
            number_of_lids_layers_value = LineEdit(str(self.sett().slicing.lids_depth))
            number_of_lids_layers_value.setValidator(self.intValidator)
            number_of_lids_layers_value.textChanged.connect(self.__update_lid_thickness)

            self.panel.addWidget(number_of_lids_layers_label, self.next_row, 1)
            self.panel.addWidget(number_of_lids_layers_value, self.cur_row, 2)

            lid_thickness_label = QLabel(self.locale.LidsThickness)
            lid_thickness_value = LineEdit(
                str(
                    round(
                        self.sett().slicing.lids_depth
                        * self.sett().slicing.layer_height,
                        2,
                    ),
                )
            )
            lid_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            self.panel.addWidget(lid_thickness_label, self.cur_row, 3)
            self.panel.addWidget(lid_thickness_value, self.cur_row, 4)
            self.panel.addWidget(millimeter_label, self.cur_row, 5)

            def on_change():
                self.sett().slicing.lids_depth = self.__smart_float(
                    number_of_lids_layers_value.text()
                )

            number_of_lids_layers_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": number_of_lids_layers_label,
                "edit": number_of_lids_layers_value,
                "lid_thickness_label": lid_thickness_label,
                "lid_thickness_value": lid_thickness_value,
            }

        elif name == "extruder_temp":
            self.ensure_sett("slicing.extruder_temperature")

            extruder_temp_label = QLabel(self.locale.ExtruderTemp)
            extruder_temp_value = LineEdit(
                str(self.sett().slicing.extruder_temperature)
            )
            extruder_temp_value.setValidator(self.intValidator)
            self.panel.addWidget(extruder_temp_label, self.next_row, 1)
            self.panel.addWidget(
                extruder_temp_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.extruder_temperature = self.__smart_float(
                    extruder_temp_value.text()
                )

            extruder_temp_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": extruder_temp_label,
                "edit": extruder_temp_value,
            }

        elif name == "bed_temp":
            self.ensure_sett("slicing.bed_temperature")

            bed_temp_label = QLabel(self.locale.BedTemp)
            bed_temp_value = LineEdit(str(self.sett().slicing.bed_temperature))
            bed_temp_value.setValidator(self.intValidator)
            self.panel.addWidget(bed_temp_label, self.next_row, 1)
            self.panel.addWidget(bed_temp_value, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.bed_temperature = self.__smart_float(
                    bed_temp_value.text()
                )

            bed_temp_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": bed_temp_label,
                "edit": bed_temp_value,
            }

        elif name == "skirt_line_count":
            self.ensure_sett("slicing.skirt_line_count")

            skirt_line_count_label = QLabel(self.locale.SkirtLineCount)
            skirt_line_count_value = LineEdit(str(self.sett().slicing.skirt_line_count))
            skirt_line_count_value.setValidator(self.intValidator)
            self.panel.addWidget(skirt_line_count_label, self.next_row, 1)
            self.panel.addWidget(
                skirt_line_count_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.skirt_line_count = self.__smart_float(
                    skirt_line_count_value.text()
                )

            skirt_line_count_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": skirt_line_count_label,
                "edit": skirt_line_count_value,
            }

        elif name == "fan_speed":
            self.ensure_sett("slicing.fan_speed")

            fan_speed_label = QLabel(self.locale.FanSpeed)
            fan_speed_value = LineEdit(str(self.sett().slicing.fan_speed))
            fan_speed_value.setValidator(self.intValidator)
            self.panel.addWidget(fan_speed_label, self.next_row, 1)
            self.panel.addWidget(fan_speed_value, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.fan_speed = self.__smart_float(
                    fan_speed_value.text()
                )

            fan_speed_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": fan_speed_label,
                "edit": fan_speed_value,
            }

        elif name == "fan_off_layer1":
            self.ensure_sett("slicing.fan_off_layer1")

            fan_off_layer1_label = QLabel(self.locale.FanOffLayer1)
            fan_off_layer1_box = QCheckBox()
            if self.sett().slicing.fan_off_layer1:
                fan_off_layer1_box.setCheckState(QtCore.Qt.Checked)
            self.panel.addWidget(fan_off_layer1_label, self.next_row, 1)
            self.panel.addWidget(
                fan_off_layer1_box, self.cur_row, 2, 1, self.col2_cells
            )

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
            print_speed_value = LineEdit(str(self.sett().slicing.print_speed))
            print_speed_value.setValidator(self.intValidator)
            self.panel.addWidget(print_speed_label, self.next_row, 1)
            self.panel.addWidget(print_speed_value, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.print_speed = self.__smart_float(
                    print_speed_value.text()
                )

            print_speed_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_label,
                "edit": print_speed_value,
            }

        elif name == "print_speed_layer1":
            self.ensure_sett("slicing.print_speed_layer1")

            print_speed_layer1_label = QLabel(self.locale.PrintSpeedLayer1)
            print_speed_layer1_value = LineEdit(
                str(self.sett().slicing.print_speed_layer1)
            )
            print_speed_layer1_value.setValidator(self.intValidator)
            self.panel.addWidget(print_speed_layer1_label, self.next_row, 1)
            self.panel.addWidget(
                print_speed_layer1_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.print_speed_layer1 = self.__smart_float(
                    print_speed_layer1_value.text()
                )

            print_speed_layer1_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_layer1_label,
                "edit": print_speed_layer1_value,
            }

        elif name == "print_speed_wall":
            self.ensure_sett("slicing.print_speed_wall")

            print_speed_wall_label = QLabel(self.locale.PrintSpeedWall)
            print_speed_wall_value = LineEdit(str(self.sett().slicing.print_speed_wall))
            print_speed_wall_value.setValidator(self.intValidator)
            self.panel.addWidget(print_speed_wall_label, self.next_row, 1)
            self.panel.addWidget(
                print_speed_wall_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.print_speed_wall = self.__smart_float(
                    print_speed_wall_value.text()
                )

            print_speed_wall_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": print_speed_wall_label,
                "edit": print_speed_wall_value,
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
            self.panel.addWidget(filling_type_label, self.next_row, 1)
            self.panel.addWidget(
                filling_type_values, self.cur_row, 2, 1, self.col2_cells
            )

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
            fill_density_value = LineEdit(str(self.sett().slicing.fill_density))
            fill_density_value.setValidator(self.intValidator)
            self.panel.addWidget(fill_density_label, self.next_row, 1)
            self.panel.addWidget(
                fill_density_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.fill_density = self.__smart_float(
                    fill_density_value.text()
                )

            fill_density_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": fill_density_label,
                "edit": fill_density_value,
                "setting": "slicing.fill_density",
            }

        elif name == "overlap_infill":
            self.ensure_sett("slicing.overlapping_infill_percentage")

            overlap_infill_label = QLabel(self.locale.OverlappingInfillPercentage)
            overlap_infill_value = LineEdit(
                str(self.sett().slicing.overlapping_infill_percentage)
            )
            overlap_infill_value.setValidator(self.intValidator)
            self.panel.addWidget(overlap_infill_label, self.next_row, 1)
            self.panel.addWidget(
                overlap_infill_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.overlapping_infill_percentage = self.__smart_float(
                    overlap_infill_value.text()
                )

            overlap_infill_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": overlap_infill_label,
                "edit": overlap_infill_value,
            }

        elif name == "retraction_on":
            self.ensure_sett("slicing.retraction_on")

            retraction_on_label = QLabel(self.locale.Retraction)
            retraction_on_box = QCheckBox()
            if self.sett().slicing.retraction_on:
                retraction_on_box.setCheckState(QtCore.Qt.Checked)
            self.panel.addWidget(retraction_on_label, self.next_row, 1)
            self.panel.addWidget(retraction_on_box, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.retraction_on = retraction_on_box.isChecked()

            retraction_on_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_on_label,
                "checkbox": retraction_on_box,
            }

        elif name == "retraction_distance":
            self.ensure_sett("slicing.retraction_distance")

            retraction_distance_label = QLabel(self.locale.RetractionDistance)
            retraction_distance_value = LineEdit(
                str(self.sett().slicing.retraction_distance)
            )
            retraction_distance_value.setValidator(self.doubleValidator)
            self.panel.addWidget(retraction_distance_label, self.next_row, 1)
            self.panel.addWidget(
                retraction_distance_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retraction_distance = self.__smart_float(
                    retraction_distance_value.text()
                )

            retraction_distance_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_distance_label,
                "edit": retraction_distance_value,
            }

        elif name == "retraction_speed":
            self.ensure_sett("slicing.retraction_speed")

            retraction_speed_label = QLabel(self.locale.RetractionSpeed)
            retraction_speed_value = LineEdit(str(self.sett().slicing.retraction_speed))
            retraction_speed_value.setValidator(self.intValidator)
            self.panel.addWidget(retraction_speed_label, self.next_row, 1)
            self.panel.addWidget(
                retraction_speed_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retraction_speed = self.__smart_float(
                    retraction_speed_value.text()
                )

            retraction_speed_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_speed_label,
                "edit": retraction_speed_value,
            }

        elif name == "retraction_compensation":
            self.ensure_sett("slicing.retract_compensation_amount")

            retraction_compensation_label = QLabel(
                self.locale.RetractCompensationAmount
            )
            retraction_compensation_value = LineEdit(
                str(self.sett().slicing.retract_compensation_amount)
            )
            retraction_compensation_value.setValidator(self.doubleValidator)
            self.panel.addWidget(retraction_compensation_label, self.next_row, 1)
            self.panel.addWidget(
                retraction_compensation_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.retract_compensation_amount = self.__smart_float(
                    retraction_compensation_value.text()
                )

            retraction_compensation_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": retraction_compensation_label,
                "edit": retraction_compensation_value,
            }

        elif name == "material_shrinkage":
            self.ensure_sett("slicing.material_shrinkage")

            material_shrinkage_label = QLabel(self.locale.MaterialShrinkage)
            material_shrinkage_value = LineEdit(
                str(self.sett().slicing.material_shrinkage)
            )
            material_shrinkage_value.setValidator(self.doublePercentValidator)
            self.panel.addWidget(material_shrinkage_label, self.next_row, 1)
            self.panel.addWidget(
                material_shrinkage_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().slicing.material_shrinkage = self.__smart_float(
                    material_shrinkage_value.text()
                )

            material_shrinkage_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": material_shrinkage_label,
                "edit": material_shrinkage_value,
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

            self.panel.addWidget(supports_on_label, self.next_row, 1)
            self.panel.addWidget(supports_on_box, self.cur_row, 2, 1, self.col2_cells)

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
            support_density_value = LineEdit(str(self.sett().supports.fill_density))
            support_density_value.setValidator(self.intValidator)
            self.panel.addWidget(support_density_label, self.next_row, 1)
            self.panel.addWidget(
                support_density_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.fill_density = self.__smart_float(
                    support_density_value.text()
                )

            support_density_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_density_label,
                "edit": support_density_value,
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
            self.panel.addWidget(support_fill_type_label, self.next_row, 1)
            self.panel.addWidget(
                support_fill_type_values, self.cur_row, 2, 1, self.col2_cells
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
            support_xy_offset_value = LineEdit(str(self.sett().supports.xy_offset))
            support_xy_offset_value.setValidator(self.doubleValidator)
            self.panel.addWidget(support_xy_offset_label, self.next_row, 1)
            self.panel.addWidget(
                support_xy_offset_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.xy_offset = self.__smart_float(
                    support_xy_offset_value.text()
                )

            support_xy_offset_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_xy_offset_label,
                "edit": support_xy_offset_value,
            }

        elif name == "support_z_offset":
            self.ensure_sett("supports.z_offset_layers")

            support_z_offset_label = QLabel(self.locale.SupportZOffsetLayers)
            support_z_offset_value = LineEdit(str(self.sett().supports.z_offset_layers))
            support_z_offset_value.setValidator(self.intValidator)
            self.panel.addWidget(support_z_offset_label, self.next_row, 1)
            self.panel.addWidget(
                support_z_offset_value, self.cur_row, 2, 1, self.col2_cells
            )

            def on_change():
                self.sett().supports.z_offset_layers = self.__smart_float(
                    support_z_offset_value.text()
                )

            support_z_offset_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_z_offset_label,
                "edit": support_z_offset_value,
            }

        elif name == "support_priority_zoffset":
            self.ensure_sett("supports.priority_z_offset")

            support_priority_zoffset_label = QLabel(self.locale.SupportPriorityZOffset)
            support_priorityz_offset_box = QCheckBox()
            if self.sett().supports.priority_z_offset:
                support_priorityz_offset_box.setCheckState(QtCore.Qt.Checked)

            self.panel.addWidget(support_priority_zoffset_label, self.next_row, 1)
            self.panel.addWidget(
                support_priorityz_offset_box, self.cur_row, 2, 1, self.col2_cells
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
            support_number_of_bottom_layers_value = LineEdit(
                str(self.sett().supports.bottoms_depth)
            )
            support_number_of_bottom_layers_value.setValidator(self.intValidator)
            support_number_of_bottom_layers_value.textChanged.connect(
                self.__update_supports_bottom_thickness
            )
            self.panel.addWidget(
                support_number_of_bottom_layers_label, self.next_row, 1
            )
            self.panel.addWidget(support_number_of_bottom_layers_value, self.cur_row, 2)

            bottom_thickness_label = QLabel(self.locale.BottomThickness)
            bottom_thickness_value = LineEdit(
                str(
                    round(
                        self.sett().supports.bottoms_depth
                        * self.sett().slicing.layer_height,
                        2,
                    ),
                )
            )
            bottom_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            self.panel.addWidget(bottom_thickness_label, self.cur_row, 3)
            self.panel.addWidget(bottom_thickness_value, self.cur_row, 4)
            self.panel.addWidget(millimeter_label, self.cur_row, 5)

            def on_change():
                self.sett().supports.bottoms_depth = self.__smart_float(
                    support_number_of_bottom_layers_value.text()
                )

            support_number_of_bottom_layers_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_number_of_bottom_layers_label,
                "edit": support_number_of_bottom_layers_value,
                "bottom_thickness_label": bottom_thickness_label,
                "bottom_thickness_value": bottom_thickness_value,
            }

        elif name == "support_number_of_lid_layers":
            self.ensure_sett("supports.lids_depth")

            support_number_of_lid_layers_label = QLabel(self.locale.NumberOfLidLayers)
            support_number_of_lid_layers_value = LineEdit(
                str(self.sett().supports.lids_depth)
            )
            support_number_of_lid_layers_value.setValidator(self.intValidator)
            support_number_of_lid_layers_value.textChanged.connect(
                self.__update_supports_lid_thickness
            )
            self.panel.addWidget(support_number_of_lid_layers_label, self.next_row, 1)
            self.panel.addWidget(support_number_of_lid_layers_value, self.cur_row, 2)

            lid_thickness_label = QLabel(self.locale.LidsThickness)
            lid_thickness_value = LineEdit(
                str(
                    round(
                        self.sett().supports.lids_depth
                        * self.sett().slicing.layer_height,
                        2,
                    ),
                )
            )
            lid_thickness_value.setReadOnly(True)
            millimeter_label = QLabel(self.locale.Millimeter)

            self.panel.addWidget(lid_thickness_label, self.cur_row, 3)
            self.panel.addWidget(lid_thickness_value, self.cur_row, 4)
            self.panel.addWidget(millimeter_label, self.cur_row, 5)

            def on_change():
                self.sett().supports.lids_depth = self.__smart_float(
                    support_number_of_lid_layers_value.text()
                )

            support_number_of_lid_layers_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": support_number_of_lid_layers_label,
                "edit": support_number_of_lid_layers_value,
                "lid_thickness_label": lid_thickness_label,
                "lid_thickness_value": lid_thickness_value,
            }
        elif name == "critical_angle":
            self.ensure_sett("slicing.angle")

            angle_label = QLabel(self.locale.CriticalWallOverhangAngle)
            angle_value = LineEdit(str(self.sett().slicing.angle))
            angle_value.setValidator(self.doubleValidator)
            self.panel.addWidget(angle_label, self.next_row, 1)
            self.panel.addWidget(angle_value, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().slicing.angle = self.__smart_float(angle_value.text())

            angle_value.textChanged.connect(on_change)

            self.__elements[name] = {
                "label": angle_label,
                "edit": angle_value,
            }
        elif name == "support_create_walls":
            self.ensure_sett("supports.create_walls")

            create_walls_label = QLabel(self.locale.ShouldCreateWalls)
            create_walls_box = QCheckBox()
            if self.sett().supports.create_walls:
                create_walls_box.setCheckState(QtCore.Qt.Checked)
            self.panel.addWidget(create_walls_label, self.next_row, 1)
            self.panel.addWidget(create_walls_box, self.cur_row, 2, 1, self.col2_cells)

            def on_change():
                self.sett().supports.create_walls = create_walls_box.isChecked()

            create_walls_box.stateChanged.connect(on_change)

            self.__elements[name] = {
                "label": create_walls_label,
                "checkbox": create_walls_box,
            }

        # add row index for element
        self.__elements[name]["row_idx"] = self.cur_row

        return self

    def __update_wall_thickness(self):
        """Callback to update wall thickness when number of wall lines or line width changes."""
        try:
            self.update_dependent_fields(
                self.edit("number_wall_lines"),
                self.edit("line_width"),
                self.get_element("number_wall_lines", "wall_thickness_value"),
            )
        except KeyError:
            pass

    def __update_bottom_thickness(self):
        """Callback to update bottom thickness when number of bottom layers or layer height changes."""
        try:
            self.update_dependent_fields(
                self.edit("number_of_bottom_layers"),
                self.edit("layer_height"),
                self.get_element("number_of_bottom_layers", "bottom_thickness_value"),
            )
        except KeyError:
            pass

    def __update_lid_thickness(self):
        """Callback to update lid thickness when number of lid layers or layer height changes."""
        try:
            self.update_dependent_fields(
                self.edit("number_of_lids_layers"),
                self.edit("layer_height"),
                self.get_element("number_of_lids_layers", "lid_thickness_value"),
            )
        except KeyError:
            pass

    def __update_supports_bottom_thickness(self):
        """Callback to update bottom thickness when number of bottom layers or layer height changes."""
        try:
            self.update_dependent_fields(
                self.edit("support_number_of_bottom_layers"),
                self.edit("layer_height"),
                self.get_element(
                    "support_number_of_bottom_layers", "bottom_thickness_value"
                ),
            )
        except KeyError:
            pass

    def __update_supports_lid_thickness(self):
        """Callback to update lid thickness when number of lid layers or layer height changes."""
        try:
            self.update_dependent_fields(
                self.edit("support_number_of_lid_layers"),
                self.edit("layer_height"),
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
