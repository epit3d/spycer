import sys
import traceback
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QApplication

from src.settings import load_settings, sett, get_color
from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    with open("err.txt", "a+") as file1:
        file1.write(tb + "\n")
    QtWidgets.QApplication.quit()


if __name__ == "__main__":
    load_settings()

    app = QApplication(sys.argv)
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
    sys.exit(ret)
