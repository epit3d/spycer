import unittest

import qt_stubs  # noqa: F401
import settings_widget_stubs  # noqa: F401

from src.settings_widget import SettingsWidget
from src.settings import Settings


class SettingsWidgetReloadTest(unittest.TestCase):
    def test_reload_repopulates(self):
        settings = Settings({"slicing": {"fill_density": 20}})
        widget = SettingsWidget(settings_provider=lambda: settings, use_grouping=False)
        widget.with_sett("fill_density")
        self.assertEqual(widget.spinbox("fill_density").value(), 20)
        settings.slicing.fill_density = 50
        widget.reload()
        self.assertEqual(widget.spinbox("fill_density").value(), 50)


if __name__ == "__main__":
    unittest.main()
