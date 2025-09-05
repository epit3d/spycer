import sys
import types

import qt_stubs  # noqa: F401

# Ensure real SettingsWidget can be imported even if previous tests stubbed it
sys.modules.pop("src.settings_widget", None)

# Stub vtk dependency
vtk = types.ModuleType("vtk")


class vtkNamedColors:
    def GetColor3d(self, key):
        return (0, 0, 0)


vtk.vtkNamedColors = vtkNamedColors
sys.modules["vtk"] = vtk

# Stub Qt utility helpers
qt_utils_stub = types.ModuleType("src.qt_utils")
qt_utils_stub.ClickableLineEdit = qt_stubs.QLineEdit
qt_utils_stub.LineEdit = qt_stubs.QLineEdit
sys.modules["src.qt_utils"] = qt_utils_stub

# Stub settings module used by SettingsWidget
settings_module = sys.modules.get("src.settings", types.ModuleType("src.settings"))


class Settings:
    def __init__(self, data=None):
        if data is None:
            data = {}
        for k, v in data.items():
            if isinstance(v, dict):
                v = Settings(v)
            setattr(self, k, v)


settings_module.Settings = Settings
settings_module.read_settings = lambda filename=None: {"slicing": {"fill_density": 0}}
settings_module.APP_PATH = ""
sys.modules["src.settings"] = settings_module

# Stub locales expected by SettingsWidget
locales_module = types.ModuleType("src.locales")


class Locale:
    GroupNames = {}
    Settings = "Settings"
    FillDensity = "Fill Density"

    def __getattr__(self, item):
        return item


locales_module.Locale = Locale
locales_module.getLocale = lambda: Locale()
sys.modules["src.locales"] = locales_module
