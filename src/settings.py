import os
import sys
import tempfile as tmp
from os import path
import shutil

import yaml
import vtk

_sett = None  # do not forget to load_settings() at start


def sett():
    return _sett


_colors = {}  # Available colors: https://en.wikipedia.org/wiki/File:SVG_Recognized_color_keyword_names.svg
_vtk_colors = vtk.vtkNamedColors()


def get_color(key):
    if key in _colors:
        return _colors[key]
    val = _vtk_colors.GetColor3d(key)
    _colors[key] = val
    return val


def load_settings():
    settings_filename = "settings.yaml"
    temp_dir = tmp.gettempdir()

    try:
        bundle_path = sys._MEIPASS
        if not path.exists(path.join(temp_dir, "spycer", settings_filename)):
            # settings_path = path.join(bundle_path, settings_filename)
            os.makedirs(path.join(temp_dir, "spycer"), exist_ok=True)
            shutil.copyfile(path.join(bundle_path, settings_filename),
                            path.join(path.join(temp_dir, "spycer", settings_filename)))
    except Exception as e:
        # print(e)
        temp_dir = path.abspath(".")

    with open(path.join(temp_dir, "spycer" if temp_dir != path.abspath(".") else "", settings_filename)) as f:
        data = yaml.safe_load(f)
        global _sett
        _sett = Settings(data)
    # print(path.join(temp_dir, "spycer", settings_filename))


def save_settings():
    temp = yaml.dump(_sett)
    temp = temp.replace("!!python/object:src.settings.Settings", "").strip()

    settings_filename = "settings.yaml"

    try:
        bundle_path = sys._MEIPASS
        path_settings = path.join(tmp.gettempdir(), "spycer", settings_filename)
    except Exception:
        path_settings = path.join(path.abspath("."), settings_filename)

    # print(path_settings)

    with open(path_settings, "w") as f:
        f.write(temp)


class Settings(object):
    def __init__(self, d):
        for a, b in d.items():
            if isinstance(b, (list, tuple)):
                setattr(self, a, [Settings(x) if isinstance(x, dict) else x for x in b])
            else:
                setattr(self, a, Settings(b) if isinstance(b, dict) else b)
