# if we run pyinstaller build for linux, we have to extend LD_LIBRARY_PATH with goosli dependencies
import os, sys

# check whether we are in pyinstaller bundle and on linux
if getattr(sys, "frozen", False) and sys.platform.startswith("linux"):
    app_path = os.path.dirname(sys.executable)

    prev_ld_path = os.environ.get("LD_LIBRARY_PATH", "")

    # shared libraries are located at lib/
    shared_libs = os.path.join(app_path, "lib")

    # add shared libraries to LD_LIBRARY_PATH
    os.environ["LD_LIBRARY_PATH"] = shared_libs + ":" + prev_ld_path
    print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])


import logging
import sys
import traceback
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
import pathlib
from src.settings import (
    copy_project_files,
    load_settings,
    sett,
    create_temporary_project_files,
)
from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController
from src.interface_style_sheet import getStyleSheet
from src.entry_window import EntryWindow
from src.gui_utils import read_plane

logging.basicConfig(
    filename="interface.log",
    filemode="a+",
    level=logging.INFO,
    format="%(asctime)s %(message)s",
)


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    logging.error(tb)
    QtWidgets.QApplication.quit()


if __name__ == "__main__":
    load_settings()

    app = QApplication(sys.argv)

    style_sheet = getStyleSheet()
    app.setStyleSheet(style_sheet)

    def open_project(project_path: str):
        load_settings(str(pathlib.Path(project_path, "settings.yaml")))

        # update project_path in settings, because it originally might be in another place
        sett().project_path = project_path
        create_temporary_project_files()

        window = MainWindow()
        window.close_signal.connect(entry_window.show)

        model = MainModel()
        cntrl = MainController(window, model)

        # try to open stl file
        stlpath = pathlib.Path(project_path, sett().slicing.stl_file)
        if os.path.isfile(stlpath):
            cntrl.load_stl(stlpath)

        if hasattr(sett().slicing, "splanes_file"):
            # we have kinda old settings which point to separate file with planes
            # load planes as it is, but remove this parameter and save settings
            # TODO: we can remove this condition after one release

            # try to open figures file
            figpath = pathlib.Path(project_path, sett().slicing.splanes_file)
            if os.path.isfile(figpath):
                cntrl.load_planes_from_file(figpath)

            del sett().slicing.splanes_file

            cntrl.save_settings("vip")
        else:
            # load splanes from settings
            cntrl.load_planes(
                [read_plane(figure.description) for figure in sett().figures]
            )

        window.showMaximized()
        window.show()
        cntrl.reset_settings()
        cntrl.update_interface(sett().slicing.stl_filename)
        entry_window.close()

    def create_project(project_path: str):
        copy_project_files(project_path)
        load_settings(str(pathlib.Path(project_path, "settings.yaml")))
        create_temporary_project_files()

        window = MainWindow()
        window.close_signal.connect(entry_window.show)

        model = MainModel()
        cntrl = MainController(window, model)
        window.showMaximized()
        window.show()
        entry_window.close()

    entry_window = EntryWindow()
    entry_window.show()

    entry_window.open_project_signal.connect(open_project)
    entry_window.create_project_signal.connect(create_project)

    # sys.exit(app.exec_())
    sys.excepthook = excepthook
    ret = app.exec_()
    print("event loop exited")

    s = sett()
    if os.path.isfile(s.colorizer.copy_stl_file):
        os.remove(s.colorizer.copy_stl_file)

    sys.exit(ret)
