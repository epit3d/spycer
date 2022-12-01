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


class Step:
    def __init__(self, num, stepType='text', labelText='', printerMethod=None):
        self.num = num
        self.type = stepType
        self.labelText = labelText
        self.printerMethod = printerMethod


class CalibrationController(QObject):
    workSignal = pyqtSignal(int)
    closeSignal = pyqtSignal()

    @pyqtSlot()
    def showSlot(self):
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

        print(self.step)
        if self.step < len(self.steps) - 1:
            self.view.btnNext.setEnabled(True)
        else:
            self.view.btnFinish.setVisible(True)
        self.view.progressBar.setVisible(False)
        self.view.label.setText(self.steps[self.step].labelText)

    def __init__(self, view, printer):
        super().__init__()

        self.messageBox = QMessageBox()
        self.gcodeResults = []
        self.textResults = []

        self.view = view
        self.printer = printer

        self.steps = []
        self.initSteps()

        view.btnNext.clicked.connect(self.clickNext)
        view.btnCancel.clicked.connect(self.view.close)
        view.btnFinish.clicked.connect(self.clickFinish)
        view.progressBar.setMinimum(0)
        view.progressBar.setMaximum(0)

        worker = Worker(self.steps)
        self.worker = worker
        self.workSignal.connect(worker.doWork)
        worker.completedSignal.connect(self.completedHandler)

        printer.setOutputMethod(print)
        printer.setStatusMethod(print)
        self.printer = printer

        view.showedSignal.connect(self.showSlot)
        # view.closedSignal.connect(self.closeSlot)

        self.worker_thread = QThread()
        worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

    def clickNext(self):
        self.workSignal.emit(self.step)
        self.view.btnNext.setEnabled(False)
        self.view.progressBar.setVisible(True)

    def clickFinish(self):
        self.view.close()

    def initSteps(self):
        stepLabels = (
            '<p>'
            'Step 1 of 4'
            '</p>'
            '<p>'
            'This wizard is intended for collecting the'
            ' calibaration data of the Epit 3D printer.'
            '</p>'
            '<p>'
            '<b>!!!IMPORTANT!!!</b>'
            '<br>'
            'Please unmout the glass'
            ' from the bed. If this is not done at this'
            ' step, the nozzle may crash into the bed.'
            '</p>'
            '<p>'
            'Please mount the calibration ball instead'
            ' of the nozzle.'
            '</p>'
            '<p>'
            'Please connect the calibtation wire to the bed.'
            '</p>'
            '<p>'
            'Upon pressing  the <b>Next</b> button printer will'
            ' perform movements to collect the calibration data.'
            '<br>'
            '(Delta calibration)'
            '</p>',

            '<p>'
            'Step 2 of 4'
            '</p>'
            '<p>'
            'Please mount the fixture #1 to the bed.'
            '</p>'
            '<p>'
            'Upon pressing  the <b>Next</b> button printer will'
            ' perform movements to collect the calibration data.'
            '<br>'
            '(Scale factor check, orthogonality check)'
            '</p>',

            '<p>'
            'Step 3 of 4'
            '</p>'
            '<p>'
            'Please unmount the fixture #1 from the bed.'
            '</p>'
            '<p>'
            'Upon pressing  the <b>Next</b> button printer will'
            ' perform movements to collect the calibration data.'
            '<br>'
            '(U axis definition, V axis definition)'
            '</p>',

            '<p>'
            'Step 4 of 4'
            '</p>'
            '<p>'
            'Please mount the fixture #2 to the bed.'
            '</p>'
            '<p>'
            'Upon pressing  the <b>Next</b> button printer will'
            ' perform movements to collect the calibration data.'
            '<br>'
            '(Origin definition)'
            '</p>',

            '<p>'
            'Calibration point collection finished successfully.'
            '</p>'
            '<p>'
            'Please unmount the fixture #2 from the bed.'
            '</p>'
            '<p>'
            'Please disconnect the calibtation wire from the bed.'
            '</p>'
            '<p>'
            'Please mount back the glass to the bed and'
            ' replace the calibration ball by nozzle.'
            '</p>'
            'Upon pressing  the <b>Finish</b> button a new calibration'
            ' file will be created for this printer.'
            '</p>',
        )
        for num, label in enumerate(stepLabels):
            self.steps += [Step(num, labelText=label)]

        for step in self.steps:
            step.printerMethod = lambda n=step.num: print('Printer method', n)
