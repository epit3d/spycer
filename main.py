import logging
import sys
import traceback
import os
import qdarkstyle
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from src.settings import load_settings, sett, get_color
from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController
from src.interface_style_sheet import getStyleSheet

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

    lineedit_style_sheet = getStyleSheet()
    app.setStyleSheet(lineedit_style_sheet)

    window = MainWindow()
    model = MainModel()
    cntrl = MainController(window, model)
    # cntrl.load_stl("/home/l1va/Downloads/1_odn2.stl")  # TODO: removeme
    window.showMaximized()
    window.show()

    # sys.exit(app.exec_())
    sys.excepthook = excepthook
    ret = app.exec_()
    print("event loop exited")

    s = sett()
    if os.path.isfile(s.colorizer.copy_stl_file):
        os.remove(s.colorizer.copy_stl_file)

    sys.exit(ret)
