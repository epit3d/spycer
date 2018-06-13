import sys

from PyQt5.QtWidgets import QApplication

from gui import Gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Gui()
    window.prepareWidgets()
    window.show()
    # window.loadGCode("/home/l1va/out_home.gcode", True)
    sys.exit(app.exec_())
