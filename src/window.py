from typing import Optional

import vtk, src
from PyQt5 import QtCore
from PyQt5 import QtGui
from PyQt5.QtCore import Qt, QEvent
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QMainWindow,
    QWidget,
    QLabel,
    QComboBox,
    QGridLayout,
    QSlider,
    QCheckBox,
    QVBoxLayout,
    QPushButton,
    QFileDialog,
    QScrollArea,
    QGroupBox,
    QAction,
    QDialog,
    QTreeWidget,
    QTreeWidgetItem,
    QAbstractItemView,
    QTabWidget,
    QMessageBox,
)
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor

from src import locales, gui_utils, interactor_style
from src.InteractorAroundActivePlane import InteractionAroundActivePlane
from src.gui_utils import plane_tf, Plane, Cone, showErrorDialog
from src.settings import (
    sett,
    get_color,
    save_settings,
    delete_temporary_project_files,
    project_change_check,
)
import src.settings as settings
from src.figure_editor import StlMovePanel
from src.qt_utils import ClickableLineEdit, LineEdit
from src.settings_widget import SettingsWidget
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

        self.setHeaderLabels(
            [locales.getLocale().Hide, "№", locales.getLocale().NamePlanes]
        )
        self.resizeColumnToContents(0)
        self.resizeColumnToContents(1)
        self.setMinimumWidth(400)

        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setDragDropMode(QAbstractItemView.InternalMove)
        self.setDragEnabled(True)
        self.setDropIndicatorShown(True)
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e: QtGui.QDragEnterEvent) -> None:
        # we cannot start dragging the first row
        item = self.selectedItems()[0]
        idx = self.indexFromItem(item)
        if idx.row() == 0:
            e.ignore()
            return

        return super().dragEnterEvent(e)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        self.itemIsMoving = True
        super().dragMoveEvent(event)

    def dropEvent(self, event):
        # we cannot drop on the first row
        if self.indexAt(event.pos()).row() == 0:
            showErrorDialog(locales.getLocale().CannotDropHere)
            return

        super().dropEvent(event)


class MainWindow(QMainWindow):
    from src.figure_editor import FigureEditor

    # by default it is None, because there is nothing to edit, will be updated by derived from FigureEditor
    parameters_tooling: Optional[FigureEditor] = None

    close_signal = QtCore.pyqtSignal()
    save_project_signal = QtCore.pyqtSignal()
    before_closing_signal = QtCore.pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FASP")
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

        help_menu = bar.addMenu(self.locale.Help)
        self.slicing_info_action = QAction(self.locale.SlicerInfo, self)
        help_menu.addAction(self.slicing_info_action)

        self.documentation_action = QAction(self.locale.Documentation, self)
        help_menu.addAction(self.documentation_action)

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

        self.cancel_action = QPushButton(self)
        self.cancel_action.setIcon(QtGui.QIcon("icons/undo.png"))
        self.cancel_action.setIconSize(QtCore.QSize(20, 20))
        self.cancel_action.setToolTip("Undo")
        self.cancel_action.setCheckable(False)
        self.cancel_action.setFixedWidth(30)
        page_layout.addWidget(self.cancel_action, 1, 4)

        self.return_action = QPushButton(self)
        self.return_action.setIcon(QtGui.QIcon("icons/redo.png"))
        self.return_action.setIconSize(QtCore.QSize(20, 20))
        self.return_action.setToolTip("Redo")
        self.return_action.setCheckable(False)
        self.return_action.setFixedWidth(30)
        page_layout.addWidget(self.return_action, 1, 5)

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
        widget3d.installEventFilter(self)

        self.render = vtk.vtkRenderer()
        self.render.SetBackground(get_color("white"))

        widget3d.GetRenderWindow().AddRenderer(self.render)
        self.interactor = widget3d.GetRenderWindow().GetInteractor()
        self.interactor.SetInteractorStyle(None)

        self.interactor.Initialize()
        self.interactor.Start()

        # self.render.ResetCamera()
        # self.render.GetActiveCamera().AddObserver('ModifiedEvent', CameraModifiedCallback)

        # set position of camera to (5, 5, 5) and look at (0, 0, 0) and z-axis is looking up
        self.render.GetActiveCamera().SetPosition(5, 5, 5)
        self.render.GetActiveCamera().SetFocalPoint(0, 0, 0)
        self.render.GetActiveCamera().SetViewUp(0, 0, 1)

        self.customInteractor = InteractionAroundActivePlane(
            self.interactor, self.render
        )
        self.interactor.AddObserver(
            "MouseWheelBackwardEvent", self.customInteractor.middleBtnPress
        )
        self.interactor.AddObserver(
            "MouseWheelForwardEvent", self.customInteractor.middleBtnPress
        )
        self.interactor.AddObserver(
            "RightButtonPressEvent", self.customInteractor.rightBtnPress
        )
        self.interactor.AddObserver(
            "RightButtonReleaseEvent", self.customInteractor.rightBtnPress
        )
        self.interactor.AddObserver(
            "LeftButtonPressEvent",
            lambda obj, event: self.customInteractor.leftBtnPress(obj, event, self),
        )
        self.interactor.AddObserver(
            "LeftButtonReleaseEvent", self.customInteractor.leftBtnPress
        )
        self.interactor.AddObserver(
            "MouseMoveEvent",
            lambda obj, event: self.customInteractor.mouseMove(obj, event, self),
        )

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

        legend_color = [192, 192, 192]
        self.legend.SetEntry(0, hackData, "rotate - left mouse button", legend_color)
        self.legend.SetEntry(1, hackData, "move - right mouse button", legend_color)
        self.legend.SetEntry(2, hackData, "scale  - mouse wheel", legend_color)

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
        buttons_layout.addWidget(
            self.print_time_label, get_cur_row(), 2, Qt.AlignmentFlag(3)
        )
        buttons_layout.addWidget(self.print_time_value, get_cur_row(), 3)

        self.model_centering_box = QCheckBox(self.locale.ModelCentering)
        buttons_layout.addWidget(self.model_centering_box, get_next_row(), 1)
        self.consumption_material_label = QLabel(self.locale.ConsumptionMaterial)
        self.consumption_material_value = QLabel("")
        buttons_layout.addWidget(
            self.consumption_material_label, get_cur_row(), 2, Qt.AlignmentFlag(3)
        )
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
        buttons_layout.setColumnMinimumWidth(1, 230)

        self.slice_vip_button = QPushButton(self.locale.SliceVip)
        buttons_layout.addWidget(self.slice_vip_button, get_next_row(), 1, 1, 2)

        self.slice3a_button = QPushButton(self.locale.Slice3Axes)
        buttons_layout.addWidget(self.slice3a_button, get_cur_row(), 3)

        self.setts = SettingsWidget(settings_provider=sett).with_all()

        # check if there is some stuff going on with loaded and missed settings
        logging.debug("Loaded settings after settings widget: %s", sett())

        # and when some of these parameters are null, we are actually better
        # just take their defalts from the bundled settings yaml config
        # this way these mismatched settings will be fixed

        scroll = QScrollArea()
        scroll.setWidget(self.setts)
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

        self.color_model_button = QPushButton(self.locale.ColorModel)
        bottom_layout.addWidget(self.color_model_button, 3, 3)

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
            self,
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
            ],
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

    def change_layer_view(
        self, new_slider_value, prev_value, gcd
    ):  # shows +1 layer to preview finish
        if prev_value is None:
            return new_slider_value

        last = False if len(self.actors) > new_slider_value else True
        prev_last = False if len(self.actors) > prev_value else True

        if not last:
            self.actors[new_slider_value].GetProperty().SetColor(
                get_color(sett().colors.last_layer)
            )
            self.actors[new_slider_value].GetProperty().SetLineWidth(4)
            self.actors[new_slider_value].GetProperty().SetOpacity(
                sett().common.opacity_last_layer
            )
        if not prev_last:
            self.actors[prev_value].GetProperty().SetColor(
                get_color(sett().colors.layer)
            )
            self.actors[prev_value].GetProperty().SetLineWidth(1)
            self.actors[prev_value].GetProperty().SetOpacity(
                sett().common.opacity_layer
            )

        self.layers_number_label.setText(str(new_slider_value))

        if new_slider_value < prev_value:
            for layer in range(
                new_slider_value + 1, prev_value if prev_last else prev_value + 1
            ):
                self.actors[layer].VisibilityOff()
        else:
            for layer in range(
                prev_value, new_slider_value if last else new_slider_value + 1
            ):
                self.actors[layer].VisibilityOn()

        new_rot = gcd.lays2rots[0] if last else gcd.lays2rots[new_slider_value]
        prev_rot = gcd.lays2rots[0] if prev_last else gcd.lays2rots[prev_value]

        if new_rot != prev_rot:
            curr_rotation = gcd.rotations[new_rot]
            for block in range(new_slider_value if last else new_slider_value + 1):
                # revert prev rotation firstly and then apply current
                tf = gui_utils.prepareTransform(
                    gcd.rotations[gcd.lays2rots[block]], curr_rotation
                )
                self.actors[block].SetUserTransform(tf)

            self.rotate_plane(plane_tf(curr_rotation))
            # for i in range(len(self.planes)):
            #     self.rotateAnyPlane(self.planesActors[i], self.planes[i], currRotation)
        return new_slider_value

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if not self.keyPressProcessing(event):
                return super().eventFilter(obj, event)
            return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if not self.keyPressProcessing(event):
            super().keyPressEvent(event)

    def keyPressProcessing(self, event):
        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.save_project_action.trigger()
            return True

        if event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Z:
            self.shift_state()
            return True
        elif event.modifiers() == Qt.ControlModifier and event.key() == Qt.Key_Y:
            self.shift_state(False)
            return True

        return False

    def move_stl2(self):
        if self.move_button.isChecked():
            self.state_moving()

            # self.interactor.SetInteractorStyle(self.actor_interactor_style)

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

                def EndTransform(obj, event):
                    self.save_current_movement()

                self.boxWidget.AddObserver("InteractionEvent", TransformActor)
                self.boxWidget.AddObserver("EndInteractionEvent", EndTransform)
            else:
                self.boxWidget.SetEnabled(True)
            # self.interactor.GetInteractorStyle().SetCurrentStyleToTrackballActor()
        else:
            self.state_stl()  # TODO: might be not stl but both or gcode
            # self.interactor.SetInteractorStyle(self.camera_interactor_style)
            self.boxWidget.SetEnabled(False)
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

    def save_current_movement(self):
        movements = self.stlActor.movements_array
        current_index = self.stlActor.current_movement_index

        movements = [movement for movement in movements if movement[0] <= current_index]

        movement = self.copyTransform(self.stlActor.GetUserTransform())
        movements.append((current_index + 1, movement))

        max_movements = 100
        if len(movements) > max_movements:
            movements.pop(0)

        self.stlActor.movements_array = movements
        self.stlActor.current_movement_index = len(movements) - 1

    # We move on to the nearest state of movement of the model.
    # If cancel=True, go back. If cancel=False, move forward.
    def shift_state(self, cancel=True):
        current_index = self.stlActor.current_movement_index
        movements = self.stlActor.movements_array

        if cancel:
            current_index -= 1
        else:
            current_index += 1

        if (current_index > len(movements) - 1) or (current_index < 0):
            return False

        transform = movements[current_index][1]

        self.stlActor.SetUserTransform(transform)
        if not self.boxWidget is None:
            self.boxWidget.SetTransform(transform)

        self.updateTransform()
        self.reload_scene()

        self.stlActor.current_movement_index = current_index

    def copyTransform(self, transform):
        new_transform = vtk.vtkTransform()
        new_transform.SetMatrix(transform.GetMatrix())
        return new_transform

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

    def save_dialog(
        self,
        caption,
        format="STL (*.stl *.STL);;Gcode (*.gcode)",
        directory="/home/l1va/Downloads/5axes_3d_printer/test",
    ):  # TODO: fix path
        return QFileDialog.getSaveFileName(None, caption, directory, format)[0]

    def open_dialog(
        self,
        caption,
        format="STL (*.stl *.STL);;Gcode (*.gcode)",
        directory="/home/l1va/Downloads/5axes_3d_printer/test",
    ):  # TODO: fix path
        return QFileDialog.getOpenFileName(None, caption, directory, format)[0]

    def load_stl(self, stl_actor):
        self.clear_scene()
        self.boxWidget = None
        self.stlActor = stl_actor
        self.stlActor.movements_array = [
            (0, self.copyTransform(self.stlActor.GetUserTransform()))
        ]
        self.stlActor.current_movement_index = 0
        self.stlActor.addUserTransformUpdateCallback(self.stl_move_panel.update)
        # self.actor_interactor_style.setStlActor(self.stlActor)
        self.updateTransform()

        self.render.AddActor(self.stlActor)
        self.state_stl()
        # self.render.ResetCamera()
        self.render.GetActiveCamera().SetClippingRange(100, 10000)
        self.reload_scene()

    def hide_splanes(self):
        if self.hide_checkbox.isChecked():
            for s in self.splanes_actors:
                s.VisibilityOff()
        else:
            for i, s in enumerate(self.splanes_actors):
                if (
                    not self.splanes_tree.topLevelItem(i).checkState(0)
                    == Qt.CheckState.Checked
                ):
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
            self.splanes_tree.setCurrentItem(
                self.splanes_tree.topLevelItem(len(splanes) - 1)
            )
        self.reload_scene()

    def _recreate_splanes(self, splanes):
        for p in self.splanes_actors:
            self.render.RemoveActor(p)
        self.splanes_actors = []
        for i, p in enumerate(splanes):
            if isinstance(p, Plane):
                act = gui_utils.create_splane_actor([p.x, p.y, p.z], p.incline, p.rot)
            else:  # isinstance(p, Cone):
                act = gui_utils.create_cone_actor(
                    (p.x, p.y, p.z), p.cone_angle, p.h1, p.h2
                )

            row = self.splanes_tree.topLevelItem(i)
            if row != None:
                if (
                    row.checkState(0) == QtCore.Qt.CheckState.Checked
                ) or self.hide_checkbox.isChecked():
                    act.VisibilityOff()
            # act = gui_utils.create_cone_actor((p.x, p.y, p.z), p.cone_angle)
            self.splanes_actors.append(act)
            self.render.AddActor(act)

    def update_splane(self, sp, ind):
        self.reset_colorize()
        settableVisibility = (
            self.splanes_actors[ind].GetVisibility()
            and not self.hide_checkbox.isChecked()
        )
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
            self.splanes_actors[sel].GetProperty().SetColor(
                get_color(sett().colors.last_layer)
            )
            self.splanes_actors[sel].GetProperty().SetOpacity(0.8)
        self.reload_scene()

    def update_cone(self, cone: Cone, ind):
        self.render.RemoveActor(self.splanes_actors[ind])
        # TODO update to pass values as self.splanes_actors[ind], and only then destruct object
        act = gui_utils.create_cone_actor(
            (cone.x, cone.y, cone.z), cone.cone_angle, cone.h1, cone.h2
        )
        self.splanes_actors[ind] = act
        self.render.AddActor(act)
        sel = self.splanes_tree.currentIndex().row()
        if sel == ind:
            self.splanes_actors[sel].GetProperty().SetColor(
                get_color(sett().colors.last_layer)
            )
            self.splanes_actors[sel].GetProperty().SetOpacity(
                sett().common.opacity_current_plane
            )
        self.reload_scene()

    def change_combo_select(self, plane, ind):
        for p in self.splanes_actors:
            p.GetProperty().SetColor(get_color(sett().colors.splane))
            p.GetProperty().SetOpacity(sett().common.opacity_plane)
        self.splanes_actors[ind].GetProperty().SetColor(
            get_color(sett().colors.last_layer)
        )
        self.splanes_actors[ind].GetProperty().SetOpacity(
            sett().common.opacity_current_plane
        )
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

        # self.render.ResetCamera()
        self.reload_scene()

    def rotate_plane(self, tf):
        self.planeActor.SetUserTransform(tf)
        self.planeTransform = tf

        # i, j, k = tf.GetOrientation()
        # print("Orientation: " + strF(i) + " " + strF(j) + " " + strF(k))
        # self.xyz_orient_value.setText("Orientation: " + strF(i) + " " + strF(j) + " " + strF(k))

    def save_gcode_dialog(self):
        return QFileDialog.getSaveFileName(
            None, self.locale.SaveGCode, "", "Gcode (*.gcode)"
        )[0]

    def about_dialog(self):
        d = QDialog()
        d.setWindowTitle("About Epit3d")
        d.setWindowModality(Qt.ApplicationModal)
        d.setMinimumSize(250, 200)

        v_layout = QVBoxLayout()

        site_label = QLabel('Site Url: <a href="https://www.epit3d.ru/">epit3d.ru</a>')
        site_label.setOpenExternalLinks(True)
        # site_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v_layout.addWidget(site_label)

        phone_label = QLabel("Phone: +7 (960) 086-11-97")
        phone_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        v_layout.addWidget(phone_label)

        email_label = QLabel(
            "E-mail: <a href='mailto:Info@epit3d.ru?subject=FASP Question&body=My question is ...'>Info@epit3d.ru</a>"
        )
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
        self.cancel_action.setEnabled(False)
        self.return_action.setEnabled(False)
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
        self.cancel_action.setEnabled(False)
        self.return_action.setEnabled(False)
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
        self.cancel_action.setEnabled(True)
        self.return_action.setEnabled(True)
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
        self.place_button.setEnabled(False)
        self.load_model_button.setEnabled(False)
        self.slice3a_button.setEnabled(False)
        self.color_model_button.setEnabled(False)
        self.slice_vip_button.setEnabled(False)
        self.save_gcode_button.setEnabled(False)
        # self.hide_checkbox.setChecked(False)
        self.bottom_panel.setEnabled(False)
        self.stl_move_panel.setEnabled(True)
        self.cancel_action.setEnabled(True)
        self.return_action.setEnabled(True)
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
        self.place_button.setEnabled(False)
        self.load_model_button.setEnabled(True)
        self.slice3a_button.setEnabled(True)
        self.color_model_button.setEnabled(True)
        self.slice_vip_button.setEnabled(True)
        self.save_gcode_button.setEnabled(True)
        self.hide_checkbox.setChecked(True)
        self.bottom_panel.setEnabled(True)
        self.stl_move_panel.setEnabled(False)
        self.cancel_action.setEnabled(True)
        self.return_action.setEnabled(True)
        self.state = BothState

    def reset_colorize(self):
        if self.stlActor:
            self.stlActor.ResetColorize()


def strF(v):  # cut 3 numbers after the point in float
    s = str(v)
    i = s.find(".")
    if i != -1:
        s = s[: min(len(s), i + 3)]
    return s
