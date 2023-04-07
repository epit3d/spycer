from PyQt5.QtWidgets import (
    QLineEdit, QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout,
    QTextEdit, QMessageBox, QDialog
)

from PyQt5.QtCore import pyqtSignal


class ServicePanel(QDialog):

    def __del__(self):
        print('service panel deleted')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.messageBox = QMessageBox(parent=self)

        mainLayout = QVBoxLayout()

        button = QPushButton('Z probe')
        mainLayout.addWidget(button)
        self.zProbeButton = button

        button = QPushButton('Start Calibration')
        mainLayout.addWidget(button)
        self.startCalibrationButton = button

        def subWidget():
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel('Z initial height')
            layout.addWidget(label)

            lineEdit = QLineEdit('10')
            layout.addWidget(lineEdit)
            widget.zLevelSource = lineEdit

            self.bedZLevelWidget = widget
            return widget

        mainLayout.addWidget(subWidget())

        button = QPushButton('Delta Calibration')
        mainLayout.addWidget(button)
        self.defDeltaButton = button

        # U axis, V axis, Origin
        def subLayout():
            layout = QHBoxLayout()

            button = QPushButton('U axis Definition')
            layout.addWidget(button)
            self.defAxisUButton = button

            button = QPushButton('V axis Definition')
            layout.addWidget(button)
            self.defAxisVButton = button

            button = QPushButton('Origin Definition')
            layout.addWidget(button)
            self.defOriginButton = button

            return layout

        mainLayout.addLayout(subLayout())

        button = QPushButton('Test Calibration')
        mainLayout.addWidget(button)
        self.testCalibrationButton = button

        button = QPushButton('Emergency Stop (M112)')
        mainLayout.addWidget(button)
        self.callM112Button = button

        # Home, Probe X, Probe Line, Heat, Demo
        def subLayout():
            layout = QHBoxLayout()

            button = QPushButton('Home')
            layout.addWidget(button)
            self.callHomeButton = button

            button = QPushButton('Probe Pos X')
            layout.addWidget(button)
            self.callProbePosXButton = button

            button = QPushButton('Probe Neg X')
            layout.addWidget(button)
            self.callProbeNegXButton = button

            button = QPushButton('Probe Line')
            layout.addWidget(button)
            self.probeLineButton = button

            button = QPushButton('Heat')
            layout.addWidget(button)
            self.doHeatButton = button

            button = QPushButton('Demo')
            layout.addWidget(button)
            self.doDemoButton = button

            button = QPushButton('Demo2')
            layout.addWidget(button)
            self.doDemo2Button = button

            return layout

        mainLayout.addLayout(subLayout())

        # incremental move
        def subLayout():
            layout = QHBoxLayout()

            # X incremental move
            def subLayout():
                layout = QVBoxLayout()

                button = QPushButton('X+')
                layout.addWidget(button)
                self.incPosXButton = button

                button = QPushButton('X-')
                layout.addWidget(button)
                self.incNegXButton = button

                return layout
            layout.addLayout(subLayout())

            # Y incremental move
            def subLayout():
                layout = QVBoxLayout()

                button = QPushButton('Y+')
                layout.addWidget(button)
                self.incPosYButton = button

                button = QPushButton('Y-')
                layout.addWidget(button)
                self.incNegYButton = button

                return layout
            layout.addLayout(subLayout())

            # Z incremental move
            def subLayout():
                layout = QVBoxLayout()

                button = QPushButton('Z+')
                layout.addWidget(button)
                self.incPosZButton = button

                button = QPushButton('Z-')
                layout.addWidget(button)
                self.incNegZButton = button

                return layout
            layout.addLayout(subLayout())

            return layout

        mainLayout.addLayout(subLayout())

        self.runGcodeWidgets = []
        for num in range(4):
            container = QWidget()
            layout = QHBoxLayout(container)
            layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f'G-Code {num + 1}:')
            layout.addWidget(label)

            lineEdit = QLineEdit()
            layout.addWidget(lineEdit)
            container.gcodeSource = lineEdit

            button = QPushButton('Run')
            layout.addWidget(button)
            container.runButton = button

            mainLayout.addWidget(container)
            self.runGcodeWidgets.append(container)

        def subWidget():
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f'Y :')
            layout.addWidget(label)

            lineEdit = QLineEdit('30')
            layout.addWidget(lineEdit)
            widget.angleSource = lineEdit

            button = QPushButton('Adjust Plate')
            layout.addWidget(button)
            widget.adjustButton = button

            button = QPushButton('Meausre Plate')
            layout.addWidget(button)
            widget.measureButton = button

            self.adjustMeasurePlateYWidget = widget
            return widget

        mainLayout.addWidget(subWidget())

        def subWidget():
            widget = QWidget()
            layout = QHBoxLayout(widget)
            layout.setContentsMargins(0, 0, 0, 0)

            label = QLabel(f'X :')
            layout.addWidget(label)

            lineEdit = QLineEdit('30')
            layout.addWidget(lineEdit)
            widget.angleSource = lineEdit

            button = QPushButton('Adjust Plate')
            layout.addWidget(button)
            widget.adjustButton = button

            button = QPushButton('Meausre Plate')
            layout.addWidget(button)
            widget.measureButton = button

            self.adjustMeasurePlateXWidget = widget
            return widget

        mainLayout.addWidget(subWidget())

        def subLayout():
            layout = QHBoxLayout()

            button = QPushButton('Measure X from V')
            layout.addWidget(button)
            self.measureXDeviationFromVButton = button

            button = QPushButton('Measure Z from V')
            layout.addWidget(button)
            self.measureZDeviationFromVButton = button

            button = QPushButton('Measure V from V')
            layout.addWidget(button)
            self.measureVDeviationFromVButton = button

            button = QPushButton('Measure Ortho XY')
            layout.addWidget(button)
            self.measureOrthogonalityXYButton = button

            button = QPushButton('Measure Ortho YZ')
            layout.addWidget(button)
            self.measureOrthoYZButton = button

            button = QPushButton('Measure Ortho XZ')
            layout.addWidget(button)
            self.measureOrthoXZButton = button

            return layout

        mainLayout.addLayout(subLayout())

        label = QLabel('Application started')
        mainLayout.addWidget(label)
        self.statusLabel = label

        textEdit = QTextEdit()
        textEdit.setReadOnly(True)
        mainLayout.addWidget(textEdit)
        self.logOutput = textEdit

        self.setLayout(mainLayout)

    showedSignal = pyqtSignal()

    def showEvent(self, event):
        self.showedSignal.emit()

    closedSignal = pyqtSignal()

    def closeEvent(self, event):
        self.messageBox.setText("Are you sure?")
        self.messageBox.setStandardButtons(
            QMessageBox.StandardButton.Yes |
            QMessageBox.StandardButton.Cancel)
        close = self.messageBox.exec_()

        if close != QMessageBox.StandardButton.Yes:
            event.ignore()
            return

        self.closedSignal.emit()
        event.accept()
