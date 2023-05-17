import sys
from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, \
    QPushButton, QLabel, QListWidget, QDesktopWidget, QLineEdit, QFileDialog
from PyQt5.QtCore import QSettings

# import aligntop
from PyQt5 import QtCore
from PyQt5 import QtGui
from typing import List

from src.gui_utils import showErrorDialog


class EntryWindow(QWidget):
    # entry window is a window that is shown before main window
    # it is used to choose between creation of new project and opening existing one

    # signal accepts path to project file
    open_project_signal = QtCore.pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle('FASP project manager')
        self.setWindowIcon(QtGui.QIcon("icon.png"))
        self.init_ui()

    def init_ui(self):
        self.setFixedSize(600, 300)

        # create layout for creating new project
        new_proj_layout = QVBoxLayout()
        new_proj_layout.setAlignment(QtCore.Qt.AlignTop)

        # Create "New Project" button
        self.new_project_button = QPushButton("New Project", self)
        self.new_project_button.clicked.connect(self.create_new_project)
        new_proj_layout.addWidget(self.new_project_button)

        # create project directory label
        self.project_directory_label = QLabel("Project directory:", self)
        new_proj_layout.addWidget(self.project_directory_label)

        # create project location label with current folder
        self.project_directory_edit = QLineEdit("", self)
        self.project_directory_edit.setPlaceholderText(
            "Choose folder for project")
        self.project_directory_edit.setReadOnly(True)
        new_proj_layout.addWidget(self.project_directory_edit)

        # create project location folder dialog
        self.project_location_folder_dialog = QPushButton(
            "Choose Folder", self)
        new_proj_layout.addWidget(self.project_location_folder_dialog)
        self.project_location_folder_dialog.clicked.connect(
            self.choose_project_location)

        # create "project name" label
        self.project_name_label = QLabel("Project Name:", self)
        new_proj_layout.addWidget(self.project_name_label)

        # create "project name" text edit
        self.project_name_text_edit = QLineEdit("", self)
        self.project_name_text_edit.setPlaceholderText("Project Name")
        new_proj_layout.addWidget(self.project_name_text_edit)

        # create layout for opening recent or existing projects
        existing_proj_layout = QVBoxLayout()

        # Create "Open Project" button
        self.open_project_button = QPushButton("Open Project", self)
        self.open_project_button.clicked.connect(self.open_existing_project)

        existing_proj_layout.addWidget(self.open_project_button)

        # Create label for recent projects
        self.recent_projects_label = QLabel("Recent Projects:", self)

        # Create list widget for recent projects
        self.recent_projects_list_widget = QListWidget(self)
        self.recent_projects_list_widget.itemDoubleClicked.connect(
            self.open_existing_project)

        # Add recent projects to list widget
        self.recent_projects = self.load_recent_projects()
        self.recent_projects_list_widget.addItems(self.recent_projects)
        existing_proj_layout.addWidget(self.recent_projects_label)
        existing_proj_layout.addWidget(self.recent_projects_list_widget)

        layout = QHBoxLayout()
        # left part is to create new project
        layout.addLayout(new_proj_layout)

        # right part is to open existing project
        layout.addLayout(existing_proj_layout)

        self.setLayout(layout)
        self.show()

    def choose_project_location(self):
        file = str(QFileDialog.getExistingDirectory(self, "Select Directory"))
        if not file:
            return

        self.project_directory_edit.setText(file)

    def load_recent_projects(self) -> List[str]:
        settings = QSettings('Epit3D', 'Spycer')

        if settings.contains('recent_projects'):
            return settings.value('recent_projects', type=list)

        return []

    def create_new_project(self):
        print("Creating new project...")
        # check if project name is empty
        if self.project_name_text_edit.text() == "":
            showErrorDialog("Project name cannot be empty")
            return

        # check if project location is empty
        if self.project_directory_edit.text() == "":
            showErrorDialog("Project location cannot be empty")
            return

        import pathlib

        full_path = pathlib.Path(
            self.project_directory_edit.text(), self.project_name_text_edit.text())
        print(full_path)

        # check if project already exists
        if full_path.exists():
            showErrorDialog("Project already exists")
            return

        # add current project to recent projects
        self.recent_projects.append(str(full_path))
        settings = QSettings('Epit3D', 'Spycer')
        settings.setValue('recent_projects', self.recent_projects)

        # create project directory
        full_path.mkdir(parents=True, exist_ok=True)

        # create project file
        with open(full_path / "project.json", "w") as project_file:
            project_file.write("{}")

        # emit signal with path to project file
        self.open_project_signal.emit(full_path)

    def open_existing_project(self):
        if self.recent_projects_list_widget.currentItem() is None:
            showErrorDialog("No project selected")
            return
        selected_project = self.recent_projects_list_widget.currentItem().text()
        print(f"Opening {selected_project}...")

        # emit signal with path to project file
        self.open_project_signal.emit(selected_project)
