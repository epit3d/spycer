"""
Provides a class creating a new window to edit parameters of custom figures
"""

import logging
import sys
from typing import List, Callable, Dict, Tuple, Optional, Union
from functools import partial

from PyQt5 import QtCore, sip
from PyQt5.QtWidgets import (
    QSlider,
    QLineEdit,
    QApplication,
    QGridLayout,
    QWidget,
    QLabel,
    QSizePolicy,
    QPushButton,
    QHBoxLayout,
    QCheckBox,
    QScrollArea,
    QVBoxLayout,
    QComboBox,
    QStyle,
)
from src.settings_widget import SettingsWidget
from src.settings import sett
from src.locales import getLocale

logger = logging.getLogger(__name__)


class FigureEditor(QWidget):
    """
    FigureEditor class creates a new qt window which would have QSlider and QLineEdit for each passed parameter,
    and on each change of any of parameters `onChange` is invoked with changed values of parameters
    """

    _checkboxes = []

    def __init__(
        self,
        tabs,
        params: List[str],
        constrains: List[Tuple[int, int]],
        on_change: Callable[[Dict[str, float]], None] = None,
        initial_params: Optional[Dict[str, float]] = None,
        settings_provider: callable = None,
        figure_index=0,
    ):
        super().__init__()
        self.on_change = on_change
        self.setWindowTitle("Parameters tooling")

        self.__layout = QHBoxLayout()

        self.__figure_params_layout = QGridLayout()
        self.__figure_params_layout.setSpacing(5)
        # self.layout.setColumnStretch(7, 1)

        self.params_widgets = []
        # TODO add implementation of True/False parameters
        self.params_dict: Dict[str, float] = {
            el: initial_params.get(el, 0) if initial_params else 0
            for el in params + self._checkboxes
        }

        for param_idx, param in enumerate(params):
            # add label for parameter name
            label = QLabel(str(param))
            self.params_widgets.append(label)
            self.__figure_params_layout.addWidget(label, param_idx, 0)

            def pass_updated_value_edit(
                param_name: str, qslider: QSlider, qlineedit: QLineEdit
            ):
                # return a function to be called from QLineEdit callback
                def emmit_value(state: str):
                    try:
                        value = float(state)
                    except ValueError:
                        value = 0

                    for param_idx, param in enumerate(params):
                        if str(param) == param_name:
                            break

                    minimumValue = constrains[param_idx][0]
                    maximumValue = constrains[param_idx][1]

                    if value < minimumValue:
                        value = minimumValue
                        qlineedit.setText(str(int(value)))  # TODO: use validator

                    elif value > maximumValue:
                        value = maximumValue
                        qlineedit.setText(str(int(value)))  # TODO: use validator

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
            self.__figure_params_layout.addWidget(edit, param_idx, 1)
            # we should disable slider for the first figure
            edit.setReadOnly(figure_index == 0)

            # add a slider for parameter
            slider = QSlider()
            slider.setOrientation(QtCore.Qt.Horizontal)
            slider.setMinimum(constrains[param_idx][0])
            slider.setMaximum(constrains[param_idx][1])
            # slider is int, ensure that it will not get float
            slider.setValue(int(initial_params.get(param, 0)))
            slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            slider.setMinimumWidth(200)
            # we should disable slider for the first figure
            slider.setEnabled(figure_index != 0)

            self.params_widgets.append(slider)
            self.__figure_params_layout.addWidget(slider, param_idx, 2)

            slider.valueChanged.connect(pass_updated_value_slider(param, edit))
            edit.textChanged.connect(pass_updated_value_edit(param, slider, edit))

        for param in self._checkboxes:
            param_idx += 1

            checkbox = QCheckBox(param, self)
            checkbox.setChecked(initial_params.get(param, False))

            self.params_widgets.append(checkbox)
            self.__figure_params_layout.addWidget(checkbox, param_idx, 0)

            checkbox.stateChanged.connect(self.pass_updated_value_checkbox(param))

            help_image = getattr(self, "_checkbox_help", {}).get(param)
            if help_image:
                help_label = QLabel("?")
                help_label.setToolTip(
                    f"<img src='{help_image}'><br>{getLocale().SmoothConeUpwardTooltip}"
                )
                help_label.setStyleSheet("QLabel { color : blue; font-weight: bold; }")
                self.__figure_params_layout.addWidget(help_label, param_idx, 1)

        self.__figure_params_widget = QWidget()
        self.__figure_params_widget.setLayout(self.__figure_params_layout)
        self.__layout.addWidget(self.__figure_params_widget)

        # part regarding additional settings per figure
        self.__additional_settings_widget = (
            SettingsWidget(settings_provider=settings_provider, use_grouping=False)
            .from_settings(settings_provider())
            .with_delete()
        )

        self.__scroll = QScrollArea()
        self.__scroll.setWidget(self.__additional_settings_widget)
        self.__scroll.setWidgetResizable(True)

        # widget with vertical layout:
        # element to add settings to layout
        # settings widget
        self.__right_widget = QWidget()
        self.__right_layout = QVBoxLayout()

        self.__add_settings_widget = QWidget()
        self.__add_settings_layout = QHBoxLayout()

        # add combobox to choose settings
        self.__add_settings_combobox = QComboBox()
        self.__combobox_values = []
        for param in self.__additional_settings_widget.extra_sett_parameters:
            self.__combobox_values.append(param)
            self.__add_settings_combobox.addItem(
                self.__additional_settings_widget.translation[param]
            )
        self.__add_settings_layout.addWidget(self.__add_settings_combobox)

        # add button which adds selected setting to layout
        self.__add_settings_button = QPushButton()
        self.__add_settings_button.setIcon(
            self.style().standardIcon(QStyle.SP_DialogApplyButton)
        )
        self.__add_settings_layout.addWidget(self.__add_settings_button)

        def add_sett():
            self.__additional_settings_widget.with_sett(
                self.__combobox_values[self.__add_settings_combobox.currentIndex()]
            ).with_delete()

        self.__add_settings_button.clicked.connect(add_sett)

        self.__add_settings_widget.setLayout(self.__add_settings_layout)

        self.__right_layout.addWidget(self.__add_settings_widget)
        self.__right_layout.addWidget(self.__scroll)
        self.__right_widget.setLayout(self.__right_layout)

        self.__layout.addWidget(self.__right_widget)

        if tabs.widget(1).layout() is not None:
            self.deleteLayout(tabs.widget(1).layout())
        tabs.widget(1).setLayout(self.__layout)

    def pass_updated_value_checkbox(self, param_name: str):
        # return a function to be called from QCheckBox callback
        def emmit_value(state: int):
            self.params_dict[param_name] = state == QtCore.Qt.Checked

            # pass to function accepting parameters, if exists
            if self.on_change:
                self.on_change(self.params_dict)

        return emmit_value

    def deleteLayout(self, cur_lay):
        if cur_lay is not None:
            while cur_lay.count():
                item = cur_lay.takeAt(0)
                widget = item.widget()
                if widget is not None:
                    widget.deleteLater()
                else:
                    self.deleteLayout(item.layout())

            sip.delete(cur_lay)


class PlaneEditor(FigureEditor):
    __params = ["X", "Y", "Z", "Rotation", "Tilt"]
    __constrains = [(-100, 100), (-100, 100), (0, 200), (-180, 180), (-90, 0)]
    _checkboxes = ["Smooth"]

    def __init__(
        self,
        tabs,
        on_change: Callable[[Dict[str, float]], None],
        initial_params: Optional[Dict[str, Union[float, bool]]] = None,
        **kwargs,
    ):
        super().__init__(
            tabs, self.__params, self.__constrains, on_change, initial_params, **kwargs
        )

    def params(self):
        return self.__params


class ConeEditor(FigureEditor):
    __params = ["Z", "A", "H1", "H2"]
    __constrains = [(-100, 200), (-80, 80), (0, 150), (1, 150)]
    _checkboxes = ["Smooth", "SmoothConeUpward"]
    _checkbox_help = {"SmoothConeUpward": "icons/smooth_cone.jpg"}

    def __init__(
        self,
        tabs,
        on_change: Callable[[Dict[str, float]], None],
        initial_params: Optional[Dict[str, float]] = None,
        **kwargs,
    ):
        super().__init__(
            tabs, self.__params, self.__constrains, on_change, initial_params, **kwargs
        )

    def params(self):
        return self.__params


class StlMovePanel(QWidget):
    def __init__(self, viev, methods, captions):
        super().__init__()

        self.setEnabled(False)

        self.edits = {}

        mainLayout = QHBoxLayout()
        for col, caption in enumerate(captions):
            gridLayout = QGridLayout()
            gridLayout.setSpacing(5)

            label = QLabel(caption)
            label.setAlignment(QtCore.Qt.AlignCenter)
            gridLayout.addWidget(label, 0, 0, 1, 3)
            for row, param in enumerate(["X", "Y", "Z"], start=1):
                btn_pos = QPushButton(str(param) + "+")
                gridLayout.addWidget(btn_pos, row, 0)

                btn_neg = QPushButton(str(param) + "-")
                gridLayout.addWidget(btn_neg, row, 1)

                edit = QLineEdit()
                edit.installEventFilter(viev)
                edit.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
                edit.setMinimumWidth(20)
                gridLayout.addWidget(edit, row, 2)

                self.edits[col, param] = edit
                if methods[col, param] is None:
                    continue
                act_pos, act_neg, act_set = methods[col, param]
                btn_pos.clicked.connect(act_pos)
                btn_neg.clicked.connect(act_neg)
                if col == 1:
                    edit.textChanged.connect(act_set)
                else:
                    edit.editingFinished.connect(partial(act_set, edit))

            mainLayout.addLayout(gridLayout)

        initial_pos = [0, 0, 0]
        initial_orient = [0, 0, 0]
        initial_scale = [1, 1, 1]

        self.update(initial_pos, initial_orient, initial_scale)
        self.setLayout(mainLayout)

    def update(self, pos, orient, scale):
        for col, data in enumerate([pos, orient, scale]):
            for param, val in zip(["X", "Y", "Z"], data):
                if col == 2:
                    val = val * 100
                edit = self.edits[col, param]
                if edit.hasFocus():
                    continue

                edit.blockSignals(True)
                edit.setText("{:.3f}".format(val))
                edit.blockSignals(False)


if __name__ == "__main__":

    def handle1(d):
        logger.debug("handler1 %s", d)

    def handle2(d):
        logger.debug("handler2 %s", d)

    app = QApplication(sys.argv)
    f1 = PlaneEditor(handle1, None)
    f2 = PlaneEditor(handle2, None)

    f1.show()
    f2.show()

    sys.exit(app.exec_())
