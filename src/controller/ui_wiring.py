"""UI signal wiring for controllers."""

from functools import partial

from src import locales
from src.gui_utils import showInfoDialog


def connect_signals(controller):
    view = controller.view
    view.open_action.triggered.connect(controller.open_file)
    view.save_gcode_action.triggered.connect(partial(controller.save_gcode_file))
    view.save_sett_action.triggered.connect(controller.save_settings_file)
    view.save_project_action.triggered.connect(controller.save_project)
    view.save_project_as_action.triggered.connect(controller.save_project_as)
    view.load_sett_action.triggered.connect(controller.load_settings_file)
    view.slicing_info_action.triggered.connect(controller.get_slicer_version)
    view.documentation_action.triggered.connect(controller.show_online_documentation)
    view.check_updates_action.triggered.connect(controller.open_updater)

    if controller.calibrationPanel is not None:
        view.calibration_action.triggered.connect(controller.calibration_action_show)
    else:
        view.calibration_action.triggered.connect(
            lambda: showInfoDialog(locales.getLocale().ErrorHardwareModule)
        )

    try:
        view.bug_report.triggered.connect(controller.bugReportDialog.show)
    except Exception:
        view.bug_report.triggered.connect(
            lambda: showInfoDialog(locales.getLocale().ErrorBugModule)
        )

    view.setts.get_element("printer_path", "add_btn").clicked.connect(
        controller.create_printer
    )
    view.setts.edit("printer_path").clicked.connect(controller.choose_printer_path)
    view.model_switch_box.stateChanged.connect(view.switch_stl_gcode)
    view.model_centering_box.stateChanged.connect(view.model_centering)
    view.picture_slider.valueChanged.connect(controller.change_layer_view)
    view.move_button.clicked.connect(controller.move_model)
    view.place_button.clicked.connect(controller.place_model)
    view.cancel_action.clicked.connect(partial(view.shift_state, True))
    view.return_action.clicked.connect(partial(view.shift_state, False))
    view.load_model_button.clicked.connect(controller.open_file)
    view.slice3a_button.clicked.connect(partial(controller.slice_stl, "3axes"))
    view.slice_vip_button.clicked.connect(partial(controller.slice_stl, "vip"))
    view.save_gcode_button.clicked.connect(controller.save_gcode_file)
    view.color_model_button.clicked.connect(controller.colorize_model)

    view.add_plane_button.clicked.connect(controller.add_splane)
    view.add_cone_button.clicked.connect(controller.add_cone)
    view.edit_figure_button.clicked.connect(controller.change_figure_parameters)
    view.save_planes_button.clicked.connect(controller.save_planes)
    view.download_planes_button.clicked.connect(controller.download_planes)
    view.remove_plane_button.clicked.connect(controller.remove_splane)
    view.splanes_tree.itemClicked.connect(controller.change_splanes_tree)
    view.splanes_tree.itemChanged.connect(controller.change_figure_check_state)
    view.splanes_tree.currentItemChanged.connect(controller.change_combo_select)
    view.splanes_tree.model().rowsInserted.connect(controller.moving_figure)

    view.hide_checkbox.stateChanged.connect(view.hide_splanes)
    view.before_closing_signal.connect(controller.save_planes_on_close)
    view.save_project_signal.connect(controller.save_project)
