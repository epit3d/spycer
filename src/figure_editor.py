"""
Provides a class creating a new window to edit parameters of custom figures
"""
import sys
from typing import List, Callable, Dict, Tuple, Optional

from PyQt5 import QtCore
from PyQt5.QtWidgets import QSlider, QLineEdit, QApplication, QGridLayout, QWidget, QLabel, QSizePolicy, QPushButton, QHBoxLayout


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
        # TODO add implementation of True/False parameters
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
    __params = ["Z", "A", "H"]
    __constrains = [(-100, 200), (-60, 60), (15, 150)]

    def __init__(self, on_change: Callable[[Dict[str, float]], None],
                 initial_params: Optional[Dict[str, float]] = None):
        super().__init__(self.__params, self.__constrains, on_change, initial_params)

    def params(self):
        return self.__params
    
class StlMovePanel(QWidget):
    def __init__(self, methods, captions):
        super().__init__()
        #intended to avoid panel updating when actor moved by inserting value in QlineEdit
        self.setEnabled(False)
        
        self.edits = {}
        
        mainLayout = QHBoxLayout()
        for col, caption in enumerate(captions):
            gridLayout = QGridLayout()
            gridLayout.setSpacing(2)
            
            label = QLabel(caption)
            label.setAlignment(QtCore.Qt.AlignCenter)
            gridLayout.addWidget(label, 0, 0, 1, 3)
            for row, param in enumerate(["X", "Y", "Z"], start=1):
                btn_pos = QPushButton(str(param) + '+')
                gridLayout.addWidget(btn_pos, row, 0)
                
                btn_neg = QPushButton(str(param) + '-')
                gridLayout.addWidget(btn_neg, row, 1)
                
                edit = QLineEdit()
                edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
                edit.setMinimumWidth(20)
                gridLayout.addWidget(edit, row, 2)
                
                self.edits[col, param] = edit
                if methods[col, param] is None:
                    continue
                act_pos, act_neg, act_set = methods[col, param]
                btn_pos.clicked.connect(act_pos)
                btn_neg.clicked.connect(act_neg)
                edit.textChanged.connect(act_set)
                
            mainLayout.addLayout(gridLayout)
            
        initial_pos = [0, 0, 0]
        initial_orient = [0, 0, 0]
        initial_sacle = [1, 1, 1]

        self.update(initial_pos, initial_orient, initial_sacle)
        self.setLayout(mainLayout)
        
    def update(self, pos, orient, sacale):
        for col, data in enumerate([pos, orient, sacale]):
            for param, val in zip(["X", "Y", "Z"], data):
                edit = self.edits[col, param]
                if edit.hasFocus():
                    continue
                
                edit.blockSignals(True)
                edit.setText("{:.3f}".format(val))
                edit.blockSignals(False)


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
