import sys
import types


class Signal:
    def __init__(self):
        self._callbacks = []

    def connect(self, func):
        self._callbacks.append(func)

    def emit(self, *args, **kwargs):
        for cb in self._callbacks:
            cb(*args, **kwargs)


class QStyle:
    SP_DialogApplyButton = 0
    SP_DialogCloseButton = 0

    def standardIcon(self, *args, **kwargs):
        return None


class QWidget:
    def __init__(self, *args, **kwargs):
        pass

    def setLayout(self, *args, **kwargs):
        pass

    def setSizePolicy(self, *args, **kwargs):
        pass

    def setObjectName(self, *args, **kwargs):
        pass

    def style(self):
        return QStyle()

    def setWindowTitle(self, *args, **kwargs):
        pass

    def deleteLater(self):
        pass


class QLayout:
    SetFixedSize = 0


class LayoutItem:
    def __init__(self, widget):
        self._widget = widget

    def widget(self):
        return self._widget


class QGridLayout:
    def __init__(self, *args, **kwargs):
        self._grid = {}

    def setSpacing(self, *args, **kwargs):
        pass

    def setVerticalSpacing(self, *args, **kwargs):
        pass

    def setHorizontalSpacing(self, *args, **kwargs):
        pass

    def setContentsMargins(self, *args, **kwargs):
        pass

    def setColumnStretch(self, *args, **kwargs):
        pass

    def setSizeConstraint(self, *args, **kwargs):
        pass

    def addWidget(self, widget, row, column, rowspan=1, colspan=1):
        for r in range(row, row + rowspan):
            for c in range(column, column + colspan):
                self._grid[(r, c)] = LayoutItem(widget)

    def itemAtPosition(self, row, column):
        return self._grid.get((row, column))


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

    def setToolTip(self, *args, **kwargs):
        pass

    def setStyleSheet(self, *args, **kwargs):
        pass


class QCheckBox(QWidget):
    def __init__(self, *args, **kwargs):
        self.stateChanged = Signal()

    def setChecked(self, *args, **kwargs):
        pass

    def setCheckState(self, *args, **kwargs):
        pass


class QScrollArea(QWidget):
    def setWidget(self, *args, **kwargs):
        pass

    def setWidgetResizable(self, *args, **kwargs):
        pass


class QComboBox(QWidget):
    def __init__(self, *args, **kwargs):
        self.currentIndexChanged = Signal()

    def addItem(self, *args, **kwargs):
        pass


class QToolBox(QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.items = []

    def addItem(self, widget, label):
        self.items.append((widget, label))


class QSpinBox(QWidget):
    def __init__(self, *args, **kwargs):
        self._value = 0
        self.valueChanged = Signal()

    def setMinimum(self, v):
        pass

    def setMaximum(self, v):
        pass

    def setValue(self, v):
        self._value = v
        self.valueChanged.emit(v)

    def value(self):
        return self._value


class QDoubleSpinBox(QSpinBox):
    pass


class QApplication:
    def __init__(self, *args, **kwargs):
        pass


qtwidgets = types.ModuleType("PyQt5.QtWidgets")
qtwidgets.QWidget = QWidget
qtwidgets.QGridLayout = QGridLayout
qtwidgets.QHBoxLayout = QHBoxLayout
qtwidgets.QVBoxLayout = QVBoxLayout
qtwidgets.QLabel = QLabel
qtwidgets.QLineEdit = QLineEdit
qtwidgets.QSlider = QSlider
qtwidgets.QSizePolicy = QSizePolicy
qtwidgets.QPushButton = QPushButton
qtwidgets.QCheckBox = QCheckBox
qtwidgets.QScrollArea = QScrollArea
qtwidgets.QComboBox = QComboBox
qtwidgets.QApplication = QApplication
qtwidgets.QToolBox = QToolBox
qtwidgets.QSpinBox = QSpinBox
qtwidgets.QDoubleSpinBox = QDoubleSpinBox
qtwidgets.QLayout = QLayout
qtwidgets.QStyle = QStyle


qtcore = types.ModuleType("PyQt5.QtCore")


class QLocale:
    def __init__(self, *args, **kwargs):
        pass


class Qt:
    Horizontal = 1
    Checked = True


class QSettings:
    def __init__(self, *args, **kwargs):
        pass


qtcore.QLocale = QLocale
qtcore.Qt = Qt
qtcore.QSettings = QSettings


qtgui = types.ModuleType("PyQt5.QtGui")


class DummyValidator:
    def __init__(self, *args, **kwargs):
        pass

    def setLocale(self, *args, **kwargs):
        pass


qtgui.QIntValidator = DummyValidator
qtgui.QDoubleValidator = DummyValidator
qtgui.QValidator = object


sip = types.ModuleType("sip")
sip.isdeleted = lambda obj: False


pyqt5 = types.ModuleType("PyQt5")
pyqt5.QtWidgets = qtwidgets
pyqt5.QtCore = qtcore
pyqt5.QtGui = qtgui
pyqt5.sip = sip

sys.modules["PyQt5"] = pyqt5
sys.modules["PyQt5.QtWidgets"] = qtwidgets
sys.modules["PyQt5.QtCore"] = qtcore
sys.modules["PyQt5.QtGui"] = qtgui
sys.modules["sip"] = sip

