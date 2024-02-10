'''Version info'''
__version__ = "0.1.3"
name = "Notamplotter"
description = "Plots notams on an interactive standalone .html"
authors = ["Jelmer Korten", "korty.codes"]
license = "GNU GPL3"
readme = "README.md"

import requests
import zipfile
import json
import io
import os
import logging
logging.basicConfig(level=logging.DEBUG, filename="plotter.log",filemode='a', format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)
# google chrome version
install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
chrome_version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip()
print(chrome_version)
logger.info(f"Current Chrome version: {chrome_version}")
chrome_mainversion = chrome_version.split(".")[0]

def update_chromedriver():
    
    with open("chromeversions.json", "r") as file:
        dct = json.load(file)

    for item in dct['channels']['Stable']['downloads']['chromedriver']:
        if item['platform'] == 'mac-x64':
            if chrome_mainversion in item['url']:
                zip_file_url = item['url']
            
    r = requests.get(zip_file_url)
    if r.ok:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall("support")
    logger.info("Done downloading chromedriver")
    logger.info("You'll find it in the >support< folder")
    logger.info("Giving file permissions")
    print("Done downloading chromedriver")
    print("You'll find it in the >support< folder")
    print("....")
    print("Giving permissions")
    chromedriver_path = 'support/chromedriver-mac-x64/chromedriver'
    try:
        os.chmod(chromedriver_path, 0o755)
        print("permissions given")
        logger.info("File Permissions given")
    except:
        print("unable to give permissions, program might not run")
        logger.warning("Unable to give permissions, program might not run")
    

def check_update():
    """to check if update required"""
    logger.info("running check_update")
    if chromedriver_mainversion == chrome_mainversion:
        logger.info("No need to update, mainversions are the same")
        return False
    elif chromedriver_mainversion > chrome_mainversion:
        print("uhoh, your chromedriver is a higher version than chrome")
        logger.warning("Your chromedriver is a higher than chrome, program might not run")
        return
    else:
        logger.debug("Update needed..")
        return True
    

def get_versions():
    jsonpath = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'

    my_versions = requests.get(jsonpath)
    if my_versions:
        my_versions = my_versions.json()
        with open("chromeversions.json", "w") as file:
            json.dump(my_versions, file, indent = "")

        print("Done getting new versions json")
        logger.info("Getting new versions file from github")
    else:
        print("Unable to load latest versions")
        print("Please go to chromedriver.chromium.org")
        print("To update chromedriver manually")
        logger.warning("Unable to load latest versions")
        logger.warning("Please go to chromedriver.chromium.org to update manually")
        




# chrome driver version
chromedriver_folder = 'support/chromedriver-mac-x64'
if not os.path.isdir(chromedriver_folder):
    os.makedirs(chromedriver_folder)
    get_versions()
    update_chromedriver()

chromedriver_path = os.path.join(chromedriver_folder, "chromedriver")
print(chromedriver_path)

chromedriver_version = os.popen(f"{chromedriver_path} --version").read().split()[1]

chromedriver_mainversion = chromedriver_version.split(".")[0]
print(chromedriver_mainversion)
logger.info(f"Current chromedriver mainversion: {chromedriver_mainversion}")




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