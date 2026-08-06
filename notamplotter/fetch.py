"""Fetching of raw NOTAM data.

Phase 2 (AGENT_PLAN.md): hosts the legacy fetch/collection functions from the
former ``notam_util.py`` -- :func:`collect`, :func:`alternative`,
:func:`read_gcaa_pdf` and :func:`successfull_notam_fetch`.

> Phase 3 replaces the Selenium-based :func:`collect` with a ``requests``-based
> :class:`FaaClient`; :func:`fetch_notams` is the stable entry point that will
> be re-implemented against that client.
"""

import os
import re
import time
from datetime import date
from platform import system as ps

import pypdf
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from notamplotter._logging import get_logger

logger = get_logger(__name__)

_URL = "https://www.notams.faa.gov/dinsQueryWeb/"


def fetch_notams(base, airports: str) -> None:
    """Fetch NOTAMs to the local files dir.

    Thin legacy wrapper around :func:`collect`, replaced by the FAA API client
    in Phase 3.
    """
    collect(base, airports)


def collect(base, airports: str) -> None:
    """Get raw NOTAMs from notams.faa.gov and write them to file."""
    logger.info("running collect()")
    today = date.today().strftime("%Y%m%d")
    airports = airports.replace("_", " ")
    airports_str = "_".join(airports.split(" "))

    FILE_URL = os.path.join(base, "files", f"{today}_notams_{airports_str}.csv")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    sys_name = ps()
    chromedriver_url = os.path.join(base, "support")

    if sys_name == "Windows":
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver_win32", "chromedriver.exe")
        logger.info("running on windows")
    else:
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver-mac-x64", "chromedriver")

    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ser = Service(chromedriver_url)
    driver = webdriver.Chrome(service=ser, options=options)

    driver.get(_URL)

    XPATH = "/html/body/div[3]/div[3]/button"
    input_element = driver.find_element("xpath", XPATH)
    input_element.click()

    XPATH = "/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[3]/td/input[2]"
    input_element = driver.find_element("xpath", XPATH)
    input_element.click()

    XPATH = "/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[4]/td/textarea"
    input_element = driver.find_element("xpath", XPATH)
    input_element.send_keys(airports)

    XPATH = "/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[5]/td/input[1]"
    input_element = driver.find_element("xpath", XPATH)
    input_element.click()

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    current_notams = driver.find_element("xpath", "/html/body").text
    driver.close()

    with open(FILE_URL, "w") as file:
        file.write(current_notams)
    logger.info("csv file created")


def alternative(base, filepath=None, airports: str = "omaa") -> None:
    """Fetch notams from GCAA site when the primary FAA site is not working."""
    logger.info("running alternative()")

    today = date.today().strftime("%Y%m%d")
    airports = airports.replace("_", " ")
    airports_str = "_".join(airports.split(" "))

    FOLDER_URL = os.path.join(base, "files")
    FILE_URL = os.path.join(base, "files", f"{today}_notams_{airports_str}.csv")

    try:
        os.remove(FILE_URL)
    except FileNotFoundError:
        print("file not found")
    except OSError as e:
        print("error", e)

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    sys_name = ps()
    chromedriver_url = os.path.join(base, "support")

    if sys_name == "Windows":
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver_win32", "chromedriver.exe")
        logger.info("running on windows")
    else:
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver-mac-x64", "chromedriver")

    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ser = Service(chromedriver_url)

    download_dir = os.path.join(base, "files")
    download_prefs = {"download.default_directory": download_dir, "download.prompt_for_download": False}
    options.add_experimental_option("prefs", download_prefs)
    driver = webdriver.Chrome(service=ser, options=options)

    url = "https://www.gcaa.gov.ae/en/ais/Pages/notam.aspx"
    driver.get(url)

    XPATH = """//*[@id="taskInfo"]/tbody/tr[2]/td[5]/a[2]/i"""
    input_element = driver.find_element("xpath", XPATH)
    input_element.click()

    start_time = time.time()
    START_STRING = "OMAE_ValidNOTAM"

    while time.time() - start_time < 10:
        for filename in os.listdir(FOLDER_URL):
            if filename.startswith(START_STRING) and not filename.endswith(".crdownload"):
                break
        time.sleep(1)

    driver.close()

    logger.info("pdf file downloaded")


def read_gcaa_pdf(base) -> str:
    """Parse the latest ``OMAE*`` PDF in the files dir and write a CSV."""
    folder = os.path.join(base, "files")
    files = os.listdir(folder)
    paths = [os.path.join(folder, basename) for basename in files if basename.startswith("OMAE")]
    latest_pdf = max(paths, key=os.path.getmtime)

    try:
        with open(latest_pdf, "rb") as file:
            reader = pypdf.PdfReader(file)

            notams = []
            for i in range(len(reader.pages)):
                page = reader.pages[i]
                page = page.extract_text(extraction_mode="layout")
                page = page.splitlines()

                leftsplit = []
                rightsplit = []
                disclaimer_finish = False
                for line in page:
                    if not disclaimer_finish:
                        if re_match_serial(line):
                            disclaimer_finish = True
                    if disclaimer_finish:
                        splits = re.split(r"\040{9,}", line)
                        if len(splits) == 1:
                            leftsplit.append(splits[0])
                        elif len(splits) == 2:
                            leftsplit.append(splits[0])
                            rightsplit.append(splits[1])

                notams.append(leftsplit)
                notams.append(rightsplit)

    except FileNotFoundError:
        print(f"Error: '{latest_pdf}' not found. Please ensure the file exists.")
    except Exception as e:
        print(f"An error occurred: {e}")

    notams_cleaned = []
    currentnotam = []
    has_started = False
    for lines in notams:
        for item in lines:
            if item == "":
                continue
            elif item.startswith("As of"):
                continue
            elif re.match(r"^\d{,3}$", item):
                continue
            elif re_match_serial(item):
                has_started = True
                if len(currentnotam) > 2:
                    notams_cleaned.append(currentnotam)
                    currentnotam = []
            if has_started:
                currentnotam.append(item)
    if len(currentnotam) > 2:
        notams_cleaned.append(currentnotam)

    print(f"total notams found: {len(notams_cleaned)}")
    today = date.today().strftime("%Y%m%d")
    newfilename = os.path.join(folder, f"OMAE_notams_{today}.csv")

    with open(newfilename, "w") as file:
        for notam in notams_cleaned:
            for line in notam:
                file.write(line)
                file.write("\n")
            file.write("\n")

    return newfilename


def successfull_notam_fetch(filepath=None, airports_str="omaa_omae_omad_omam") -> bool:
    """Return True if the fetched NOTAM file does not contain an invalid query."""
    if filepath is None:
        today = date.today().strftime("%Y%m%d")
        filepath = f"files/{today}_notams_{airports_str}.csv"
    try:
        with open(filepath) as file:
            current_notams = file.readlines()
    except FileNotFoundError:
        return False

    for line in current_notams:
        if "Invalid Query Request" in line:
            return False
    return True


def re_match_serial(text: str) -> bool:
    """Return True if ``text`` looks like a NOTAM serial line (e.g. ``A1718/25``)."""
    return bool(re.match(r"^[A-Z]\d{4}/\d{2}", text))
