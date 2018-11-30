import sys
from cx_Freeze import setup, Executable

buildOptions = dict(includes = ['src/'])

setup(
    name = "spycer",
    version = "3.6",
    description = "Spycer vis.",
	options = dict(build_exe = buildOptions),
    executables = [Executable("C:\l1va\spycer\main.py")])#, base = "Win32GUI")])
