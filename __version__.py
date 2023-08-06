'''Version info'''
__version__ = "0.1.2"
name = "Notamplotter"
description = "Plots notams on an interactive standalone .html"
authors = ["Jelmer Korten", "korty.codes"]
license = "GNU GPL3"
readme = "README.md"


import os

# google chrome version
install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
chrome_version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip()
print(chrome_version)

# chrome driver version
chromedriver_path = 'support/chromedriver-mac-x64/chromedriver'
chromedriver_version = os.popen(f"{chromedriver_path} --version").read().split()[1]

chromedriver_mainversion = chromedriver_version.split(".")[0]
print(chromedriver_mainversion)



# so I can remember
# Release Type
# Version Bump
# Description
# Major
# 2.X.X -> 3.0.0 (December, 2008)
# This release included breaking changes, e.g., print() became a function, integer division resulted a float rather than an integer, built-in objects like dictionaries and strings changed considerably, and many old features were removed.
# Minor
# 3.8.X -> 3.9.0 (October, 2020)
# New features and optimizations were added in this release, e.g., string methods to remove prefixes and suffixes (.removeprefix()/.removesuffix()) were added, and a new parser was implemented for CPython (the engine that compiles and executes your Python code).
# Patch
# 3.9.5 -> 3.9.6 (June, 2021)
# This release contained bug and maintenance fixes, e.g., a confusing error message was updated in the str.format() method, and the version of pip bundled with Python downloads was updated from 21.1.2 -> 21.1.3, and parts of the documentation were updated.