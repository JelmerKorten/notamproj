# HOW TO BUILD
# run: python setup.py build





from __future__ import annotations

from cx_Freeze import Executable, setup

options = {"build_exe": {"build_exe":"notamproject",
                        "excludes": ["tkinter"],
                        "include_files": ["support","output","files"]}}

executables = [
    Executable("notamplotter.py"),
]

setup(
    name="notamplotter",
    version="0.1.3",
    description="uiless script",
    executables=executables,
    options=options,
)