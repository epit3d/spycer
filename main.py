import sys

from PyQt5.QtWidgets import QApplication

from src.settings import load_settings, sett, get_color
from src.window import MainWindow
from src.model import MainModel
from src.controller import MainController

if __name__ == "__main__":
    load_settings()

    app = QApplication(sys.argv)
    window = MainWindow()
    model = MainModel()
    cntrl = MainController(window, model)
    #cntrl.load_stl("/home/l1va/Downloads/1_odn2.stl")  # TODO: removeme
    window.showMaximized()
    window.show()
    try:
        sys.exit(app.exec_())
    except:
        print("Error:", sys.exc_info())
        with open("err.txt", "a+") as file1:
            file1.write(str(sys.exc_info()))
