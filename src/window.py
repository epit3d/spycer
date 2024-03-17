from typing import Optional

import vtk, src
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QMainWindow, QWidget, QLabel, QLineEdit, QComboBox, QGridLayout, QSlider,
                             QCheckBox, QVBoxLayout,
                             QPushButton, QFileDialog, QScrollArea, QGroupBox, QAction, QDialog,
                             QTreeWidget, QTreeWidgetItem, QAbstractItemView, QTabWidget, QMessageBox)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src import locales, gui_utils, interactor_style
from src.InteractorAroundActivePlane import InteractionAroundActivePlane
from src.gui_utils import plane_tf, Plane, Cone
from src.settings import sett, get_color, save_settings, delete_temporary_project_files, project_change_check
import src.settings as settings
from src.figure_editor import StlMovePanel
from src.qt_utils import ClickableLineEdit
import os.path as path
import logging

NothingState = "nothing"
GCodeState = "gcode"
StlState = "stl"
BothState = "both"
MovingState = "moving"

class TreeWidget(QTreeWidget):
    itemIsMoving = False

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setHeaderLabels([locales.getLocale().Hide, "№", locales.getLocale().NamePlanes])
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.setMinimumWidth(400)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setAcceptDrops(True)

    def dragMoveEvent(self, event):
        self.itemIsMoving = True
        super().dragMoveEvent(event)

class LineEdit(QLineEdit):
    colorize_invalid_value = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.returnPressed.connect(self.value_formatting)
        self.textChanged.connect(self.input_validation)
        self.textChanged.connect(self.colorize_field)

    def setValidator(self, validator, colorize_invalid_value = False):
        self.colorize_invalid_value = colorize_invalid_value
        super().setValidator(validator)

    def focusOutEvent(self, event):
        self.value_formatting()
        self.colorize_field()
        super().focusOutEvent(event)

    def fill_empty(self):
        if (not self.text()) or (self.text() == "."):
            self.setText("0")

    def value_formatting(self):
        self.fill_empty()
        if isinstance(self.validator(), QtGui.QDoubleValidator):
            cursor_position = self.cursorPosition()
            self.setText(str(float(self.text())))
            self.setCursorPosition(cursor_position)

    def input_validation(self):
        cursor_position = self.cursorPosition()
        self.setText(self.text().replace(',', '.'))

        if (not self.colorize_invalid_value) and self.validator():
            value = float(self.text()) if self.text() else 0

            max_value = self.validator().top()
            min_value = self.validator().bottom()

            if value > max_value:
                self.setText(str(max_value))
            if value < min_value:
                self.setText(str(min_value))
        self.setCursorPosition(cursor_position)

    def colorize_field(self):
        default_background_color = "#0e1621"
        invalid_value_background_color = "#ff6e00"

        if self.colorize_invalid_value:
            if self.hasAcceptableInput() or (not self.text()):
                self.setStyleSheet(f'background-color: {default_background_color}')
            else:
                self.setStyleSheet(f'background-color: {invalid_value_background_color}')

class MainWindow(QMainWindow):
    from src.figure_editor import FigureEditor
    # by default it is None, because there is nothing to edit, will be updated by derived from FigureEditor
    parameters_tooling: Optional[FigureEditor] = None

    close_signal = QtCore.pyqtSignal()
    save_project_signal = QtCore.pyqtSignal()
    before_closing_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FASP')
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setMinimumWidth(1600)
        # self.statusBar().showMessage('Ready')

        self.locale = locales.getLocale()

        # Menu
        bar = self.menuBar()
        file_menu = bar.addMenu(self.locale.File)
        self.open_action = QAction(self.locale.Open, self)
        file_menu.addAction(self.open_action)
        # file_menu.addAction(close_action)

        self.save_gcode_action = QAction(self.locale.SaveGCode, self)
        self.save_project_action = QAction(self.locale.SaveProject, self)
        file_menu.addAction(self.save_project_action)
        self.save_project_as_action = QAction(self.locale.SaveProjectAs, self)
        file_menu.addAction(self.save_project_as_action)
        file_menu.addAction(self.save_gcode_action)
        self.save_sett_action = QAction(self.locale.SaveSettings, self)
        file_menu.addAction(self.save_sett_action)
        self.load_sett_action = QAction(self.locale.LoadSettings, self)
        file_menu.addAction(self.load_sett_action)

        self.slicing_info_action = QAction(self.locale.SlicerInfo, self)
        file_menu.addAction(self.slicing_info_action)

        tools_menu = bar.addMenu(self.locale.Tools)
        self.calibration_action = QAction(self.locale.Calibration, self)
        tools_menu.addAction(self.calibration_action)
        self.bug_report = QAction(self.locale.SubmitBugReport, self)
        tools_menu.addAction(self.bug_report)

        self.check_updates_action = QAction(self.locale.CheckUpdates, self)
        tools_menu.addAction(self.check_updates_action)

        # main parts
        central_widget = QWidget()
        main_grid = QGridLayout()
        self.widget3d = self.init3d_widget()
        main_grid.addWidget(self.widget3d, 0, 0, 20, 5)
        main_grid.addWidget(self.init_right_panel(), 0, 5, 21, 2)

        # Tabs
        tabs = QTabWidget()
        tabs.setFixedHeight(230)
        page_model_coordinates = QWidget(tabs)
        page_layout = QGridLayout()
        page_layout.setColumnMinimumWidth(0, 5)
        page_layout.setRowMinimumHeight(0, 10)

        self.move_button = QPushButton(self.locale.MoveModel)
        self.move_button.setCheckable(True)
        self.move_button.setFixedWidth(190)
        page_layout.addWidget(self.move_button, 1, 1)

        self.place_button = QPushButton(self.locale.PlaceModelOnEdge)
        self.place_button.setCheckable(True)
        self.place_button.setFixedWidth(240)
        page_layout.addWidget(self.place_button, 1, 2)

        page_layout.addWidget(self.init_stl_move_panel(), 2, 0, 1, 5)
        page_layout.setColumnStretch(0, 0)
        page_layout.setRowStretch(0, 0)

        page_model_coordinates.setLayout(page_layout)
        tabs.addTab(page_model_coordinates, locales.getLocale().ModelCoordinates)

        main_grid.addWidget(tabs, 20, 0, 1, 5)
        main_grid.setRowMinimumHeight(20, 200)

        # Making all rows stretchable, except for the row with tabs
        main_grid.setRowStretch(0, 1)
        main_grid.setRowStretch(20, 0)

        page_figure_settings = QWidget(tabs)
        tabs.addTab(page_figure_settings, locales.getLocale().FigureSettings)
        tabs.setTabEnabled(1, False)

        self.tabs = tabs

        central_widget.setLayout(main_grid)
        self.setCentralWidget(central_widget)

        self.state_nothing()

        # ###################TODO:
        self.actors = []
        self.stlActor = None
        # self.colorizeModel()

        # close_action.triggered.connect(self.close)

        ####################

    def closeEvent(self, event):
        self.before_closing_signal.emit()

        if not project_change_check():
            reply = self.projectChangeDialog()

            if reply == QMessageBox.Save:
                self.save_project_signal.emit()
                delete_temporary_project_files()
                event.accept()
            elif reply == QMessageBox.Discard:
                delete_temporary_project_files()
                event.accept()
            else:
                event.ignore()
                return

        self.close_signal.emit()
        event.accept()

        self.widget3d.Finalize()

    def projectChangeDialog(self):
        message_box = QMessageBox()
        message_box.setWindowTitle(self.locale.SavingProject)
        message_box.setText(self.locale.ProjectChange)

        message_box.addButton(QMessageBox.Save)
        message_box.addButton(QMessageBox.Discard)
        message_box.addButton(QMessageBox.Cancel)

        message_box.button(QMessageBox.Save).setText(self.locale.Save)
        message_box.button(QMessageBox.Discard).setText(self.locale.DontSave)
        message_box.button(QMessageBox.Cancel).setText(self.locale.Cancel)

        return message_box.exec()

    def init3d_widget(self):
        widget3d = QVTKRenderWindowInteractor(self)

        self.render = vtk.vtkRenderer()
        self.render.SetBackground(get_color("white"))

        widget3d.GetRenderWindow().AddRenderer(self.render)
        self.interactor = widget3d.GetRenderWindow().GetInteractor()
        self.interactor.SetInteractorStyle(None)

        self.interactor.Initialize()
        self.interactor.Start()

        #self.render.ResetCamera()
        # self.render.GetActiveCamera().AddObserver('ModifiedEvent', CameraModifiedCallback)

        # set position of camera to (5, 5, 5) and look at (0, 0, 0) and z-axis is looking up
        self.render.GetActiveCamera().SetPosition(5, 5, 5)
        self.render.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.render.GetActiveCamera().SetViewUp(0, 0, 1)

        self.customInteractor = InteractionAroundActivePlane(self.interactor, self.render)
        self.interactor.AddObserver("MouseWheelBackwardEvent", self.customInteractor.middleBtnPress)
        self.interactor.AddObserver("MouseWheelForwardEvent", self.customInteractor.middleBtnPress)
        self.interactor.AddObserver("RightButtonPressEvent", self.customInteractor.rightBtnPress)
        self.interactor.AddObserver("RightButtonReleaseEvent", self.customInteractor.rightBtnPress)
        self.interactor.AddObserver("LeftButtonPressEvent", lambda obj, event: self.customInteractor.leftBtnPress(obj, event, self))
        self.interactor.AddObserver("LeftButtonReleaseEvent", self.customInteractor.leftBtnPress)
        self.interactor.AddObserver("MouseMoveEvent", lambda obj, event: self.customInteractor.mouseMove(obj, event, self))

        # self.actor_interactor_style = interactor_style.ActorInteractorStyle(self.updateTransform)
        # self.actor_interactor_style.SetDefaultRenderer(self.render)
        # self.interactor.SetInteractorStyle(style)
        # self.camera_interactor_style = interactor_style.CameraInteractorStyle()
        # self.camera_interactor_style.SetDefaultRenderer(self.render)

        self.axesWidget = gui_utils.createAxes(self.interactor)

        self.planeActor = gui_utils.createPlaneActorCircle()
        self.planeTransform = vtk.vtkTransform()
        self.render.AddActor(self.planeActor)

        self.add_legend()

        self.splanes_actors = []

        # self.render.ResetCamera()
        # self.render.SetUseDepthPeeling(True)

        widget3d.Initialize()
        widget3d.Start()

        return widget3d

    def add_legend(self):
        hackData = vtk.vtkPolyData()  # it is hack to pass value to legend
        hackData.SetPoints(vtk.vtkPoints())

        self.legend = vtk.vtkLegendBoxActor()
        self.legend.SetNumberOfEntries(3)
        self.legend.GetEntryTextProperty().SetFontSize(15)
        self.legend.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.legend.GetPositionCoordinate().SetValue(0, 0)
        self.legend.GetPosition2Coordinate().SetCoordinateSystemToDisplay()
        self.legend.GetPosition2Coordinate().SetValue(290, 3 * 30)
        self.legend.SetEntry(0, hackData, "rotate - left mouse button", [1, 1, 1])
        self.legend.SetEntry(1, hackData, "move - middle mouse button (or shift+left)", [1, 1, 1])
        self.legend.SetEntry(2, hackData, "scale - right mouse button", [1, 1, 1])
        self.render.AddActor(self.legend)

    def init_right_panel(self):
        right_panel = QGridLayout()
        right_panel.setSpacing(5)
        right_panel.setColumnStretch(1, 1)
        right_panel.setColumnStretch(3, 1)
        right_panel.setColumnStretch(4, 1)

        сolumn2_number_of_cells = 4

        validatorLocale = QtCore.QLocale("Englishs")
        intValidator = QtGui.QIntValidator(0, 9000)

        doubleValidator = QtGui.QDoubleValidator(0.00, 9000.00, 2)
        doubleValidator.setLocale(validatorLocale)

        doublePercentValidator = QtGui.QDoubleValidator(0.00, 9000.00, 2)
        doublePercentValidator.setLocale(validatorLocale)

        # Front-end development at its best
        self.cur_row = 1

        def get_next_row():
            self.cur_row += 1
            return self.cur_row

        def get_cur_row():
            return self.cur_row
        
        # printer choice
        printer_label = QLabel(locales.getLocale().PrinterName)
        printer_basename = ""
        try:
            printer_basename = path.basename(sett().hardware.printer_dir)
            if sett().hardware.printer_dir == "" or not path.isdir(sett().hardware.printer_dir):
                # empty directory
                raise Exception("Choose default printer")

            logging.info(f"hardware printer path is {sett().hardware.printer_dir}")
        except:
            # set default path to printer config
            sett().hardware.printer_dir = path.join(settings.APP_PATH, "data", "printers", "default")
            logging.info(f"hardware printer path is default: {sett().hardware.printer_dir}")
            printer_basename = path.basename(sett().hardware.printer_dir)
            save_settings()

        self.printer_path_edit = ClickableLineEdit(printer_basename)
        self.printer_path_edit.setReadOnly(True)

        self.printer_add_btn = QPushButton("+")
        self.printer_add_btn.setToolTip(locales.getLocale().AddNewPrinter)

        right_panel.addWidget(printer_label, get_next_row(), 1)
        right_panel.addWidget(self.printer_add_btn, get_cur_row(), 2)
        right_panel.addWidget(self.printer_path_edit, get_cur_row(), 3, 1, сolumn2_number_of_cells)

        uninterrupted_print = QLabel(self.locale.UninterruptedPrint)
        self.uninterrupted_print_box = QCheckBox()
        if sett().uninterrupted_print.enabled:
            self.uninterrupted_print_box.setCheckState(QtCore.Qt.Checked)
        right_panel.addWidget(uninterrupted_print, get_next_row(), 1)
        right_panel.addWidget(self.uninterrupted_print_box, get_cur_row(), 2, 1, сolumn2_number_of_cells)
        # on check on this box, we should restrict fill type to zigzag only
        def on_uninterrupted_print_change():
            isUninterrupted = self.uninterrupted_print_box.isChecked()
            
            self.filling_type_values.setEnabled(not isUninterrupted)
            self.retraction_on_box.setEnabled(not isUninterrupted)
            self.retraction_distance_value.setEnabled(not isUninterrupted)
            self.retraction_speed_value.setEnabled(not isUninterrupted)
            self.retract_compensation_amount_value.setEnabled(not isUninterrupted)                

            if isUninterrupted:
                zigzag_idx = locales.getLocaleByLang("en").FillingTypeValues.index("ZigZag")
                self.filling_type_values.setCurrentIndex(zigzag_idx)
                self.retraction_on_box.setChecked(False)

        self.uninterrupted_print_box.stateChanged.connect(on_uninterrupted_print_change)

        # M10 cut distance setting
        m10_cut_distance_label = QLabel(self.locale.M10CutDistance)
        self.m10_cut_distance_value = LineEdit(str(sett().uninterrupted_print.cut_distance))
        self.m10_cut_distance_value.setValidator(doubleValidator)
        right_panel.addWidget(m10_cut_distance_label, get_next_row(), 1)
        right_panel.addWidget(self.m10_cut_distance_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        line_width_label = QLabel(self.locale.LineWidth)
        self.line_width_value = LineEdit(str(sett().slicing.line_width))
        self.line_width_value.setValidator(doubleValidator, True)
        right_panel.addWidget(line_width_label, get_next_row(), 1)
        right_panel.addWidget(self.line_width_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        layer_height_label = QLabel(self.locale.LayerHeight)
        self.layer_height_value = LineEdit(str(sett().slicing.layer_height))
        self.layer_height_value.setValidator(doubleValidator)
        right_panel.addWidget(layer_height_label, get_next_row(), 1)
        right_panel.addWidget(self.layer_height_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        number_wall_lines_label = QLabel(self.locale.NumberWallLines)
        if sett().slicing.line_width > 0:
            number_wall_lines = int(sett().slicing.wall_thickness/sett().slicing.line_width)
        else:
            number_wall_lines = 0
        self.number_wall_lines_value = LineEdit(str(number_wall_lines))
        self.number_wall_lines_value.setValidator(intValidator)
        right_panel.addWidget(number_wall_lines_label, get_next_row(), 1)
        right_panel.addWidget(self.number_wall_lines_value, get_cur_row(), 2)
        wall_thickness_label = QLabel(self.locale.WallThickness)
        self.wall_thickness_value = LineEdit(str(sett().slicing.wall_thickness))
        self.wall_thickness_value.setReadOnly(True)
        millimeter_label = QLabel(self.locale.Millimeter)
        right_panel.addWidget(wall_thickness_label, get_cur_row(), 3)
        right_panel.addWidget(self.wall_thickness_value, get_cur_row(), 4)
        right_panel.addWidget(millimeter_label, get_cur_row(), 5)

        number_of_bottom_layers_label = QLabel(self.locale.NumberOfBottomLayers)
        self.number_of_bottom_layers_value = LineEdit(str(sett().slicing.bottoms_depth))
        self.number_of_bottom_layers_value.setValidator(intValidator)
        right_panel.addWidget(number_of_bottom_layers_label, get_next_row(), 1)
        right_panel.addWidget(self.number_of_bottom_layers_value, get_cur_row(), 2)
        bottom_thickness_label = QLabel(self.locale.BottomThickness)
        self.bottom_thickness_value = LineEdit(str(round(sett().slicing.layer_height*sett().slicing.bottoms_depth,2)))
        self.bottom_thickness_value.setReadOnly(True)
        millimeter_label = QLabel(self.locale.Millimeter)
        right_panel.addWidget(bottom_thickness_label, get_cur_row(), 3)
        right_panel.addWidget(self.bottom_thickness_value, get_cur_row(), 4)
        right_panel.addWidget(millimeter_label, get_cur_row(), 5)

        number_of_lid_layers_label = QLabel(self.locale.NumberOfLidLayers)
        self.number_of_lid_layers_value = LineEdit(str(int(sett().slicing.lids_depth)))
        # self.number_of_lid_layers_value.setValidator(QtGui.QIntValidator(0, 100))
        self.number_of_lid_layers_value.setValidator(intValidator)
        right_panel.addWidget(number_of_lid_layers_label, get_next_row(), 1)
        right_panel.addWidget(self.number_of_lid_layers_value, get_cur_row(), 2)
        lid_thickness_label = QLabel(self.locale.LidsThickness)
        self.lid_thickness_value = LineEdit(str(round(sett().slicing.layer_height*sett().slicing.lids_depth,2)))
        self.lid_thickness_value.setReadOnly(True)
        millimeter_label = QLabel(self.locale.Millimeter)
        right_panel.addWidget(lid_thickness_label, get_cur_row(), 3)
        right_panel.addWidget(self.lid_thickness_value, get_cur_row(), 4)
        right_panel.addWidget(millimeter_label, get_cur_row(), 5)

        extruder_temp_label = QLabel(self.locale.ExtruderTemp)
        self.extruder_temp_value = LineEdit(str(sett().slicing.extruder_temperature))
        self.extruder_temp_value.setValidator(doubleValidator)
        right_panel.addWidget(extruder_temp_label, get_next_row(), 1)
        right_panel.addWidget(self.extruder_temp_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        bed_temp_label = QLabel(self.locale.BedTemp)
        self.bed_temp_value = LineEdit(str(sett().slicing.bed_temperature))
        self.bed_temp_value.setValidator(doubleValidator)
        right_panel.addWidget(bed_temp_label, get_next_row(), 1)
        right_panel.addWidget(self.bed_temp_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        skirt_line_count_label = QLabel(self.locale.SkirtLineCount)
        self.skirt_line_count_value = LineEdit(str(sett().slicing.skirt_line_count))
        self.skirt_line_count_value.setValidator(intValidator)

        right_panel.addWidget(skirt_line_count_label, get_next_row(), 1)
        right_panel.addWidget(self.skirt_line_count_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        fan_speed_label = QLabel(self.locale.FanSpeed)
        self.fan_speed_value = LineEdit(str(sett().slicing.fan_speed))
        self.fan_speed_value.setValidator(doublePercentValidator)
        right_panel.addWidget(fan_speed_label, get_next_row(), 1)
        right_panel.addWidget(self.fan_speed_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        fan_off_layer1_label = QLabel(self.locale.FanOffLayer1)
        self.fan_off_layer1_box = QCheckBox()
        if sett().slicing.fan_off_layer1:
            self.fan_off_layer1_box.setCheckState(QtCore.Qt.Checked)
        right_panel.addWidget(fan_off_layer1_label, get_next_row(), 1)
        right_panel.addWidget(self.fan_off_layer1_box, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        print_speed_label = QLabel(self.locale.PrintSpeed)
        self.print_speed_value = LineEdit(str(sett().slicing.print_speed))
        self.print_speed_value.setValidator(doubleValidator)
        right_panel.addWidget(print_speed_label, get_next_row(), 1)
        right_panel.addWidget(self.print_speed_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        print_speed_layer1_label = QLabel(self.locale.PrintSpeedLayer1)
        self.print_speed_layer1_value = LineEdit(str(sett().slicing.print_speed_layer1))
        self.print_speed_layer1_value.setValidator(doubleValidator)
        right_panel.addWidget(print_speed_layer1_label, get_next_row(), 1)
        right_panel.addWidget(self.print_speed_layer1_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        print_speed_wall_label = QLabel(self.locale.PrintSpeedWall)
        self.print_speed_wall_value = LineEdit(str(sett().slicing.print_speed_wall))
        self.print_speed_wall_value.setValidator(doubleValidator)
        right_panel.addWidget(print_speed_wall_label, get_next_row(), 1)
        right_panel.addWidget(self.print_speed_wall_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        filling_type_label = QLabel(self.locale.FillingType)
        right_panel.addWidget(filling_type_label, get_next_row(), 1)
        filling_type_values_widget = QWidget()
        filling_type_values_widget.setFixedHeight(26)
        self.filling_type_values = QComboBox(filling_type_values_widget)
        self.filling_type_values.addItems(self.locale.FillingTypeValues)
        ind = locales.getLocaleByLang("en").FillingTypeValues.index(sett().slicing.filling_type)
        self.filling_type_values.setCurrentIndex(ind)
        right_panel.addWidget(filling_type_values_widget, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        fill_density_label = QLabel(self.locale.FillDensity)
        self.fill_density_value = LineEdit(str(sett().slicing.fill_density))
        self.fill_density_value.setValidator(doublePercentValidator)
        right_panel.addWidget(fill_density_label, get_next_row(), 1)
        right_panel.addWidget(self.fill_density_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        overlapping_infill = QLabel(self.locale.OverlappingInfillPercentage)
        self.overlapping_infill_value = LineEdit(str(sett().slicing.overlapping_infill_percentage))
        self.overlapping_infill_value.setValidator(doublePercentValidator)
        right_panel.addWidget(overlapping_infill, get_next_row(), 1)
        right_panel.addWidget(self.overlapping_infill_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        retraction_on_label = QLabel(self.locale.Retraction)
        self.retraction_on_box = QCheckBox()
        if sett().slicing.retraction_on:
            self.retraction_on_box.setCheckState(QtCore.Qt.Checked)
        right_panel.addWidget(retraction_on_label, get_next_row(), 1)
        right_panel.addWidget(self.retraction_on_box, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        retraction_distance_label = QLabel(self.locale.RetractionDistance)
        self.retraction_distance_value = LineEdit(str(sett().slicing.retraction_distance))
        self.retraction_distance_value.setValidator(doubleValidator)
        right_panel.addWidget(retraction_distance_label, get_next_row(), 1)
        right_panel.addWidget(self.retraction_distance_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        retraction_speed_label = QLabel(self.locale.RetractionSpeed)
        self.retraction_speed_value = LineEdit(str(sett().slicing.retraction_speed))
        self.retraction_speed_value.setValidator(doubleValidator)
        right_panel.addWidget(retraction_speed_label, get_next_row(), 1)
        right_panel.addWidget(self.retraction_speed_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        retract_compensation_amount_label = QLabel(self.locale.RetractCompensationAmount)
        self.retract_compensation_amount_value = LineEdit(str(sett().slicing.retract_compensation_amount))
        self.retract_compensation_amount_value.setValidator(doubleValidator)
        right_panel.addWidget(retract_compensation_amount_label, get_next_row(), 1)
        right_panel.addWidget(self.retract_compensation_amount_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        material_shrinkage_label = QLabel(self.locale.MaterialShrinkage)
        self.material_shrinkage_value = LineEdit(str(sett().slicing.material_shrinkage))
        self.material_shrinkage_value.setValidator(doubleValidator)
        right_panel.addWidget(material_shrinkage_label, get_next_row(), 1)
        right_panel.addWidget(self.material_shrinkage_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        # supports related stuff section
        right_panel.addWidget(QLabel(self.locale.SupportsSettings), get_next_row(), 1, Qt.AlignCenter)

        supports_on_label = QLabel(self.locale.SupportsOn)
        self.supports_on_box = QCheckBox()
        if sett().supports.enabled:
            self.supports_on_box.setCheckState(QtCore.Qt.Checked)
        right_panel.addWidget(supports_on_label, get_next_row(), 1)
        right_panel.addWidget(self.supports_on_box, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        support_density_label = QLabel(self.locale.SupportDensity)
        self.support_density_value = LineEdit(str(sett().supports.fill_density))
        self.support_density_value.setValidator(doublePercentValidator)
        right_panel.addWidget(support_density_label, get_next_row(), 1)
        right_panel.addWidget(self.support_density_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        support_fill_type_label = QLabel(self.locale.FillingType)
        right_panel.addWidget(support_fill_type_label, get_next_row(), 1)
        support_fill_type_values_widget = QWidget()
        support_fill_type_values_widget.setFixedHeight(26)
        self.support_fill_type_values = QComboBox(support_fill_type_values_widget)
        self.support_fill_type_values.addItems(self.locale.FillingTypeValues)
        ind = locales.getLocaleByLang("en").FillingTypeValues.index(sett().supports.fill_type)
        self.support_fill_type_values.setCurrentIndex(ind)
        right_panel.addWidget(support_fill_type_values_widget, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        support_xy_offset_label = QLabel(self.locale.SupportXYOffset)
        self.support_xy_offset_value = LineEdit(str(sett().supports.xy_offset))
        self.support_xy_offset_value.setValidator(doubleValidator)
        right_panel.addWidget(support_xy_offset_label, get_next_row(), 1)
        right_panel.addWidget(self.support_xy_offset_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)
        
        support_z_offset_layers_label = QLabel(self.locale.SupportZOffsetLayers)
        self.support_z_offset_layers_value = LineEdit(str(sett().supports.z_offset_layers))
        self.support_z_offset_layers_value.setValidator(intValidator)
        right_panel.addWidget(support_z_offset_layers_label, get_next_row(), 1)
        right_panel.addWidget(self.support_z_offset_layers_value, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        support_priorityZoffset_label = QLabel(self.locale.SupportPriorityZOffset)
        self.support_priority_z_offset_box = QCheckBox()
        if sett().supports.priority_z_offset:
            self.support_priority_z_offset_box.setCheckState(QtCore.Qt.Checked)
        right_panel.addWidget(support_priorityZoffset_label, get_next_row(), 1)
        right_panel.addWidget(self.support_priority_z_offset_box, get_cur_row(), 2, 1, сolumn2_number_of_cells)

        supports_number_of_bottom_layers_label = QLabel(self.locale.NumberOfBottomLayers)
        self.supports_number_of_bottom_layers_value = LineEdit(str(sett().supports.bottoms_depth))
        self.supports_number_of_bottom_layers_value.setValidator(intValidator)
        right_panel.addWidget(supports_number_of_bottom_layers_label, get_next_row(), 1)
        right_panel.addWidget(self.supports_number_of_bottom_layers_value, get_cur_row(), 2)
        supports_bottom_thickness_label = QLabel(self.locale.BottomThickness)
        self.supports_bottom_thickness_value = LineEdit(str(round(sett().slicing.layer_height*sett().supports.bottoms_depth,2)))
        self.supports_bottom_thickness_value.setReadOnly(True)
        millimeter_label = QLabel(self.locale.Millimeter)
        right_panel.addWidget(supports_bottom_thickness_label, get_cur_row(), 3)
        right_panel.addWidget(self.supports_bottom_thickness_value, get_cur_row(), 4)
        right_panel.addWidget(millimeter_label, get_cur_row(), 5)

        supports_number_of_lid_layers_label = QLabel(self.locale.NumberOfLidLayers)
        self.supports_number_of_lid_layers_value = LineEdit(str(int(sett().supports.lids_depth)))
        # self.number_of_lid_layers_value.setValidator(QtGui.QIntValidator(0, 100))
        self.supports_number_of_lid_layers_value.setValidator(intValidator)
        right_panel.addWidget(supports_number_of_lid_layers_label, get_next_row(), 1)
        right_panel.addWidget(self.supports_number_of_lid_layers_value, get_cur_row(), 2)
        supports_lid_thickness_label = QLabel(self.locale.LidsThickness)
        self.supports_lid_thickness_value = LineEdit(str(round(sett().slicing.layer_height*sett().supports.lids_depth,2)))
        self.supports_lid_thickness_value.setReadOnly(True)
        millimeter_label = QLabel(self.locale.Millimeter)
        right_panel.addWidget(supports_lid_thickness_label, get_cur_row(), 3)
        right_panel.addWidget(self.supports_lid_thickness_value, get_cur_row(), 4)
        right_panel.addWidget(millimeter_label, get_cur_row(), 5)

        self.name_stl_file = QLabel("")

        self.warning_nozzle_and_table_collision = QLabel("")
        self.warning_nozzle_and_table_collision.setStyleSheet("QLabel {color : red;}")
        self.warning_nozzle_and_table_collision.setWordWrap(True)

        # BUTTONS
        buttons_layout = QGridLayout()
        buttons_layout.setSpacing(5)
        buttons_layout.setColumnMinimumWidth(3, 250)
        # buttons_layout.setColumnStretch(0, 2)

        self.model_switch_box = QCheckBox(self.locale.ShowStl)
        buttons_layout.addWidget(self.model_switch_box, get_next_row(), 1)
        self.print_time_label = QLabel(self.locale.PrintTime)
        self.print_time_value = QLabel("")
        buttons_layout.addWidget(self.print_time_label, get_cur_row(), 2, Qt.AlignmentFlag(3))
        buttons_layout.addWidget(self.print_time_value, get_cur_row(), 3)

        self.model_centering_box = QCheckBox(self.locale.ModelCentering)
        buttons_layout.addWidget(self.model_centering_box, get_next_row(), 1)
        self.consumption_material_label = QLabel(self.locale.ConsumptionMaterial)
        self.consumption_material_value = QLabel("")
        buttons_layout.addWidget(self.consumption_material_label, get_cur_row(), 2, Qt.AlignmentFlag(3))
        buttons_layout.addWidget(self.consumption_material_value, get_cur_row(), 3)

        self.model_align_height = QCheckBox(self.locale.AlignModelHeight)
        self.model_align_height.setChecked(True)
        buttons_layout.addWidget(self.model_align_height, get_next_row(), 1)

        self.slider_label = QLabel(self.locale.LayersCount)
        self.layers_number_label = QLabel()
        buttons_layout.addWidget(self.slider_label, get_next_row(), 1)
        buttons_layout.addWidget(self.layers_number_label, get_cur_row(), 2)

        self.picture_slider = QSlider()
        self.picture_slider.setOrientation(QtCore.Qt.Horizontal)
        self.picture_slider.setMinimum(0)
        self.picture_slider.setValue(0)
        buttons_layout.addWidget(self.picture_slider, get_next_row(), 1, 1, 3)

        # self.x_position_value = QLineEdit("0")
        # buttons_layout.addWidget(self.x_position_value, get_next_row(), 1)
        # self.y_position_value = QLineEdit("0")
        # buttons_layout.addWidget(self.y_position_value, get_cur_row(), 2)
        # self.z_position_value = QLineEdit("0")
        # buttons_layout.addWidget(self.z_position_value, get_next_row(), 1)

        self.xyz_position_value = QLabel("Position: 0 0 0")
        buttons_layout.addWidget(self.xyz_position_value, get_next_row(), 1, 1, 3)
        self.xyz_scale_value = QLabel("Scale: 1 1 1")
        buttons_layout.addWidget(self.xyz_scale_value, get_next_row(), 1, 1, 3)
        self.xyz_orient_value = QLabel("Orientation: 0 0 0")
        buttons_layout.addWidget(self.xyz_orient_value, get_next_row(), 1, 1, 3)

        self.load_model_button = QPushButton(self.locale.OpenModel)
        buttons_layout.addWidget(self.load_model_button, get_next_row(), 1, 1, 2)

        self.save_gcode_button = QPushButton(self.locale.SaveGCode)
        buttons_layout.addWidget(self.save_gcode_button, get_cur_row(), 3)

        self.critical_wall_overhang_angle_label = QLabel(self.locale.CriticalWallOverhangAngle)
        buttons_layout.addWidget(self.critical_wall_overhang_angle_label, get_next_row(), 1, 1, 2)
        buttons_layout.setColumnMinimumWidth(1, 230)
        self.colorize_angle_value = LineEdit(str(sett().slicing.angle))
        self.colorize_angle_value.setValidator(doubleValidator)
        buttons_layout.addWidget(self.colorize_angle_value, get_cur_row(), 2, 1, 1)

        self.color_model_button = QPushButton(self.locale.ColorModel)
        buttons_layout.addWidget(self.color_model_button, get_cur_row(), 3)

        self.slice_vip_button = QPushButton(self.locale.SliceVip)
        buttons_layout.addWidget(self.slice_vip_button, get_next_row(), 1, 1, 2)

        self.slice3a_button = QPushButton(self.locale.Slice3Axes)
        buttons_layout.addWidget(self.slice3a_button, get_cur_row(), 3)

        panel_widget = QWidget()
        panel_widget.setLayout(right_panel)

        scroll = QScrollArea()
        scroll.setWidget(panel_widget)
        scroll.setWidgetResizable(True)
        # scroll.setFixedHeight(400)

        v_layout = QVBoxLayout()
        v_layout.addWidget(scroll)
        settings_group = QGroupBox(self.locale.Settings)
        settings_group.setLayout(v_layout)

        buttons_group = QWidget()
        buttons_group.setLayout(buttons_layout)

        high_layout = QVBoxLayout()
        high_layout.addWidget(settings_group)
        high_layout.addWidget(self.name_stl_file)
        high_layout.addWidget(self.warning_nozzle_and_table_collision)
        high_layout.addWidget(buttons_group)
        high_layout.addWidget(self.init_figure_panel())
        high_widget = QWidget()
        high_widget.setLayout(high_layout)

        return high_widget

    def init_figure_panel(self):
        bottom_layout = QGridLayout()
        bottom_layout.setSpacing(5)
        bottom_layout.setColumnStretch(7, 1)

        self.splanes_tree = TreeWidget()
        bottom_layout.addWidget(self.splanes_tree, 0, 0, 5, 1)

        # self.tilted_checkbox = QCheckBox(self.locale.Tilted)
        # bottom_layout.addWidget(self.tilted_checkbox, 0, 2)

        self.hide_checkbox = QCheckBox(self.locale.Hide)
        bottom_layout.addWidget(self.hide_checkbox, 0, 2)

        self.add_plane_button = QPushButton(self.locale.AddPlane)
        bottom_layout.addWidget(self.add_plane_button, 1, 2)

        self.add_cone_button = QPushButton(self.locale.AddCone)
        bottom_layout.addWidget(self.add_cone_button, 2, 2)

        self.remove_plane_button = QPushButton(self.locale.DeletePlane)
        bottom_layout.addWidget(self.remove_plane_button, 3, 2)

        self.edit_figure_button = QPushButton(self.locale.EditFigure)
        bottom_layout.addWidget(self.edit_figure_button, 4, 2)

        self.save_planes_button = QPushButton(self.locale.SavePlanes)
        bottom_layout.addWidget(self.save_planes_button, 1, 3)

        self.download_planes_button = QPushButton(self.locale.DownloadPlanes)
        bottom_layout.addWidget(self.download_planes_button, 2, 3)

        bottom_panel = QWidget()
        bottom_panel.setLayout(bottom_layout)
        bottom_panel.setEnabled(False)
        self.bottom_panel = bottom_panel
        return bottom_panel

    def init_stl_move_panel(self):
        stlRotator = gui_utils.StlRotator(self)

        def translate(x, y, z):

            def translatePos():
                stlTranslator.act(5, [x, y, z])

            def translateNeg():
                stlTranslator.act(-5, [x, y, z])

            def translateSet(self):
                stlTranslator.set(self.text(), [x, y, z])

            return translatePos, translateNeg, translateSet

        def rotate(x, y, z):

            def rotatePos():
                stlRotator.act(5, [x, y, z])

            def rotateNeg():
                stlRotator.act(-5, [x, y, z])

            def rotateSet(text):
                stlRotator.set(text, [x, y, z])

            return rotatePos, rotateNeg, rotateSet

        stlTranslator = gui_utils.StlTranslator(self)

        stlScale = gui_utils.StlScale(self)

        def scale(x, y, z):

            def scalePos():
                stlScale.act(5, [x, y, z])

            def scaleNeg():
                stlScale.act(-5, [x, y, z])

            def scaleSet(self):
                stlScale.set(self.text(), [x, y, z])

            return scalePos, scaleNeg, scaleSet

        self.stl_move_panel = StlMovePanel(
            {
                (0, "X"): translate(1, 0, 0),
                (0, "Y"): translate(0, 1, 0),
                (0, "Z"): translate(0, 0, 1),
                (1, "X"): rotate(1, 0, 0),
                (1, "Y"): rotate(0, 1, 0),
                (1, "Z"): rotate(0, 0, 1),
                (2, "X"): scale(1, 0, 0),
                (2, "Y"): scale(0, 1, 0),
                (2, "Z"): scale(0, 0, 1),
            },
            captions=[
                self.locale.StlMoveTranslate,
                self.locale.StlMoveRotate,
                self.locale.StlMoveScale,
            ]
        )
        self.stl_move_panel.setFixedHeight = 100
        return self.stl_move_panel

    def switch_stl_gcode(self):
        if self.model_switch_box.isChecked():
            self.picture_slider.setValue(0)
            self.model_switch_box.setChecked(True)
            for actor in self.actors:
                actor.VisibilityOff()
            self.stlActor.VisibilityOn()
        else:
            for layer in range(self.picture_slider.value()):
                self.actors[layer].VisibilityOn()
            self.stlActor.VisibilityOff()
        self.reload_scene()

    def model_centering(self):
        s = sett()
        s.slicing.model_centering = self.model_centering_box.isChecked()
        save_settings()
        self.reset_colorize()

        origin = gui_utils.findStlOrigin(self.stlActor)
        bound = gui_utils.getBounds(self.stlActor)
        z_mid = (bound[4] + bound[5]) / 2
        origin = origin[0], origin[1], z_mid

        transform = self.stlActor.GetUserTransform()
        transform.PostMultiply()
        transform.Translate(-origin[0], -origin[1], -origin[2])

        if s.slicing.model_centering:
            self.stlActor.lastMove = origin
        else:
            transform.Translate(self.stlActor.lastMove)

        if self.model_align_height.isChecked():
            xc, yc, zmin = gui_utils.findStlOrigin(self.stlActor)
            transform.Translate(0, 0, -zmin)

        transform.PreMultiply()

        self.stlActor.SetUserTransform(transform)

        if not self.boxWidget is None:
            self.boxWidget.SetTransform(transform)

        self.updateTransform()
        self.reload_scene()

    def clear_scene(self):
        self.render.RemoveAllViewProps()
        self.render.AddActor(self.planeActor)
        self.render.AddActor(self.legend)
        self.rotate_plane(vtk.vtkTransform())

    def reload_scene(self):
        self.render.Modified()
        self.interactor.Render()

    def change_layer_view(self, new_slider_value, prev_value, gcd):  # shows +1 layer to preview finish

        if prev_value is None:
            return new_slider_value

        last = False if len(self.actors) > new_slider_value else True
        prev_last = False if len(self.actors) > prev_value else True

        if not last:
            self.actors[new_slider_value].GetProperty().SetColor(get_color(sett().colors.last_layer))
            self.actors[new_slider_value].GetProperty().SetLineWidth(4)
            self.actors[new_slider_value].GetProperty().SetOpacity(sett().common.opacity_last_layer)
        if not prev_last:
            self.actors[prev_value].GetProperty().SetColor(get_color(sett().colors.layer))
            self.actors[prev_value].GetProperty().SetLineWidth(1)
            self.actors[prev_value].GetProperty().SetOpacity(sett().common.opacity_layer)

        self.layers_number_label.setText(str(new_slider_value))

        if new_slider_value < prev_value:
            for layer in range(new_slider_value + 1, prev_value if prev_last else prev_value + 1):
                self.actors[layer].VisibilityOff()
        else:
            for layer in range(prev_value, new_slider_value if last else new_slider_value + 1):
                self.actors[layer].VisibilityOn()

        new_rot = gcd.lays2rots[0] if last else gcd.lays2rots[new_slider_value]
        prev_rot = gcd.lays2rots[0] if prev_last else gcd.lays2rots[prev_value]

        if new_rot != prev_rot:
            curr_rotation = gcd.rotations[new_rot]
            for block in range(new_slider_value if last else new_slider_value + 1):
                # revert prev rotation firstly and then apply current
                tf = gui_utils.prepareTransform(gcd.rotations[gcd.lays2rots[block]], curr_rotation)
                self.actors[block].SetUserTransform(tf)

            self.rotate_plane(plane_tf(curr_rotation))
            # for i in range(len(self.planes)):
            #     self.rotateAnyPlane(self.planesActors[i], self.planes[i], currRotation)
        return new_slider_value

    def move_stl2(self):
        if self.move_button.isChecked():
            self.state_moving()

            # self.interactor.SetInteractorStyle(self.actor_interactor_style)

            self.axesWidget.SetEnabled(False)
            if self.boxWidget is None:
                self.boxWidget = vtk.vtkBoxWidget()
                self.boxWidget.SetInteractor(self.interactor)
                # self.boxWidget.SetProp3D(self.stlActor)
                self.boxWidget.SetPlaceFactor(1.25)
                self.boxWidget.SetHandleSize(0.005)
                self.boxWidget.SetEnabled(True)
                self.boxWidget.SetScalingEnabled(True)

                # hack for boxWidget - 1. reset actor transform
                # 2. place boxWidget
                # 3. apply transform to actor and boxWidget
                tf = self.stlActor.GetUserTransform()
                self.stlActor.SetUserTransform(vtk.vtkTransform())
                self.boxWidget.SetProp3D(self.stlActor)
                self.boxWidget.PlaceWidget()
                self.boxWidget.SetTransform(tf)
                self.stlActor.SetUserTransform(tf)

                def TransformActor(obj, event):
                    tf = vtk.vtkTransform()
                    obj.GetTransform(tf)
                    # print(tf.GetScale())
                    self.stlActor.SetUserTransform(tf)
                    self.updateTransform()
                    origin = gui_utils.findStlOrigin(self.stlActor)
                    if origin != (0, 0, 0):
                        self.stlActor.lastMove = origin
                        self.model_centering_box.setChecked(False)

                self.boxWidget.AddObserver("InteractionEvent", TransformActor)
            else:
                self.boxWidget.SetEnabled(True)
            # self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballActor()
        else:
            self.state_stl()  # TODO: might be not stl but both or gcode
            # self.interactor.SetInteractorStyle(self.camera_interactor_style)
            self.boxWidget.SetEnabled(False)
            self.axesWidget.SetEnabled(True)
            xc, yc, zmin = gui_utils.findStlOrigin(self.stlActor)
            tf = self.stlActor.GetUserTransform()
            tf.PostMultiply()
            if self.model_align_height.isChecked():
                tf.Translate(0, 0, -zmin)
            tf.PreMultiply()
            self.reset_colorize()
            self.stlActor.SetUserTransform(tf)
            self.boxWidget.SetTransform(tf)
            self.updateTransform()
            # self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballCamera()
        self.reload_scene()

    def updateTransform(self):
        tf = self.stlActor.GetUserTransform()
        x, y, z = tf.GetPosition()
        # self.x_position_value.setText(str(x)[:10])
        # self.y_position_value.setText(str(y)[:10])
        # self.z_position_value.setText(str(z)[:10])
        self.xyz_position_value.setText(f"Position: {x:.2f} {y:.2f} {z:.2f}")
        a, b, c = tf.GetScale()
        self.xyz_scale_value.setText(f"Scale: {a:.2f} {b:.2f} {c:.2f}")
        i, j, k = tf.GetOrientation()
        self.xyz_orient_value.setText(f"Orientation: {i:.2f} {j:.2f} {k:.2f}")

    def save_dialog(self, caption, format = "STL (*.stl *.STL);;Gcode (*.gcode)", directory="/home/l1va/Downloads/5axes_3d_printer/test"): # TODO: fix path
        return QFileDialog.getSaveFileName(None, caption, directory, format)[0]

    def open_dialog(self, caption, format = "STL (*.stl *.STL);;Gcode (*.gcode)", directory="/home/l1va/Downloads/5axes_3d_printer/test"): # TODO: fix path
        return QFileDialog.getOpenFileName(None, caption, directory, format)[0]

    def load_stl(self, stl_actor):
        self.clear_scene()
        self.boxWidget = None
        self.stlActor = stl_actor
        self.stlActor.addUserTransformUpdateCallback(self.stl_move_panel.update)
        # self.actor_interactor_style.setStlActor(self.stlActor)
        self.updateTransform()

        self.render.AddActor(self.stlActor)
        self.state_stl()
        #self.render.ResetCamera()
        self.render.GetActiveCamera().SetClippingRange(100, 10000)
        self.reload_scene()

    def hide_splanes(self):
        if self.hide_checkbox.isChecked():
            for s in self.splanes_actors:
                s.VisibilityOff()
        else:
            for i, s in enumerate(self.splanes_actors):
                if not self.splanes_tree.topLevelItem(i).checkState(0) == Qt.CheckState.Checked:
                    s.VisibilityOn()
        self.reload_scene()

    def reload_splanes(self, splanes):
        self.reset_colorize()
        self._recreate_splanes(splanes)
        self.splanes_tree.clear()
        for i in range(len(splanes)):
            row = QTreeWidgetItem(self.splanes_tree)

            if self.splanes_actors[i].GetVisibility():
                row.setCheckState(0, Qt.CheckState.Unchecked)
            else:
                row.setCheckState(0, Qt.CheckState.Checked)

            row.setText(1, str(i + 1))
            row.setText(2, splanes[i].toFile())
            # self.splanes_list.addItem(self.locale.Plane + " " + str(i + 1))

        if len(splanes) > 0:
            self.splanes_tree.setCurrentItem(self.splanes_tree.topLevelItem(len(splanes) - 1))
        self.reload_scene()

    def _recreate_splanes(self, splanes):
        for p in self.splanes_actors:
            self.render.RemoveActor(p)
        self.splanes_actors = []
        for i, p in enumerate(splanes):
            if isinstance(p, Plane):
                act = gui_utils.create_splane_actor([p.x, p.y, p.z], p.incline, p.rot)
            else:  # isinstance(p, Cone):
                act = gui_utils.create_cone_actor((p.x, p.y, p.z), p.cone_angle, p.h1, p.h2)

            row = self.splanes_tree.topLevelItem(i)
            if row != None:
                if (row.checkState(0) == QtCore.Qt.CheckState.Checked) or self.hide_checkbox.isChecked():
                    act.VisibilityOff()
            # act = gui_utils.create_cone_actor((p.x, p.y, p.z), p.cone_angle)
            self.splanes_actors.append(act)
            self.render.AddActor(act)

    def update_splane(self, sp, ind):
        self.reset_colorize()
        settableVisibility = self.splanes_actors[ind].GetVisibility() and not self.hide_checkbox.isChecked()
        self.render.RemoveActor(self.splanes_actors[ind])
        # TODO update to pass values as self.splanes_actors[ind], and only then destruct object
        act = gui_utils.create_splane_actor([sp.x, sp.y, sp.z], sp.incline, sp.rot)

        if settableVisibility:
            act.VisibilityOn()
        else:
            act.VisibilityOff()

        self.splanes_actors[ind] = act
        self.render.AddActor(act)
        sel = self.splanes_tree.currentIndex().row()
        if sel == ind:
            self.splanes_actors[sel].GetProperty().SetColor(get_color(sett().colors.last_layer))
            self.splanes_actors[sel].GetProperty().SetOpacity(0.8)
        self.reload_scene()

    def update_cone(self, cone: Cone, ind):
        self.render.RemoveActor(self.splanes_actors[ind])
        # TODO update to pass values as self.splanes_actors[ind], and only then destruct object
        act = gui_utils.create_cone_actor((cone.x, cone.y, cone.z), cone.cone_angle, cone.h1, cone.h2)
        self.splanes_actors[ind] = act
        self.render.AddActor(act)
        sel = self.splanes_tree.currentIndex().row()
        if sel == ind:
            self.splanes_actors[sel].GetProperty().SetColor(get_color(sett().colors.last_layer))
            self.splanes_actors[sel].GetProperty().SetOpacity(sett().common.opacity_current_plane)
        self.reload_scene()

    def change_combo_select(self, plane, ind):
        for p in self.splanes_actors:
            p.GetProperty().SetColor(get_color(sett().colors.splane))
            p.GetProperty().SetOpacity(sett().common.opacity_plane)
        self.splanes_actors[ind].GetProperty().SetColor(get_color(sett().colors.last_layer))
        self.splanes_actors[ind].GetProperty().SetOpacity(sett().common.opacity_current_plane)
        self.reload_scene()

    def load_gcode(self, actors, is_from_stl, plane_tf):
        self.reset_colorize()
        self.clear_scene()
        if is_from_stl:
            self.stlActor.VisibilityOff()
            self.render.AddActor(self.stlActor)

        if plane_tf:
            self.rotate_plane(plane_tf)

        self.actors = actors
        for actor in self.actors:
            self.render.AddActor(actor)

        if is_from_stl:
            self.state_both(len(self.actors))
        else:
            self.state_gcode(len(self.actors))

        #self.render.ResetCamera()
        self.reload_scene()

    def rotate_plane(self, tf):
        self.planeActor.SetUserTransform(tf)
        self.planeTransform = tf

        # i, j, k = tf.GetOrientation()
        # print("Orientation: " + strF(i) + " " + strF(j) + " " + strF(k))
        # self.xyz_orient_value.setText("Orientation: " + strF(i) + " " + strF(j) + " " + strF(k))

    def save_gcode_dialog(self):
        return QFileDialog.getSaveFileName(None, self.locale.SaveGCode, "", "Gcode (*.gcode)")[0]

    def about_dialog(self):
        d = QDialog()
        d.setWindowTitle("About Epit3d")
        d.setWindowModality(Qt.ApplicationModal)
        d.setMinimumSize(250, 200)

        v_layout = QVBoxLayout()

        site_label = QLabel("Site Url: <a href=\"https://www.epit3d.ru/\">epit3d.ru</a>")
        site_label.setOpenExternalLinks(True)
        # site_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v_layout.addWidget(site_label)

        phone_label = QLabel("Phone: +7 (960) 086-11-97")
        phone_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v_layout.addWidget(phone_label)

        email_label = QLabel(
            "E-mail: <a href='mailto:Info@epit3d.ru?subject=FASP Question&body=My question is ...'>Info@epit3d.ru</a>")
        # email_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        site_label.setOpenExternalLinks(True)
        v_layout.addWidget(email_label)

        ok = QPushButton("ok")
        ok.clicked.connect(d.close)
        v_layout.addWidget(ok)

        d.setLayout(v_layout)
        d.exec_()

    def state_nothing(self):
        self.model_switch_box.setEnabled(False)
        self.model_switch_box.setChecked(False)
        self.model_centering_box.setEnabled(False)
        self.model_centering_box.setChecked(False)
        self.model_align_height.setEnabled(False)
        self.slider_label.setEnabled(False)
        self.layers_number_label.setEnabled(False)
        self.layers_number_label.setText(" ")
        self.picture_slider.setEnabled(False)
        self.picture_slider.setSliderPosition(0)
        self.move_button.setEnabled(False)
        self.place_button.setEnabled(False)
        self.load_model_button.setEnabled(True)
        self.slice3a_button.setEnabled(False)
        self.color_model_button.setEnabled(False)
        self.slice_vip_button.setEnabled(False)
        self.save_gcode_button.setEnabled(False)
        self.hide_checkbox.setChecked(False)
        self.bottom_panel.setEnabled(False)
        self.stl_move_panel.setEnabled(False)
        self.state = NothingState

    def state_gcode(self, layers_count):
        self.model_switch_box.setEnabled(False)
        self.model_switch_box.setChecked(False)
        self.model_centering_box.setEnabled(False)
        self.model_align_height.setEnabled(False)
        self.slider_label.setEnabled(True)
        self.layers_number_label.setEnabled(True)
        self.layers_number_label.setText(str(layers_count))
        self.picture_slider.setEnabled(True)
        self.picture_slider.setMaximum(layers_count)
        self.picture_slider.setSliderPosition(layers_count)
        self.move_button.setEnabled(False)
        self.place_button.setEnabled(False)
        self.load_model_button.setEnabled(True)
        self.slice3a_button.setEnabled(False)
        self.color_model_button.setEnabled(False)
        self.slice_vip_button.setEnabled(False)
        self.save_gcode_button.setEnabled(True)
        self.hide_checkbox.setChecked(True)
        self.bottom_panel.setEnabled(False)
        self.stl_move_panel.setEnabled(False)
        self.state = GCodeState

    def state_stl(self):
        self.model_switch_box.setEnabled(False)
        self.model_switch_box.setChecked(True)
        self.model_centering_box.setEnabled(True)
        self.model_align_height.setEnabled(True)
        self.slider_label.setEnabled(False)
        self.layers_number_label.setEnabled(False)
        self.layers_number_label.setText(" ")
        self.picture_slider.setEnabled(False)
        self.picture_slider.setSliderPosition(0)
        self.move_button.setEnabled(True)
        self.place_button.setEnabled(True)
        self.load_model_button.setEnabled(True)
        self.slice3a_button.setEnabled(True)
        self.color_model_button.setEnabled(True)
        self.slice_vip_button.setEnabled(True)
        self.save_gcode_button.setEnabled(False)
        self.hide_checkbox.setChecked(False)
        self.bottom_panel.setEnabled(True)
        self.stl_move_panel.setEnabled(False)
        self.state = StlState

    def state_moving(self):
        self.model_switch_box.setEnabled(False)
        self.model_switch_box.setChecked(True)
        self.model_centering_box.setEnabled(True)
        self.model_align_height.setEnabled(True)
        self.slider_label.setEnabled(False)
        self.layers_number_label.setEnabled(False)
        self.layers_number_label.setText(" ")
        self.picture_slider.setEnabled(False)
        self.picture_slider.setSliderPosition(0)
        self.move_button.setEnabled(True)
        self.place_button.setEnabled(True)
        self.load_model_button.setEnabled(False)
        self.slice3a_button.setEnabled(False)
        self.color_model_button.setEnabled(False)
        self.slice_vip_button.setEnabled(False)
        self.save_gcode_button.setEnabled(False)
        # self.hide_checkbox.setChecked(False)
        self.bottom_panel.setEnabled(False)
        self.stl_move_panel.setEnabled(True)
        self.state = MovingState

    def state_both(self, layers_count):
        self.model_switch_box.setEnabled(True)
        self.model_switch_box.setChecked(False)
        self.model_centering_box.setEnabled(False)
        self.model_align_height.setEnabled(False)
        self.slider_label.setEnabled(True)
        self.layers_number_label.setEnabled(True)
        self.layers_number_label.setText(str(layers_count))
        self.picture_slider.setEnabled(True)
        self.picture_slider.setMaximum(layers_count)
        self.picture_slider.setSliderPosition(layers_count)
        self.move_button.setEnabled(True)
        self.place_button.setEnabled(True)
        self.load_model_button.setEnabled(True)
        self.slice3a_button.setEnabled(True)
        self.color_model_button.setEnabled(True)
        self.slice_vip_button.setEnabled(True)
        self.save_gcode_button.setEnabled(True)
        self.hide_checkbox.setChecked(True)
        self.bottom_panel.setEnabled(True)
        self.stl_move_panel.setEnabled(False)
        self.state = BothState

    def reset_colorize(self):
        if self.stlActor:
            self.stlActor.ResetColorize()

def strF(v):  # cut 3 numbers after the point in float
    s = str(v)
    i = s.find(".")
    if i != -1:
        s = s[:min(len(s), i + 3)]
    return s
