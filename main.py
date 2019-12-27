import sys

from PyQt5.QtWidgets import QApplication

from src.gui import Gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Gui()
    window.showMaximized()
    window.prepareWidgets()
    window.show()
    sys.exit(app.exec_())
