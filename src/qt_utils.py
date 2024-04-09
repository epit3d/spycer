import concurrent.futures
from PyQt5 import QtCore
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QProgressDialog, QLineEdit
from PyQt5.QtCore import Qt
from PyQt5 import QtGui


class ClickableLineEdit(QLineEdit):
    clicked = QtCore.pyqtSignal()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit()
        else:
            super().mousePressEvent(event)


class TaskManager(QtCore.QObject):
    # source: https://stackoverflow.com/questions/64500883/pyqt5-widget-qthread-issue-when-using-concurrent-futures-threadpoolexecutor
    finished = QtCore.pyqtSignal(object)

    def __init__(self, parent=None, max_workers=None):
        super().__init__(parent)
        self._executor = concurrent.futures.ThreadPoolExecutor(max_workers=max_workers)

    @property
    def executor(self):
        return self._executor

    def submit(self, fn, *args, **kwargs):
        future = self.executor.submit(fn, *args, **kwargs)
        future.add_done_callback(self._internal_done_callback)

    def _internal_done_callback(self, future):
        data = future.result()
        self.finished.emit(data)


class LineEdit(QLineEdit):
    colorize_invalid_value = False

    def __init__(self, parent=None):
        super().__init__(parent)
        self.returnPressed.connect(self.value_formatting)
        self.textChanged.connect(self.input_validation)
        self.textChanged.connect(self.colorize_field)

    def setValidator(self, validator, colorize_invalid_value=False):
        self.colorize_invalid_value = colorize_invalid_value
        super().setValidator(validator)

    def focusOutEvent(self, event):
        self.value_formatting()
        self.colorize_field()
        super().focusOutEvent(event)

    def fill_empty(self):
        if (not self.text()) or (self.text() == "."):
            self.setText("0")

    def value_formatting(self):
        self.fill_empty()
        if isinstance(self.validator(), QtGui.QDoubleValidator):
            cursor_position = self.cursorPosition()
            self.setText(str(float(self.text())))
            self.setCursorPosition(cursor_position)

    def input_validation(self):
        cursor_position = self.cursorPosition()
        self.setText(self.text().replace(",", "."))

        if (not self.colorize_invalid_value) and self.validator():
            value = float(self.text()) if self.text() else 0

            max_value = self.validator().top()
            min_value = self.validator().bottom()

            if value > max_value:
                self.setText(str(max_value))
            if value < min_value:
                self.setText(str(min_value))
        self.setCursorPosition(cursor_position)

    def colorize_field(self):
        default_background_color = "#0e1621"
        invalid_value_background_color = "#ff6e00"

        if self.colorize_invalid_value:
            if self.hasAcceptableInput() or (not self.text()):
                self.setStyleSheet(f"background-color: {default_background_color}")
            else:
                self.setStyleSheet(
                    f"background-color: {invalid_value_background_color}"
                )


def progress_dialog(title, msg, work_fn, parent=None):
    """Show a blocking progress dialog while executing work in background thread"""
    progress = QProgressDialog(msg, None, 0, 0, parent=parent)
    progress.setWindowTitle(title)

    manager = TaskManager(max_workers=1)
    result = []

    def task_finished(v):
        progress.accept()
        result.append(v)

    manager.finished.connect(task_finished)

    manager.submit(work_fn)
    _exec_dialog(progress)

    return result[0]


def _exec_dialog(dg, closer=None):
    """
    Executes a dialog running the main event-loop instead of spawning a local one.
    Allows to nest dialog boxes safely.
    See: https://doc.qt.io/qt-6/qdialog.html#exec
    @param closer function accepting one QDialog param and connecting it via signals-slots with close action
    """
    event_loop = QEventLoop()
    dg.finished.connect(event_loop.quit)
    dg.setModal(True)
    dg.show()
    if closer:
        closer(dg)
    event_loop.exec_()
    return dg.result()
