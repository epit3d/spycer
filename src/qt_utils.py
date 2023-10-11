import concurrent.futures
from PyQt5 import QtCore
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QProgressDialog, QLineEdit
from PyQt5.QtCore import Qt

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

    return result[0] # if len(result) != 0 else 'Program crashed without returning a result.'

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
