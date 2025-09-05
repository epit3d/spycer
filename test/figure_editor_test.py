import sys
import types
import unittest

import qt_stubs  # noqa: F401

# Stub out project-specific modules that depend on PyQt5
settings_widget_module = types.ModuleType("src.settings_widget")


class SettingsWidget:
    def __init__(self, *args, **kwargs):
        self.extra_sett_parameters = []
        self.translation = {}

    def from_settings(self, *args, **kwargs):
        return self

    def with_delete(self, *args, **kwargs):
        return self

    def with_sett(self, *args, **kwargs):
        return self


settings_widget_module.SettingsWidget = SettingsWidget
sys.modules["src.settings_widget"] = settings_widget_module

settings_module = types.ModuleType("src.settings")


def sett():
    return None


settings_module.sett = sett
sys.modules["src.settings"] = settings_module

locales_module = types.ModuleType("src.locales")
locales_module.getLocale = lambda x: x
sys.modules["src.locales"] = locales_module

# --- End stubs ---

from src.figure_editor import FigureEditor


class DummyTab:
    def __init__(self):
        self._layout = None

    def layout(self):
        return self._layout

    def setLayout(self, layout):
        self._layout = layout


class TabsStub:
    def __init__(self):
        self._tab = DummyTab()

    def widget(self, index):
        return self._tab


class FigureEditorTest(unittest.TestCase):
    def test_missing_initial_params_defaults_to_zero(self):
        tabs = TabsStub()
        params = ["length", "width"]
        constrains = [(0, 10), (0, 10)]
        initial_params = {"length": 5}  # 'width' is missing
        editor = FigureEditor(
            tabs,
            params,
            constrains,
            initial_params=initial_params,
            settings_provider=lambda: {},
        )
        self.assertEqual(editor.params_dict["length"], 5)
        self.assertEqual(editor.params_dict["width"], 0)


if __name__ == "__main__":
    unittest.main()
