import traceback
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class Worker(QObject):
    completedSignal = pyqtSignal(int)

    def __init__(self, steps):
        super().__init__()
        self.steps = steps

    @staticmethod
    def handleExceptions(method):
        def _wrapper(self, *args, **kwargs):
            try:
                method(self, *args, **kwargs)
            except Exception as e:
                print('handler:', e)
                traceback.print_exc(chain=False)
                self.completedSignal.emit(1)
                return
                # traceback.print_last()
                # exc_info = sys.exc_info()

            self.completedSignal.emit(0)

        return _wrapper

    @pyqtSlot(int)
    @handleExceptions
    def doWork(self, i):
        self.steps[i].printerMethod()


class CalibrationController(QObject):
    workSignal = pyqtSignal(int)
    closeSignal = pyqtSignal()

    @pyqtSlot()
    def showSlot(self):
        self.worker_thread.start()

        self.step = 0
        self.view.label.setText(self.steps[self.step].labelText)
        self.view.btnFinish.setVisible(False)
        self.view.progressBar.setVisible(False)
        self.view.btnNext.setEnabled(True)

    @pyqtSlot(int)
    def completedHandler(self, res):
        if res == 0:
            self.step += 1
        else:
            errorText = f"An error has occured! {res}"
            self.messageBox.critical(self.view, "Error", errorText)

        if self.step < len(self.steps) - 1:
            self.view.btnNext.setEnabled(True)
        else:
            self.view.btnFinish.setVisible(True)
        self.view.progressBar.setVisible(False)
        self.view.label.setText(self.steps[self.step].labelText)

    def __init__(self, view, steps):
        super().__init__()

        self.messageBox = QMessageBox()
        self.gcodeResults = []
        self.textResults = []

        self.view = view
        self.steps = steps

        view.btnNext.clicked.connect(self.clickNext)
        view.btnCancel.clicked.connect(self.view.close)
        view.btnFinish.clicked.connect(self.clickFinish)
        view.progressBar.setMinimum(0)
        view.progressBar.setMaximum(0)

        worker = Worker(self.steps)
        self.worker = worker
        self.workSignal.connect(worker.doWork)
        worker.completedSignal.connect(self.completedHandler)

        view.showedSignal.connect(self.showSlot)
        # view.closedSignal.connect(self.closeSlot)
        view.closeEvent = self.closeEvent

        self.worker_thread = QThread()
        worker.moveToThread(self.worker_thread)

    def clickNext(self):
        self.workSignal.emit(self.step)
        self.view.btnNext.setEnabled(False)
        self.view.progressBar.setVisible(True)

    def clickFinish(self):
        self.steps[self.step].printerMethod()
        self.view.close()

    def closeEvent(self, event):
        self.worker_thread.terminate()
        self.worker_thread.wait()
        event.accept()
