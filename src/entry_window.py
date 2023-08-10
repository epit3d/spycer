import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QLabel, QListWidget, QDesktopWidget, QLineEdit, QFileDialog
from PyQt5.QtCore import QSettings

# import aligntop
from PyQt5 import QtCore
from PyQt5 import QtGui
from typing import List

from src.gui_utils import showErrorDialog
import src.locales as locales


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

    def showEvent(self, e):
        # showEvent is run when we first open and when we close project
        # when we close project and entry window pops up we need to update
        # list of projects because new project will not be included

        # update list of recent projects
        self.reload_recent_projects_list()
        
        super().showEvent(e)

    def init_ui(self):
        self.setFixedSize(600, 300)

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
        self.open_project_button.clicked.connect(self.open_existing_project)

        existing_proj_layout.addWidget(self.open_project_button)

        # Create label for recent projects
        self.recent_projects_label = QLabel(locales.getLocale().RecentProjects, self)

        # Create list widget for recent projects
        self.recent_projects_list_widget = QListWidget(self)
        self.recent_projects_list_widget.itemDoubleClicked.connect(
            self.open_existing_project)

        # Add recent projects to list widget
        self.reload_recent_projects_list()
        existing_proj_layout.addWidget(self.recent_projects_label)
        existing_proj_layout.addWidget(self.recent_projects_list_widget)

        layout = QHBoxLayout()
        # left part is to create new project
        layout.addLayout(new_proj_layout)

        # right part is to open existing project
        layout.addLayout(existing_proj_layout)

        self.setLayout(layout)
        self.show()

    def reload_recent_projects_list(self):
        # Add recent projects to list widget
        self.recent_projects = self.load_recent_projects()
        self.recent_projects_list_widget.clear()
        self.recent_projects_list_widget.addItems(self.recent_projects)

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

            return projects

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
        # adds recent project to system settings
        if project_path in self.recent_projects:
            return
        
        self.recent_projects.append(str(project_path))
        settings = QSettings('Epit3D', 'Spycer')
        settings.setValue('recent_projects', self.recent_projects)

    def open_existing_project(self):
        if self.recent_projects_list_widget.currentItem() is None:
            if directory := str(QFileDialog.getExistingDirectory(self, locales.getLocale().ChooseFolder)):
                selected_project = directory
            else:
                # didn't choose any project, release
                return
        else:
            selected_project = self.recent_projects_list_widget.currentItem().text()
        print(f"Opening {selected_project}...")

        # add existing project to recent projects
        self.add_recent_project(selected_project)

        # emit signal with path to project file
        self.open_project_signal.emit(selected_project)
