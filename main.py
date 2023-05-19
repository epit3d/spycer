import logging
import sys
import traceback
import os
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication
import pathlib
from src.settings import copy_project_files, load_settings, sett, get_color
from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController
from src.interface_style_sheet import getStyleSheet
from src.entry_window import EntryWindow

logging.basicConfig(filename='interface.log', filemode='a+', level=logging.INFO, format='%(asctime)s %(message)s')


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

        window = MainWindow()
        window.close_signal.connect(entry_window.show)
        
        model = MainModel()
        cntrl = MainController(window, model)

        # try to open stl file
        stlpath = pathlib.Path(project_path, sett().slicing.stl_file)
        if os.path.isfile(stlpath):
            cntrl.load_stl(stlpath)

        # try to open figures file
        figpath = pathlib.Path(project_path, sett().slicing.splanes_file)
        if os.path.isfile(figpath):
            cntrl.load_planes(figpath)

        window.showMaximized()
        window.show()
        entry_window.close()

    def create_project(project_path: str):
        copy_project_files(project_path)
        load_settings(str(pathlib.Path(project_path, "settings.yaml")))

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
