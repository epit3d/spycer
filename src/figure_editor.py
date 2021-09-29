"""
Provides a class creating a new window to edit parameters of custom figures
"""
import sys
from typing import List, Callable, Dict, Tuple, Optional

from PyQt5 import QtCore
from PyQt5.QtWidgets import QSlider, QLineEdit, QApplication, QGridLayout, QWidget, QLabel, QSizePolicy


class FigureEditor(QWidget):
    """
    FigureEditor class creates a new qt window which would have QSlider and QLineEdit for each passed parameter,
    and on each change of any of parameters `onChange` is invoked with changed values of parameters
    """

    def __init__(self, params: List[str], constrains: List[Tuple[int, int]],
                 on_change: Callable[[Dict[str, float]], None] = None,
                 initial_params: Optional[Dict[str, float]] = None):
        super().__init__()
        self.setWindowTitle("Parameters tooling")

        self.layout = QGridLayout()
        self.layout.setSpacing(5)
        # self.layout.setColumnStretch(7, 1)

        self.params_widgets = []
        self.params_dict: Dict[str, float] = dict(
            (el, initial_params[el] if initial_params and initial_params[el] else 0) for el in params)

        for param_idx, param in enumerate(params):
            # add label for parameter name
            label = QLabel(str(param))
            self.params_widgets.append(label)
            self.layout.addWidget(label, param_idx, 0)

            def pass_updated_value_edit(param_name: str, qslider: QSlider):
                # return a function to be called from QLineEdit callback
                def emmit_value(state: str):
                    try:
                        value = float(state)
                    except ValueError:
                        value = 0
                    self.params_dict[param_name] = float(value)

                    # pass to function accepting parameters, if exists
                    if on_change:
                        on_change(self.params_dict)
                    # update QSlider
                    qslider.setValue(int(value))

                return emmit_value

            def pass_updated_value_slider(param_name: str, qlineedit: QLineEdit):
                # return a function to be called from QSlider callback
                def emmit_value(state: int):
                    self.params_dict[param_name] = float(state)

                    # pass to function accepting parameters, if exists
                    if on_change:
                        on_change(self.params_dict)
                    # update QLineEdit
                    qlineedit.setText(str(state))

                return emmit_value

            # add an edit of values
            edit = QLineEdit(str(initial_params.get(param, 0)))
            edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
            edit.setMinimumWidth(40)
            self.params_widgets.append(edit)
            self.layout.addWidget(edit, param_idx, 1)

            # add a slider for parameter
            slider = QSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMinimum(constrains[param_idx][0])
            slider.setMaximum(constrains[param_idx][1])
            slider.setValue((initial_params.get(param, 0)))
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setMinimumWidth(200)

            self.params_widgets.append(slider)
            self.layout.addWidget(slider, param_idx, 2)

            slider.valueChanged.connect(pass_updated_value_slider(param, edit))
            edit.textChanged.connect(pass_updated_value_edit(param, slider))
            self.setLayout(self.layout)


class PlaneEditor(FigureEditor):
    __params = ["X", "Y", "Z", "Rotation", "Tilt"]
    __constrains = [(-100, 100), (-100, 100), (0, 200), (-180, 180), (-60, 0)]

    def __init__(self, on_change: Callable[[Dict[str, float]], None],
                 initial_params: Optional[Dict[str, float]] = None):
        super().__init__(self.__params, self.__constrains, on_change, initial_params)

    def params(self):
        return self.__params


class ConeEditor(FigureEditor):
    __params = ["X", "Y", "Z", "A"]
    __constrains = [(-100, 100), (-100, 100), (0, 200), (0, 89)]

    def __init__(self, on_change: Callable[[Dict[str, float]], None],
                 initial_params: Optional[Dict[str, float]] = None):
        super().__init__(self.__params, self.__constrains, on_change, initial_params)

    def params(self):
        return self.__params


if __name__ == "__main__":
    def handle1(d):
        print(1, d)


    def handle2(d):
        print(2, d)


    app = QApplication(sys.argv)
    f1 = PlaneEditor(handle1, None)
    f2 = PlaneEditor(handle2, None)

    f1.show()
    f2.show()

    sys.exit(app.exec_())
