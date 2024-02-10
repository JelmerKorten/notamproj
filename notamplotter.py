    # NotamPlotter plots notams on a streetmap.
    # Copyright (C) 2023  Jelmer Korten (korty.codes)

    # NotamPlotter is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # NotamPlotter is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with NotamPlotter.  If not, see <https://www.gnu.org/licenses/>.

    # Contact: korty.codes@gmail.com


# imports
import notam_util as nu
from datetime import date
import os
import sys
import logging
logging.basicConfig(level=logging.DEBUG, filename="plotter.log",filemode='a', format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)


# Func to get dir of executable
def find_data_file():
    if getattr(sys, "frozen", False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        datadir = os.path.dirname(__file__)
    return datadir

ROOT = find_data_file()


# main
def main(ROOT):
    # Clean up folders to save memory
    logger.info("Calling nu.cleanup()")
    nu.cleanup(base=ROOT, DAYS=5)

    # Fetch today
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    # abu dhabi, omae fir, bateen, al dhafra
    airports = ['omaa','omae','omad','omam']
    # Files url
    airports_str = "_".join(airports)
    FILE_URL = os.path.join(ROOT, "files", f"{today_str}_notams_{airports_str}.csv")

    # Output url
    OUTPUT_FILE = os.path.join(ROOT, "output", f"{today_str}_notams_{airports_str}.html")

    if os.path.isfile(OUTPUT_FILE):
        logger.info("file already exists")
        sys.exit()
    elif os.path.isfile(FILE_URL):
        logger.info("csv alrdy exist, creating file from that")
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE, airports_str=airports_str)
    else:
        logger.info("calling nu.collect() to create .csv")
        nu.collect(base=ROOT, airports=airports_str)
        logger.info("calling nu.handle() to create .html")
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE,  airports_str=airports_str)

if __name__ == "__main__":
    main(ROOT)
    sys.exit()