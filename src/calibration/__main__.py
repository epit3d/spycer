import sys
import traceback
from PyQt5.QtWidgets import QApplication
from calibration import (
    CalibrationPanel, CalibrationController, CalibrationModel
)


def excepthook(exc_type, exc_value, exc_tb):
    tb = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
    print("error catched!:")
    print("error message:\n", tb)
    # QApplication.quit()


app = QApplication(sys.argv)
view = CalibrationPanel()
model = CalibrationModel()
controller = CalibrationController(view, model)
view.show()

sys.excepthook = excepthook
sys.exit(app.exec_())
