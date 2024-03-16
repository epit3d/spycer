import os
import shutil
import zipfile

from os import path
from datetime import datetime
from functools import partial
from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTextEdit, QPushButton, QLabel, QHBoxLayout, QFileDialog, QMessageBox
from src.settings import sett, save_splanes_to_file, PathBuilder
from src.client import send_bug_report

class bugReportDialog(QWidget):
    def __init__(self, controller):
        super().__init__()
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.setWindowTitle(controller.view.locale.SubmittingBugReport)
        self.setMinimumWidth(500)

        layout = QVBoxLayout()

        self.description_label = QLabel(controller.view.locale.ErrorDescription)
        layout.addWidget(self.description_label)

        self.error_description = QTextEdit()
        layout.addWidget(self.error_description)
        self.error_description.setMinimumSize(400, 200)

        self.image_list = QLabel()
        layout.addWidget(self.image_list)

        add_image_button = QPushButton(controller.view.locale.AddImage)
        add_image_button.setFixedWidth(207)
        add_image_button.clicked.connect(partial(self.addImage, controller))
        layout.addWidget(add_image_button)

        send_layout = QHBoxLayout()
        send_layout.setAlignment(QtCore.Qt.AlignLeft)
        layout.addLayout(send_layout)

        send_button = QPushButton(controller.view.locale.Send)
        send_button.setFixedWidth(100)
        send_button.clicked.connect(partial(self.send, controller))
        send_layout.addWidget(send_button)

        cancel_button = QPushButton(controller.view.locale.Cancel)
        cancel_button.setFixedWidth(100)
        cancel_button.clicked.connect(self.cancel)
        send_layout.addWidget(cancel_button)

        self.setLayout(layout)

        self.archive_path = ""
        self.images = []
        self.temp_folder = "temp"
        self.temp_images_folder = os.path.join(self.temp_folder, "images")

    def addImage(self, controller):
        if not os.path.exists(self.temp_folder):
            os.mkdir(self.temp_folder)

        if not os.path.exists(self.temp_images_folder):
            os.mkdir(self.temp_images_folder)

        image_path, _ = QFileDialog.getOpenFileName(self, controller.view.locale.AddingImage, "", "Images (*.png *.jpg)")

        if image_path:
            image_name = os.path.basename(image_path)
            temp_image_path = os.path.join(self.temp_images_folder, image_name)
            shutil.copy2(image_path, temp_image_path)

            if not temp_image_path in self.images:
                self.images.append(temp_image_path)
                self.update_image_names_label()

    def update_image_names_label(self):
        image_names = ', '.join([os.path.basename(image_name) for image_name in self.images])
        self.image_list.setText(image_names)

    def send(self, controller):
        try:
            error_description = self.error_description.toPlainText()

            if not error_description:
                message_box = QMessageBox(parent=self)
                message_box.setWindowTitle(controller.view.locale.SubmittingBugReport)
                message_box.setText(controller.view.locale.EmptyDescription)
                message_box.setIcon(QMessageBox.Critical)
                message_box.exec_()
                return

            controller.save_settings("vip")

            if not os.path.exists("temp"):
                os.makedirs("temp")

            current_datetime = datetime.now().strftime("%Y-%m-%d %H-%M-%S")
            self.archive_path = os.path.join("temp", f"{current_datetime}.zip")

            self.addFolderToArchive(self.archive_path, PathBuilder.project_path(), "project")
            self.addFolderToArchive(self.archive_path, self.temp_images_folder, "images")


            if os.path.exists("interface.log"):
                with zipfile.ZipFile(self.archive_path, 'a') as archive:
                    archive.write("interface.log")

            with zipfile.ZipFile(self.archive_path, 'a') as archive:
                archive.writestr("error_description.txt", error_description)

            successfully_sent = send_bug_report(self.archive_path, error_description)

            self.cleaningTempFiles()
            self.close()

            if successfully_sent:
                self.successfulSendWindow(controller)
            else:
                self.failedSendWindow(controller)

        except Exception as e:
            self.cleaningTempFiles()
            self.close()

            self.failedSendWindow(controller, str(e))

    def addFolderToArchive(self, archive_path, folder_path, subfolder = ""):
        with zipfile.ZipFile(archive_path, 'a') as archive:
            for path, _, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(path, file)
                    archive_relative_path = os.path.relpath(file_path, folder_path)
                    if subfolder:
                        archive.write(file_path, os.path.join(subfolder, archive_relative_path))
                    else:
                        archive.write(file_path, archive_relative_path)

    def successfulSendWindow(self, controller):
        message_box = QMessageBox(parent=self)
        message_box.setWindowTitle(controller.view.locale.SubmittingBugReport)
        message_box.setText(controller.view.locale.ReportSubmitSuccessfully)
        message_box.setIcon(QMessageBox.Information)
        message_box.exec_()

    def failedSendWindow(self, controller, error_msg: str = ""):
        message_box = QMessageBox(parent=self)
        message_box.setWindowTitle(controller.view.locale.SubmittingBugReport)
        message_box.setText(controller.view.locale.ErrorReport + f"\nError message: {error_msg}")
        message_box.setIcon(QMessageBox.Critical)
        message_box.exec_()

    def closeEvent(self, event):
        self.cleaningTempFiles()
        event.accept()

    def cancel(self):
        self.cleaningTempFiles()
        self.close()

    def cleaningTempFiles(self):
        try:
            for image_path in self.images:
                os.remove(image_path)
            if self.archive_path:
                if os.path.exists(self.archive_path):
                    os.remove(self.archive_path)
                self.archive_path = ""
            self.images = []
            self.image_list.setText("")
            self.error_description.setText("")
        except Exception as e:
            print(str(e))
