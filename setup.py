from __future__ import annotations

from cx_Freeze import Executable, setup

options = {"build_exe": {"excludes": ["tkinter"]}}

executables = [
    Executable("clean_uiless.py"),
]

setup(
    name="uiless_test",
    version="0.1",
    description="Test script",
    executables=executables,
    options=options,
)