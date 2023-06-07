from PyQt5.QtWidgets import (
    QProgressBar, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal


class CalibrationPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setMinimumHeight(500)

        btnLayout = QHBoxLayout()

        # btnBack = QPushButton('Back')
        # btnBack.setEnabled(False)
        # btnBack.clicked.connect(prevStep)

        btnNext = QPushButton('Next')

        btnCancel = QPushButton('Cancel')

        btnFinish = QPushButton('Finish')

        btnLayout.addStretch(1)
        # btnLayout.addWidget(btnBack)
        btnLayout.addWidget(btnNext)
        btnLayout.addWidget(btnCancel)
        btnLayout.addWidget(btnFinish)

        mainLayout = QVBoxLayout(self)
        label = QLabel('Hello')
        label.setWordWrap(True)
        label.setTextFormat(Qt.RichText)

        progressBar = QProgressBar()
        sp_retain = progressBar.sizePolicy()
        sp_retain.setRetainSizeWhenHidden(True)
        progressBar.setSizePolicy(sp_retain)

        mainLayout.addWidget(label)
        mainLayout.addWidget(progressBar)
        mainLayout.addStretch(1)
        mainLayout.addLayout(btnLayout)

        self.label = label
        # self.btnBack = btnBack
        self.btnNext = btnNext
        self.btnCancel = btnCancel
        self.btnFinish = btnFinish
        self.progressBar = progressBar

    def updateMainInterface(self, locale):
        self.setWindowTitle(locale['window'])
        self.btnNext.setText(locale['btnNext'])
        self.btnCancel.setText(locale['btnCancel'])
        self.btnFinish.setText(locale['btnFinish'])

    showedSignal = pyqtSignal()

    def showEvent(self, event):
        self.showedSignal.emit()
