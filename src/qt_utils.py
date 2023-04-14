import concurrent.futures
from PyQt5 import QtCore
from PyQt5.QtCore import QEventLoop
from PyQt5.QtWidgets import QProgressDialog


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
    event_loop = QEventLoop()
    dg.finished.connect(event_loop.quit)
    dg.setModal(True)
    dg.show()
    if closer:
        closer(dg)
    event_loop.exec_()
    return dg.result()
