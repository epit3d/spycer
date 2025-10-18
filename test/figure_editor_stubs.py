import sys
import types

# Stubs for non-Qt dependencies used by FigureEditor

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
