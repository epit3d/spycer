import sys

from PyQt5.QtWidgets import QApplication

from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    model = MainModel()
    cntrl = MainController(window, model)

    window.showMaximized()
    window.show()

    sys.exit(app.exec_())
