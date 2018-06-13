import sys

from PyQt5.QtWidgets import (QWidget, QLabel, QLineEdit,
                             QTextEdit, QGridLayout, QSlider, QCheckBox, QPushButton,
                             QApplication, QFileDialog)

from gui import Gui

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = Gui()
    window.prepareWidgets()
    window.show()
    window.loadGCode( "/home/l1va/out_home.gcode")
    # window.loadGCode()
    # window.iren.Render()
    # window.stlFileName = ""
    sys.exit(app.exec_())
