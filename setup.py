    # Notamplotter, plots notams on a streetmap.
    # Copyright (C) 2023  Jelmer Korten (korty.codes)

    # This program is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # This program is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with this program.  If not, see <https://www.gnu.org/licenses/>.

    # Contact: korty.codes@gmail.com


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
    version="0.1.4",
    description="uiless script",
    executables=executables,
    options=options,
)