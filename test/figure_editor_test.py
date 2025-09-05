import sys
import types
import unittest

# --- Begin stubs for PyQt5 and related modules ---


class Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, func):
        self._callbacks.append(func)


class QStyle:
    SP_DialogApplyButton = 0

    def standardIcon(self, *args, **kwargs):
        return None


class QWidget:
    def __init__(self, *args, **kwargs):
        pass

    def setLayout(self, *args, **kwargs):
        pass

    def style(self):
        return QStyle()

    def setWindowTitle(self, *args, **kwargs):
        pass


class QGridLayout:
    def __init__(self, *args, **kwargs):
        pass

    def setSpacing(self, *args, **kwargs):
        pass

    def addWidget(self, *args, **kwargs):
        pass


class QHBoxLayout:
    def __init__(self, *args, **kwargs):
        pass

    def addWidget(self, *args, **kwargs):
        pass

    def addLayout(self, *args, **kwargs):
        pass


class QVBoxLayout:
    def __init__(self, *args, **kwargs):
        pass

    def addWidget(self, *args, **kwargs):
        pass

    def addLayout(self, *args, **kwargs):
        pass


class QLabel(QWidget):
    def __init__(self, *args, **kwargs):
        pass


class QLineEdit(QWidget):
    def __init__(self, text=""):
        self._text = text
        self.textChanged = Signal()

    def setSizePolicy(self, *args, **kwargs):
        pass

    def setMinimumWidth(self, *args, **kwargs):
        pass

    def setReadOnly(self, *args, **kwargs):
        pass

    def setText(self, text):
        self._text = text


class QSlider(QWidget):
    def __init__(self, *args, **kwargs):
        self.valueChanged = Signal()

    def setOrientation(self, *args, **kwargs):
        pass

    def setMinimum(self, *args, **kwargs):
        pass

    def setMaximum(self, *args, **kwargs):
        pass

    def setValue(self, *args, **kwargs):
        pass

    def setSizePolicy(self, *args, **kwargs):
        pass

    def setMinimumWidth(self, *args, **kwargs):
        pass

    def setEnabled(self, *args, **kwargs):
        pass


class QSizePolicy:
    Minimum = 0
    Fixed = 0
    Expanding = 0


class QPushButton(QWidget):
    def __init__(self, *args, **kwargs):
        self.clicked = Signal()

    def setIcon(self, *args, **kwargs):
        pass


class QCheckBox(QWidget):
    def __init__(self, *args, **kwargs):
        self.stateChanged = Signal()

    def setChecked(self, *args, **kwargs):
        pass


class QScrollArea(QWidget):
    def setWidget(self, *args, **kwargs):
        pass

    def setWidgetResizable(self, *args, **kwargs):
        pass


class QComboBox(QWidget):
    def addItem(self, *args, **kwargs):
        pass


class QApplication:
    def __init__(self, *args, **kwargs):
        pass


qtwidgets = types.ModuleType("PyQt5.QtWidgets")
qtwidgets.QSlider = QSlider
qtwidgets.QLineEdit = QLineEdit
qtwidgets.QApplication = QApplication
qtwidgets.QGridLayout = QGridLayout
qtwidgets.QWidget = QWidget
qtwidgets.QLabel = QLabel
qtwidgets.QSizePolicy = QSizePolicy
qtwidgets.QPushButton = QPushButton
qtwidgets.QHBoxLayout = QHBoxLayout
qtwidgets.QCheckBox = QCheckBox
qtwidgets.QScrollArea = QScrollArea
qtwidgets.QVBoxLayout = QVBoxLayout
qtwidgets.QComboBox = QComboBox
qtwidgets.QStyle = QStyle
sys.modules["PyQt5.QtWidgets"] = qtwidgets

qtcore = types.ModuleType("PyQt5.QtCore")
qtcore.Qt = types.SimpleNamespace(Horizontal=1, Checked=True)
sys.modules["PyQt5.QtCore"] = qtcore

sip = types.ModuleType("sip")
sip.isdeleted = lambda obj: False
pyqt5 = types.ModuleType("PyQt5")
pyqt5.QtCore = qtcore
pyqt5.sip = sip
sys.modules["PyQt5"] = pyqt5
sys.modules["sip"] = sip

# Stub out project-specific modules that depend on PyQt5
settings_widget_module = types.ModuleType("src.settings_widget")


class SettingsWidget:
    def __init__(self, *args, **kwargs):
        self.extra_sett_parameters = []
        self.translation = {}

    def from_settings(self, *args, **kwargs):
        return self

    def with_delete(self, *args, **kwargs):
        return self

    def with_sett(self, *args, **kwargs):
        return self


settings_widget_module.SettingsWidget = SettingsWidget
sys.modules["src.settings_widget"] = settings_widget_module

settings_module = types.ModuleType("src.settings")


def sett():
    return None


settings_module.sett = sett
sys.modules["src.settings"] = settings_module

locales_module = types.ModuleType("src.locales")
locales_module.getLocale = lambda x: x
sys.modules["src.locales"] = locales_module

# --- End stubs ---

from src.figure_editor import FigureEditor


class DummyTab:
    def __init__(self):
        self._layout = None

    def layout(self):
        return self._layout

    def setLayout(self, layout):
        self._layout = layout


class TabsStub:
    def __init__(self):
        self._tab = DummyTab()

    def widget(self, index):
        return self._tab


class FigureEditorTest(unittest.TestCase):
    def test_missing_initial_params_defaults_to_zero(self):
        tabs = TabsStub()
        params = ["length", "width"]
        constrains = [(0, 10), (0, 10)]
        initial_params = {"length": 5}  # 'width' is missing
        editor = FigureEditor(
            tabs,
            params,
            constrains,
            initial_params=initial_params,
            settings_provider=lambda: {},
        )
        self.assertEqual(editor.params_dict["length"], 5)
        self.assertEqual(editor.params_dict["width"], 0)


if __name__ == "__main__":
    unittest.main()
