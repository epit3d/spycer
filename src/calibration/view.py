from PyQt5.QtWidgets import (
    QProgressBar, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QDialog
)
from PyQt5.QtCore import Qt, pyqtSignal


class CalibrationPanel(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(400)
        self.setMinimumHeight(300)

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

        self.setLang('ru')

    def setLang(self, lang):
        if lang == 'ru':
            print('lang', lang)
            self.btnNext.setText('Далее')
            self.btnCancel.setText('Отмена')
            self.btnFinish.setText('Завершить')
        elif lang == 'en':
            self.btnNext.setText('Next')
            self.btnCancel.setText('Cancel')
            self.btnFinish.setText('Finish')

    showedSignal = pyqtSignal()

    def showEvent(self, event):
        self.showedSignal.emit()
