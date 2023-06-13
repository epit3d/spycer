import os
import yaml
from . import http, printer


class Settings:
    def __init__(self, d):
        self._attrNames = d.keys()
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)

    def asdict(self):
        res = {}
        for attrName in self._attrNames:
            attr = getattr(self, attrName)
            if isinstance(attr, Settings):
                res[attrName] = attr.asdict()
            else:
                res[attrName] = attr
        return res


class Manager:
    _filename = "printer.yaml"

    def __init__(self):
        if self.settingsFileExists():
            self.loadSettingsFromFile()
        else:
            self.loadDefaultSettings()
            self.saveSettings()

    def settingsFileExists(self):
        return os.path.exists(self._filename)

    def loadSettingsFromFile(self):
        with open(self._filename) as f:
            data = yaml.safe_load(f)
            print(data)
            self._settings = Settings(data)

    def loadDefaultSettings(self):
        # collect here default settings from submodules
        data = {}
        data.update(http.defaultSettings())
        data.update(printer.defaultSettings())
        self._settings = Settings(data)

    def saveSettings(self):
        with open(self._filename, 'w') as f:
            data = self._settings.asdict()
            # yaml.dump(data, f, default_flow_style=False)
            yaml.dump(data, f)

    def getSettings(self):
        return self._settings
