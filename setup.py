# HOW TO BUILD
# run: python setup.py build





from __future__ import annotations

from cx_Freeze import Executable, setup

options = {"build_exe": {"build_exe":"notamproject",
                        "excludes": ["tkinter"],
                        "include_files": ["support","output","files"]}}

executables = [
    Executable("clean_uiless.py"),
]

setup(
    name="uiless_test",
    version="0.1",
    description="uiless script",
    executables=executables,
    options=options,
)