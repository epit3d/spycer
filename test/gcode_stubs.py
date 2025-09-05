import sys
import types
import importlib

# Stubs for heavy dependencies not required for gcode parser tests


def _prepare_transform(*args, **kwargs):
    class _Tf:
        def TransformPoint(self, pt):
            return pt

    return _Tf()


gui_utils_module = types.ModuleType("src.gui_utils")
gui_utils_module.prepareTransform = _prepare_transform
sys.modules["src.gui_utils"] = gui_utils_module
sys.modules["vtk"] = types.ModuleType("vtk")
sys.modules["stk"] = types.ModuleType("stk")

settings_module = types.ModuleType("src.settings")


class _Hardware:
    rotation_center_x = 0
    rotation_center_y = 0
    rotation_center_z = 0


class _Slicing:
    print_time = 0
    consumption_material = 0
    planes_contact_with_nozzle = ""


_settings = types.SimpleNamespace(hardware=_Hardware(), slicing=_Slicing())


def sett():
    return _settings


settings_module.sett = sett
sys.modules["src.settings"] = settings_module

src_pkg = importlib.import_module("src")
src_pkg.settings = settings_module
