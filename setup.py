import sys
from cx_Freeze import setup, Executable

setup(
    name = "spycer",
    version = "3.6",
    description = "Spycer vis.",
    executables = [Executable("C:\l1va\spycer\STLVisualizer.py", base = "Win32GUI")])

