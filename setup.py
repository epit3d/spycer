import sys
from cx_Freeze import setup, Executable

buildOptions = dict(includes=['src/'], packages=['vtkmodules'], excludes=['tkinter'])

base = None
if sys.platform == "win32":
    base = "Win32GUI"

setup(
    name="spycer",
    version="3.7",
    description="Spycer vis.",
    options=dict(build_exe=buildOptions),
    executables=[Executable("C:\l1va\spycer\main.py", base=base)])
