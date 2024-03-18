import sys

from PyQt5.QtWidgets import (
    QApplication,
)

from src.settings_widget import SettingsWidget
from src.settings import load_settings, sett


if __name__ == "__main__":
    app = QApplication(sys.argv)

    load_settings("settings.yaml")

    widget = SettingsWidget(settings_provider=sett).with_all()

    widget.show()

    sys.exit(app.exec_())
