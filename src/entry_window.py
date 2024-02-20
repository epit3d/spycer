import os, math
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QLabel, QListWidget, QListWidgetItem, QLineEdit, QFileDialog, QMessageBox, QShortcut
from PyQt5.QtCore import QSettings
from PyQt5.QtGui import QKeySequence

# import aligntop
from PyQt5 import QtCore
from PyQt5 import QtGui
from typing import List

from src.gui_utils import showErrorDialog
from src.settings import sett, get_version, set_version, paths_transfer_in_settings, PathBuilder
import src.locales as locales
import shutil

class EntryWindow(QWidget):
    # entry window is a window that is shown before main window
    # it is used to choose between creation of new project and opening existing one

    # signal accepts path to project file
    open_project_signal = QtCore.pyqtSignal(str)

    # signal accepts path to project file
    create_project_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(locales.getLocale().ProjectManager)
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.init_ui()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        for i in range(self.recent_projects_list_widget.count()):
            item = self.recent_projects_list_widget.item(i)
            self.adjust_item_height(item)

    def adjust_item_height(self, item):
        widget = self.recent_projects_list_widget.itemWidget(item)
        list_width = self.recent_projects_list_widget.viewport().width()
        widget.setFixedWidth(list_width)
        widget.setWordWrap(True)
        widget.adjustSize()

        item.setSizeHint(QtCore.QSize(widget.width(), widget.height()))

    def showEvent(self, e):
        # showEvent is run when we first open and when we close project
        # when we close project and entry window pops up we need to update
        # list of projects because new project will not be included

        # update list of recent projects
        self.reload_recent_projects_list()
        
        super().showEvent(e)

    def init_ui(self):
        self.setBaseSize(600, 300)

        # create layout for creating new project
        new_proj_layout = QVBoxLayout()
        new_proj_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create "New Project" button
        self.new_project_button = QPushButton(locales.getLocale().NewProject, self)
        self.new_project_button.clicked.connect(self.create_new_project)
        new_proj_layout.addWidget(self.new_project_button)

        # create project directory label
        self.project_directory_label = QLabel(locales.getLocale().ProjectDirectory, self)
        new_proj_layout.addWidget(self.project_directory_label)

        # create project location label with current folder
        self.project_directory_edit = QLineEdit(self.load_recent_projects_root(), self)
        self.project_directory_edit.setPlaceholderText(
            locales.getLocale().ChooseProjectDirectory)
        self.project_directory_edit.setReadOnly(True)
        new_proj_layout.addWidget(self.project_directory_edit)

        # create project location folder dialog
        self.project_location_folder_dialog = QPushButton(
            locales.getLocale().ChooseProjectDirectory, self)
        new_proj_layout.addWidget(self.project_location_folder_dialog)
        self.project_location_folder_dialog.clicked.connect(
            self.choose_project_location)

        # create "project name" label
        self.project_name_label = QLabel(locales.getLocale().ProjectName, self)
        new_proj_layout.addWidget(self.project_name_label)

        # create "project name" text edit
        self.project_name_text_edit = QLineEdit("", self)
        self.project_name_text_edit.setPlaceholderText(locales.getLocale().ProjectName)
        new_proj_layout.addWidget(self.project_name_text_edit)

        # create layout for opening recent or existing projects
        existing_proj_layout = QVBoxLayout()

        # Create "Open Project" button
        self.open_project_button = QPushButton(locales.getLocale().OpenProject, self)
        self.open_project_button.clicked.connect(self.open_existing_project_via_directory)

        existing_proj_layout.addWidget(self.open_project_button)

        # Create label for recent projects
        self.recent_projects_label = QLabel(locales.getLocale().RecentProjects, self)

        # Create list widget for recent projects
        self.recent_projects_list_widget = QListWidget(self)
        self.recent_projects_list_widget.itemActivated.connect(
            self.open_existing_project_in_list)
        delete_shortcut = QShortcut(QKeySequence(QtCore.Qt.Key_Delete), self.recent_projects_list_widget)
        delete_shortcut.activated.connect(self.delete_selected_item)

        # Add recent projects to list widget
        self.reload_recent_projects_list()
        existing_proj_layout.addWidget(self.recent_projects_label)
        existing_proj_layout.addWidget(self.recent_projects_list_widget)

        layout = QHBoxLayout()
        # left part is to create new project
        new_proj_layout.setContentsMargins(0, 0, 0, 0)
        new_proj_layout_widget = QWidget()
        new_proj_layout_widget.setMaximumWidth(300)
        new_proj_layout_widget.setLayout(new_proj_layout)

        layout.addWidget(new_proj_layout_widget)

        # right part is to open existing project
        layout.addLayout(existing_proj_layout)

        self.setLayout(layout)
        self.show()

    def reload_recent_projects_list(self):
        # Add recent projects to list widget
        self.recent_projects = self.load_recent_projects()
        self.recent_projects_list_widget.clear()
        self.add_recent_projects_in_list()

    def delete_selected_item(self):
        selected_item = self.recent_projects_list_widget.currentItem()
        if selected_item:
            row = self.recent_projects_list_widget.row(selected_item)
            del self.recent_projects[row]

            self.save_recent_projects()
            self.reload_recent_projects_list()

    def add_recent_projects_in_list(self):
        for _, p in enumerate(self.recent_projects):
            text = "<b>" + os.path.basename(p) + "</b><br>" + p
            label = QLabel(text)
            label.setStyleSheet("background-color: rgba(255, 255, 255, 0);")

            item = QListWidgetItem()
            self.recent_projects_list_widget.addItem(item)
            self.recent_projects_list_widget.setItemWidget(item, label)
            self.adjust_item_height(item)

    def choose_project_location(self):
        file = str(QFileDialog.getExistingDirectory(self, locales.getLocale().ChooseFolder))
        if not file:
            return
        
        # update latest project root
        settings = QSettings('Epit3D', 'Spycer')
        settings.setValue('latest-project-root', file)

        self.project_directory_edit.setText(file)

    def load_recent_projects(self) -> List[str]:
        settings = QSettings('Epit3D', 'Spycer')

        if settings.contains('recent_projects'):
            projects = settings.value('recent_projects', type=list)

            # filter projects which do not exist
            import pathlib
            projects = [p for p in projects if pathlib.Path(p).exists()]

            number_of_recent_projects = 10
            return projects[:number_of_recent_projects]

        return []
    
    def load_recent_projects_root(self) -> str:
        # returns latest directory for projects
        settings = QSettings('Epit3D', 'Spycer')

        if settings.contains('latest-project-root'):
            return settings.value('latest-project-root', type=str)
        
        return ""

    def create_new_project(self):
        print("Creating new project...")
        # check if project name is empty
        if self.project_name_text_edit.text() == "":
            showErrorDialog(locales.getLocale().ProjectNameCannotBeEmpty)
            return

        # check if project location is empty
        if self.project_directory_edit.text() == "":
            showErrorDialog(locales.getLocale().ProjectLocationCannotBeEmpty)
            return

        import pathlib

        full_path = pathlib.Path(
            self.project_directory_edit.text(), self.project_name_text_edit.text())
        print(full_path)

        # check if project already exists
        if full_path.exists():
            showErrorDialog(locales.getLocale().ProjectAlreadyExists)
            return

        # add current project to recent projects
        self.add_recent_project(full_path)
        
        # create project directory
        full_path.mkdir(parents=True, exist_ok=True)

        # emit signal with path to project file
        self.create_project_signal.emit(str(full_path))

    def add_recent_project(self, project_path):
        self.recent_projects.insert(0, str(project_path))
        self.save_recent_projects()

    def save_recent_projects(self):
        settings = QSettings('Epit3D', 'Spycer')
        settings.setValue('recent_projects', self.recent_projects)

    def open_existing_project_in_list(self):
        selected_project = self.recent_projects[self.recent_projects_list_widget.currentRow()]
        self.open_existing_project(selected_project)

    def open_existing_project_via_directory(self):
        if directory := str(QFileDialog.getExistingDirectory(self, locales.getLocale().ChooseFolder)):
            selected_project = directory
        else:
            # didn't choose any project, release
            return
        self.open_existing_project(selected_project)

    def open_existing_project(self, selected_project):
        print(f"Opening {selected_project}...")

        # adds recent project to system settings
        if selected_project in self.recent_projects:
            # move the project to the beginning of the list
            last_opened_project_index = self.recent_projects.index(selected_project)
            last_opened_project = self.recent_projects.pop(last_opened_project_index)
            self.recent_projects.insert(0, last_opened_project)
        else:
            # add existing project to recent projects
            self.add_recent_project(selected_project)

        if not self.сheck_project_version(selected_project):
            return

        self.save_recent_projects()
        self.reload_recent_projects_list()

        # emit signal with path to project file
        self.open_project_signal.emit(selected_project)

    def сheck_project_version(self, project_path):
        sett().project_path = project_path
        project_settings_filename = PathBuilder.settings_file()

        build_version = get_version(PathBuilder.settings_file_default())
        project_version = get_version(project_settings_filename)

        if build_version != project_version:
            locale = locales.getLocale()
            message_box = QMessageBox()
            message_box.setWindowTitle(locale.ProjectUpdate)
            message_box.setText(locale.SettingsUpdate)
            message_box.addButton(QMessageBox.Yes)
            message_box.addButton(QMessageBox.No)
            message_box.button(QMessageBox.Yes).setText(locale.Update)
            message_box.button(QMessageBox.No).setText(locale.Cancel)

            reply = message_box.exec()

            if reply == QMessageBox.Yes:
                project_settings_old_filename = PathBuilder.settings_file_old()
                shutil.copyfile(project_settings_filename, project_settings_old_filename)
                shutil.copyfile("settings.yaml", project_settings_filename)
                paths_transfer_in_settings(project_settings_old_filename, project_settings_filename)
                set_version(project_settings_filename, build_version)
                return True

            return False

        return True
