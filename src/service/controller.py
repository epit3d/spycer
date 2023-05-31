import sys
import datetime
import traceback

from functools import partial
from PyQt5.QtCore import QObject, QThread, pyqtSignal, pyqtSlot


class Worker(QObject):
    completedSignal = pyqtSignal(int)
    outputSignal = pyqtSignal(str)
    statusSignal = pyqtSignal(str)

    def _appendOutput(self, text):
        self.outputSignal.emit(text)

    @staticmethod
    def handleExceptions(method):
        def _wrapper(self, *args, **kwargs):
            try:
                method(self, *args, **kwargs)
            except Exception as e:
                print('handler:', e)
                traceback.print_exc(chain=False)
                # traceback.print_last()
                # exc_info = sys.exc_info()
                self._appendOutput(str(e))

            self._appendOutput('================')
            self.completedSignal.emit(0)

        return _wrapper

    @pyqtSlot(object)
    @handleExceptions
    def doWork(self, method):
        method()

    @pyqtSlot(object, list)
    @handleExceptions
    def doWorkWithArgs(self, method, args):
        method(*args)


class ServiceController(QObject):
    def _log(self, text):
        self._fileLog.write(f'{datetime.datetime.now()} {text}\n')

    @pyqtSlot()
    def showSlot(self):
        self.printer.openGcodeFile()
        self._fileLog = open('service.log', 'a', buffering=1)
        self._log('log started')

    @pyqtSlot()
    def closeSlot(self):
        self.printer.closeGcodeFile()
        self._log('===============================')
        self._fileLog.close()

    @pyqtSlot(str)
    def logOutput(self, text):
        self._log(text)
        self.view.logOutput.append(text)
        self.view.logOutput.ensureCursorVisible()

    @pyqtSlot(str)
    def setStatus(self, text):
        self.view.statusLabel.setText(text)

    def __del__(self):
        print('service controller deleted')

    workSignal = pyqtSignal([object], [object, list])

    def __init__(self, view, printer):
        super().__init__()

        view.showedSignal.connect(self.showSlot)
        view.closedSignal.connect(self.closeSlot)

        worker = Worker()

        printer.setOutputMethod(lambda text: worker.outputSignal.emit(text))
        printer.setStatusMethod(lambda text: worker.statusSignal.emit(text))

        worker.outputSignal.connect(self.logOutput)
        worker.statusSignal.connect(self.setStatus)

        @pyqtSlot(int)
        def completedHandler(res):
            print(res)
            for widget in view.runGcodeWidgets:
                    widget.setEnabled(True)
        worker.completedSignal.connect(completedHandler)

        self.workSignal[object].connect(worker.doWork)
        self.workSignal[object, list].connect(worker.doWorkWithArgs)

        view.zProbeButton.clicked.connect(
            partial(self.workSignal.emit, printer.zProbe)
        )

        view.startCalibrationButton.clicked.connect(
            partial(self.workSignal.emit, printer.startCalibration)
        )

        def runHandler(textSource):
            posZ = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.defDelta, [posZ])
        view.defDeltaButton.clicked.connect(
            partial(runHandler, view.bedZLevelWidget.zLevelSource)
        )

        def runHandler(textSource):
            posZ = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.defAxisU, [posZ])
        view.defAxisUButton.clicked.connect(
            partial(runHandler, view.bedZLevelWidget.zLevelSource)
        )

        def runHandler(textSource):
            posZ = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.defAxisV, [posZ])
        view.defAxisVButton.clicked.connect(
            partial(runHandler, view.bedZLevelWidget.zLevelSource)
        )

        view.defOriginButton.clicked.connect(
            partial(self.workSignal.emit, printer.defOrigin)
        )
        view.testCalibrationButton.clicked.connect(
            partial(self.workSignal.emit, printer.testCalibration)
        )
        view.callM112Button.clicked.connect(
            partial(self.workSignal.emit, printer.callM112)
        )
        view.callHomeButton.clicked.connect(
            partial(self.workSignal.emit, printer.callHome)
        )
        view.callProbePosXButton.clicked.connect(
            partial(self.workSignal.emit, printer.callProbePosX)
        )
        view.callProbeNegXButton.clicked.connect(
            partial(self.workSignal.emit, printer.callProbeNegX)
        )
        view.probeLineButton.clicked.connect(
            partial(self.workSignal.emit, printer.probeLine)
        )
        view.doHeatButton.clicked.connect(
            partial(self.workSignal.emit, printer.doHeat)
        )
        view.doDemoButton.clicked.connect(
            partial(self.workSignal.emit, printer.doDemo)
        )
        view.doDemo2Button.clicked.connect(
            partial(self.workSignal.emit, printer.doDemo2)
        )
        view.incPosXButton.clicked.connect(
            partial(self.workSignal.emit, printer.incPosX)
        )
        view.incNegXButton.clicked.connect(
            partial(self.workSignal.emit, printer.incNegX)
        )
        view.incPosYButton.clicked.connect(
            partial(self.workSignal.emit, printer.incPosY)
        )
        view.incNegYButton.clicked.connect(
            partial(self.workSignal.emit, printer.incNegY)
        )
        view.incPosZButton.clicked.connect(
            partial(self.workSignal.emit, printer.incPosZ)
        )
        view.incNegZButton.clicked.connect(
            partial(self.workSignal.emit, printer.incNegZ)
        )

        for widget in view.runGcodeWidgets:
            button = widget.runButton
            dataSource = widget.gcodeSource

            def runHandler(textSource):
                gcode = textSource.text()
                self.workSignal[object, list].emit(printer.runGcode, [gcode])
                for widget in view.runGcodeWidgets:
                    widget.setEnabled(False)

            button.clicked.connect(partial(runHandler, dataSource))

        def runHandler(textSource):
            posY = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.adjustPlateY, [posY])
        view.adjustMeasurePlateYWidget.adjustButton.clicked.connect(
            partial(runHandler, view.adjustMeasurePlateYWidget.angleSource)
        )

        def runHandler(textSource):
            posY = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.measurePlateY, [posY])
        view.adjustMeasurePlateYWidget.measureButton.clicked.connect(
            partial(runHandler, view.adjustMeasurePlateYWidget.angleSource)
        )

        def runHandler(textSource):
            posX = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.adjustPlateX, [posX])
        view.adjustMeasurePlateXWidget.adjustButton.clicked.connect(
            partial(runHandler, view.adjustMeasurePlateXWidget.angleSource)
        )

        def runHandler(textSource):
            posX = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.measurePlateX, [posX])
        view.adjustMeasurePlateXWidget.measureButton.clicked.connect(
            partial(runHandler, view.adjustMeasurePlateXWidget.angleSource)
        )

        view.measureXDeviationFromVButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureXDeviationFromV)
        )
        view.measureZDeviationFromVButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureZDeviationFromV)
        )
        view.measureVDeviationFromVButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureVDeviationFromV)
        )
        view.measureOrthoXYButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureOrthoXY)
        )
        view.measureOrthoYZButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureOrthoYZ)
        )
        view.measureOrthoXZButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureOrthoXZ)
        )

        view.defScaleXButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureScaleX)
        )
        view.defScaleYButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureScaleY)
        )
        view.defScaleZButton.clicked.connect(
            partial(self.workSignal.emit, printer.measureScaleZ)
        )

        def runHandler(textSource):
            posZ = float(textSource.text().strip())
            self.workSignal[object, list].emit(printer.defBedIncline, [posZ])
        view.bedInclineButton.clicked.connect(
            partial(runHandler, view.bedZLevelWidget.zLevelSource)
        )

        self.worker_thread = QThread()
        worker.moveToThread(self.worker_thread)
        self.worker_thread.start()

        self.worker = worker
        self.view = view
        self.printer = printer
