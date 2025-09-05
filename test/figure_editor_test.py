import unittest

import qt_stubs  # noqa: F401
import figure_editor_stubs  # noqa: F401

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
