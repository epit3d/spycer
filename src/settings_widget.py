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
from src.settings import sett, APP_PATH
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

    def with_sett(self, name: str):
        # we match the given name with each setting and add it to the layout
        match name:
            case "printer_path":
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
            case "uninterrupted_print":
                uninterrupted_print = QLabel(self.locale.UninterruptedPrint)
                self.uninterrupted_print_box = QCheckBox()
                if sett().uninterrupted_print.enabled:
                    self.uninterrupted_print_box.setCheckState(QtCore.Qt.Checked)
                self.panel.addWidget(
                    QLabel(self.locale.UninterruptedPrint), self.next_row, 1
                )
                self.panel.addWidget(
                    self.uninterrupted_print_box, self.cur_row, 2, 1, self.col2_cells
                )

                # on check on this box, we should restrict fill type to zigzag only
                def on_uninterrupted_print_change():
                    # TODO:
                    return
                    # isUninterrupted = self.uninterrupted_print_box.isChecked()

                    # self.filling_type_values.setEnabled(not isUninterrupted)
                    # self.retraction_on_box.setEnabled(not isUninterrupted)
                    # self.retraction_distance_value.setEnabled(not isUninterrupted)
                    # self.retraction_speed_value.setEnabled(not isUninterrupted)
                    # self.retract_compensation_amount_value.setEnabled(
                    #     not isUninterrupted
                    # )

                    # if isUninterrupted:
                    #     zigzag_idx = locales.getLocaleByLang(
                    #         "en"
                    #     ).FillingTypeValues.index("ZigZag")
                    #     self.filling_type_values.setCurrentIndex(zigzag_idx)
                    #     self.retraction_on_box.setChecked(False)

                self.uninterrupted_print_box.stateChanged.connect(
                    on_uninterrupted_print_change
                )

                self.__elements[name] = {
                    "label": uninterrupted_print,
                    "checkbox": self.uninterrupted_print_box,
                }

            case "m10_cut_distance":
                m10_cut_distance = QLabel(self.locale.M10CutDistance)
                m10_cut_distance_value = QLineEdit()
                m10_cut_distance_value.setText(
                    str(sett().uninterrupted_print.cut_distance)
                )
                m10_cut_distance_value.setValidator(self.doubleValidator)
                self.panel.addWidget(m10_cut_distance, self.next_row, 1)
                self.panel.addWidget(
                    m10_cut_distance_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": m10_cut_distance,
                    "edit": m10_cut_distance_value,
                }

            case "line_width":
                line_width = QLabel(self.locale.LineWidth)
                line_width_value = QLineEdit()
                line_width_value.setText(str(self.sett().slicing.line_width))
                line_width_value.setValidator(self.doubleValidator)
                line_width_value.textChanged.connect(self.__update_wall_thickness)
                self.panel.addWidget(line_width, self.next_row, 1)
                self.panel.addWidget(
                    line_width_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": line_width,
                    "edit": line_width_value,
                }

            case "layer_height":
                layer_height = QLabel(self.locale.LayerHeight)
                layer_height_value = QLineEdit()
                layer_height_value.setText(str(self.sett().slicing.layer_height))
                layer_height_value.setValidator(self.doubleValidator)
                layer_height_value.textChanged.connect(self.__change_layer_height)
                self.panel.addWidget(layer_height, self.next_row, 1)
                self.panel.addWidget(
                    layer_height_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": layer_height,
                    "edit": layer_height_value,
                }

            case "number_wall_lines":
                number_wall_lines_label = QLabel(self.locale.NumberWallLines)
                if self.sett().slicing.line_width > 0:
                    number_wall_lines_value = int(
                        self.sett().slicing.wall_thickness
                        / self.sett().slicing.line_width
                    )
                else:
                    number_wall_lines_value = 0

                number_wall_lines_value = LineEdit(str(number_wall_lines_value))
                number_wall_lines_value.setValidator(self.intValidator)

                number_wall_lines_value.textChanged.connect(
                    self.__update_wall_thickness
                )

                self.panel.addWidget(number_wall_lines_label, self.next_row, 1)
                self.panel.addWidget(number_wall_lines_value, self.cur_row, 2)

                wall_thickness_label = QLabel(self.locale.WallThickness)
                wall_thickness_value = LineEdit(str(self.sett().slicing.wall_thickness))
                wall_thickness_value.setReadOnly(True)
                millimeter_label = QLabel(self.locale.Millimeter)
                self.panel.addWidget(wall_thickness_label, self.cur_row, 3)
                self.panel.addWidget(wall_thickness_value, self.cur_row, 4)
                self.panel.addWidget(millimeter_label, self.cur_row, 5)

                self.__elements[name] = {
                    "label": number_wall_lines_label,
                    "edit": number_wall_lines_value,
                    "wall_thickness_label": wall_thickness_label,
                    "wall_thickness_value": wall_thickness_value,
                }

            case "number_of_bottom_layers":
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

                self.__elements[name] = {
                    "label": number_of_bottom_layers_label,
                    "edit": number_of_bottom_layers_value,
                    "bottom_thickness_label": bottom_thickness_label,
                    "bottom_thickness_value": bottom_thickness_value,
                }

            case "number_of_lids_layers":
                number_of_lids_layers_label = QLabel(self.locale.NumberOfLidLayers)
                number_of_lids_layers_value = LineEdit(
                    str(self.sett().slicing.lids_depth)
                )
                number_of_lids_layers_value.setValidator(self.intValidator)
                number_of_lids_layers_value.textChanged.connect(
                    self.__update_lid_thickness
                )

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

                self.__elements[name] = {
                    "label": number_of_lids_layers_label,
                    "edit": number_of_lids_layers_value,
                    "lid_thickness_label": lid_thickness_label,
                    "lid_thickness_value": lid_thickness_value,
                }

            case "extruder_temp":
                extruder_temp_label = QLabel(self.locale.ExtruderTemp)
                extruder_temp_value = LineEdit(
                    str(self.sett().slicing.extruder_temperature)
                )
                extruder_temp_value.setValidator(self.intValidator)
                self.panel.addWidget(extruder_temp_label, self.next_row, 1)
                self.panel.addWidget(
                    extruder_temp_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": extruder_temp_label,
                    "edit": extruder_temp_value,
                }

            case "bed_temp":
                bed_temp_label = QLabel(self.locale.BedTemp)
                bed_temp_value = LineEdit(str(self.sett().slicing.bed_temperature))
                bed_temp_value.setValidator(self.intValidator)
                self.panel.addWidget(bed_temp_label, self.next_row, 1)
                self.panel.addWidget(
                    bed_temp_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": bed_temp_label,
                    "edit": bed_temp_value,
                }

            case "skirt_line_count":
                skirt_line_count_label = QLabel(self.locale.SkirtLineCount)
                skirt_line_count_value = LineEdit(
                    str(self.sett().slicing.skirt_line_count)
                )
                skirt_line_count_value.setValidator(self.intValidator)
                self.panel.addWidget(skirt_line_count_label, self.next_row, 1)
                self.panel.addWidget(
                    skirt_line_count_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": skirt_line_count_label,
                    "edit": skirt_line_count_value,
                }

            case "fan_speed":
                fan_speed_label = QLabel(self.locale.FanSpeed)
                fan_speed_value = LineEdit(str(self.sett().slicing.fan_speed))
                fan_speed_value.setValidator(self.intValidator)
                self.panel.addWidget(fan_speed_label, self.next_row, 1)
                self.panel.addWidget(
                    fan_speed_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": fan_speed_label,
                    "edit": fan_speed_value,
                }

            case "fan_off_layer1":
                fan_off_layer1_label = QLabel(self.locale.FanOffLayer1)
                fan_off_layer1_box = QCheckBox()
                if self.sett().slicing.fan_off_layer1:
                    fan_off_layer1_box.setCheckState(QtCore.Qt.Checked)
                self.panel.addWidget(fan_off_layer1_label, self.next_row, 1)
                self.panel.addWidget(
                    fan_off_layer1_box, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": fan_off_layer1_label,
                    "checkbox": fan_off_layer1_box,
                }

            case "print_speed":
                print_speed_label = QLabel(self.locale.PrintSpeed)
                print_speed_value = LineEdit(str(self.sett().slicing.print_speed))
                print_speed_value.setValidator(self.intValidator)
                self.panel.addWidget(print_speed_label, self.next_row, 1)
                self.panel.addWidget(
                    print_speed_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": print_speed_label,
                    "edit": print_speed_value,
                }

            case "print_speed_layer1":
                print_speed_layer1_label = QLabel(self.locale.PrintSpeedLayer1)
                print_speed_layer1_value = LineEdit(
                    str(self.sett().slicing.print_speed_layer1)
                )
                print_speed_layer1_value.setValidator(self.intValidator)
                self.panel.addWidget(print_speed_layer1_label, self.next_row, 1)
                self.panel.addWidget(
                    print_speed_layer1_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": print_speed_layer1_label,
                    "edit": print_speed_layer1_value,
                }

            case "print_speed_wall":
                print_speed_wall_label = QLabel(self.locale.PrintSpeedWall)
                print_speed_wall_value = LineEdit(
                    str(self.sett().slicing.print_speed_wall)
                )
                print_speed_wall_value.setValidator(self.intValidator)
                self.panel.addWidget(print_speed_wall_label, self.next_row, 1)
                self.panel.addWidget(
                    print_speed_wall_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": print_speed_wall_label,
                    "edit": print_speed_wall_value,
                }

            case "filling_type":
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

                self.__elements[name] = {
                    "label": filling_type_label,
                    "values": filling_type_values,
                }

            case "fill_density":
                fill_density_label = QLabel(self.locale.FillDensity)
                fill_density_value = LineEdit(str(self.sett().slicing.fill_density))
                fill_density_value.setValidator(self.intValidator)
                self.panel.addWidget(fill_density_label, self.next_row, 1)
                self.panel.addWidget(
                    fill_density_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": fill_density_label,
                    "edit": fill_density_value,
                }

            case "overlap_infill":
                overlap_infill_label = QLabel(self.locale.OverlappingInfillPercentage)
                overlap_infill_value = LineEdit(
                    str(self.sett().slicing.overlapping_infill_percentage)
                )
                overlap_infill_value.setValidator(self.intValidator)
                self.panel.addWidget(overlap_infill_label, self.next_row, 1)
                self.panel.addWidget(
                    overlap_infill_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": overlap_infill_label,
                    "edit": overlap_infill_value,
                }

            case "retraction_on":
                retraction_on_label = QLabel(self.locale.Retraction)
                retraction_on_box = QCheckBox()
                if self.sett().slicing.retraction_on:
                    retraction_on_box.setCheckState(QtCore.Qt.Checked)
                self.panel.addWidget(retraction_on_label, self.next_row, 1)
                self.panel.addWidget(
                    retraction_on_box, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": retraction_on_label,
                    "checkbox": retraction_on_box,
                }

            case "retraction_distance":
                retraction_distance_label = QLabel(self.locale.RetractionDistance)
                retraction_distance_value = LineEdit(
                    str(self.sett().slicing.retraction_distance)
                )
                retraction_distance_value.setValidator(self.doubleValidator)
                self.panel.addWidget(retraction_distance_label, self.next_row, 1)
                self.panel.addWidget(
                    retraction_distance_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": retraction_distance_label,
                    "edit": retraction_distance_value,
                }

            case "retraction_speed":
                retraction_speed_label = QLabel(self.locale.RetractionSpeed)
                retraction_speed_value = LineEdit(
                    str(self.sett().slicing.retraction_speed)
                )
                retraction_speed_value.setValidator(self.intValidator)
                self.panel.addWidget(retraction_speed_label, self.next_row, 1)
                self.panel.addWidget(
                    retraction_speed_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": retraction_speed_label,
                    "edit": retraction_speed_value,
                }

            case "retraction_compensation":
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

                self.__elements[name] = {
                    "label": retraction_compensation_label,
                    "edit": retraction_compensation_value,
                }

            case "material_shrinkage":
                material_shrinkage_label = QLabel(self.locale.MaterialShrinkage)
                material_shrinkage_value = LineEdit(
                    str(self.sett().slicing.material_shrinkage)
                )
                material_shrinkage_value.setValidator(self.doublePercentValidator)
                self.panel.addWidget(material_shrinkage_label, self.next_row, 1)
                self.panel.addWidget(
                    material_shrinkage_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": material_shrinkage_label,
                    "edit": material_shrinkage_value,
                }

            case "supports_on":
                # supports_label = QLabel(self.locale.SupportsSettings)

                # supports on
                supports_on_label = QLabel(self.locale.SupportsOn)
                supports_on_box = QCheckBox()
                if self.sett().supports.enabled:
                    supports_on_box.setCheckState(QtCore.Qt.Checked)

                # self.panel.addWidget(supports_label, self.next_row, 1)

                self.panel.addWidget(supports_on_label, self.next_row, 1)
                self.panel.addWidget(
                    supports_on_box, self.cur_row, 2, 1, self.col2_cells
                )
                self.__elements[name] = {
                    # "group_label": supports_label,
                    "label": supports_on_label,
                    "checkbox": supports_on_box,
                }

            case "support_density":
                support_density_label = QLabel(self.locale.SupportDensity)
                support_density_value = LineEdit(str(self.sett().supports.fill_density))
                support_density_value.setValidator(self.intValidator)
                self.panel.addWidget(support_density_label, self.next_row, 1)
                self.panel.addWidget(
                    support_density_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": support_density_label,
                    "edit": support_density_value,
                }

            case "support_fill_type":
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

                self.__elements[name] = {
                    "label": support_fill_type_label,
                    "values": support_fill_type_values,
                }

            case "support_xy_offset":
                support_xy_offset_label = QLabel(self.locale.SupportXYOffset)
                support_xy_offset_value = LineEdit(str(self.sett().supports.xy_offset))
                support_xy_offset_value.setValidator(self.intValidator)
                self.panel.addWidget(support_xy_offset_label, self.next_row, 1)
                self.panel.addWidget(
                    support_xy_offset_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": support_xy_offset_label,
                    "edit": support_xy_offset_value,
                }

            case "support_z_offset":
                support_z_offset_label = QLabel(self.locale.SupportZOffsetLayers)
                support_z_offset_value = LineEdit(
                    str(self.sett().supports.z_offset_layers)
                )
                support_z_offset_value.setValidator(self.intValidator)
                self.panel.addWidget(support_z_offset_label, self.next_row, 1)
                self.panel.addWidget(
                    support_z_offset_value, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": support_z_offset_label,
                    "edit": support_z_offset_value,
                }

            case "support_priority_zoffset":
                support_priority_zoffset_label = QLabel(
                    self.locale.SupportPriorityZOffset
                )
                support_priorityz_offset_box = QCheckBox()
                if self.sett().supports.priority_z_offset:
                    support_priorityz_offset_box.setCheckState(QtCore.Qt.Checked)

                self.panel.addWidget(support_priority_zoffset_label, self.next_row, 1)
                self.panel.addWidget(
                    support_priorityz_offset_box, self.cur_row, 2, 1, self.col2_cells
                )

                self.__elements[name] = {
                    "label": support_priority_zoffset_label,
                    "checkbox": support_priorityz_offset_box,
                }

            case "support_number_of_bottom_layers":
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
                self.panel.addWidget(
                    support_number_of_bottom_layers_value, self.cur_row, 2
                )

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

                self.__elements[name] = {
                    "label": support_number_of_bottom_layers_label,
                    "edit": support_number_of_bottom_layers_value,
                    "bottom_thickness_label": bottom_thickness_label,
                    "bottom_thickness_value": bottom_thickness_value,
                }

            case "support_number_of_lid_layers":
                support_number_of_lid_layers_label = QLabel(
                    self.locale.NumberOfLidLayers
                )
                support_number_of_lid_layers_value = LineEdit(
                    str(self.sett().supports.lids_depth)
                )
                support_number_of_lid_layers_value.setValidator(self.intValidator)
                support_number_of_lid_layers_value.textChanged.connect(
                    self.__update_supports_lid_thickness
                )
                self.panel.addWidget(
                    support_number_of_lid_layers_label, self.next_row, 1
                )
                self.panel.addWidget(
                    support_number_of_lid_layers_value, self.cur_row, 2
                )

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

                self.__elements[name] = {
                    "label": support_number_of_lid_layers_label,
                    "edit": support_number_of_lid_layers_value,
                    "lid_thickness_label": lid_thickness_label,
                    "lid_thickness_value": lid_thickness_value,
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
