import concurrent.futures
import threading
from PyQt5 import QtCore
from PyQt5.QtCore import QThread
from PyQt5.QtWidgets import QProgressDialog, QApplication


def progress_dialog(title, msg, work_fn, parent=None):
    """Show a blocking progress dialog while executing work in background thread"""
    def work():
        """Executes work ending with accepting dialog"""
        try:
            return work_fn()
        finally:
            progress.accept()

    progress = QProgressDialog(msg, None, 0, 0, parent=parent)
    progress.setWindowTitle(title)
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        # timer is used to schedule executing work after progress dialog
        # is opened, otherwise it could be accepted before being opened
        future = []
        QtCore.QTimer.singleShot(0, lambda: future.append(executor.submit(work)))
        _exec_dialog(progress)
        return future[0].result()  # transports exceptions as well


def _exec_dialog(dg, closer=None):
    """
    Executes a dialog running the main event-loop instead of spawning a local one.
    Allows to nest dialog boxes safely.
    See: https://doc.qt.io/qt-6/qdialog.html#exec
    @param closer function accepting one QDialog param and connecting it via signals-slots with close action
    """
    app = QApplication.instance()
    if QThread.currentThread() != app.thread():
        raise Exception('attempting to exec a QDialog from non-gui thread')

    event = threading.Event()
    dg.finished.connect(lambda: event.set())
    dg.setModal(True)
    dg.show()
    if closer:
        closer(dg)
    while not event.is_set():
        app.processEvents()
    return dg.result()
