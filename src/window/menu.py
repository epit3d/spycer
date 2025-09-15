"""Menu helpers for :mod:`src.window`."""

from PyQt5.QtWidgets import QAction


def setup_menus(window):
    """Populate application menus and actions for ``window``.

    Parameters
    ----------
    window:
        Instance of :class:`~PyQt5.QtWidgets.QMainWindow` to populate.
    """
    locale = window.locale
    bar = window.menuBar()

    file_menu = bar.addMenu(locale.File)
    window.open_action = QAction(locale.Open, window)
    file_menu.addAction(window.open_action)

    window.save_gcode_action = QAction(locale.SaveGCode, window)
    window.save_project_action = QAction(locale.SaveProject, window)
    file_menu.addAction(window.save_project_action)
    window.save_project_as_action = QAction(locale.SaveProjectAs, window)
    file_menu.addAction(window.save_project_as_action)
    file_menu.addAction(window.save_gcode_action)
    window.save_sett_action = QAction(locale.SaveSettings, window)
    file_menu.addAction(window.save_sett_action)
    window.load_sett_action = QAction(locale.LoadSettings, window)
    file_menu.addAction(window.load_sett_action)

    window.slicing_info_action = QAction(locale.SlicerInfo, window)
    file_menu.addAction(window.slicing_info_action)

    tools_menu = bar.addMenu(locale.Tools)
    window.calibration_action = QAction(locale.Calibration, window)
    tools_menu.addAction(window.calibration_action)
    window.bug_report = QAction(locale.SubmitBugReport, window)
    tools_menu.addAction(window.bug_report)

    window.check_updates_action = QAction(locale.CheckUpdates, window)
    tools_menu.addAction(window.check_updates_action)

    help_menu = bar.addMenu(locale.Help)
    window.slicing_info_action = QAction(locale.SlicerInfo, window)
    help_menu.addAction(window.slicing_info_action)

    window.documentation_action = QAction(locale.Documentation, window)
    help_menu.addAction(window.documentation_action)
