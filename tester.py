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
    # logger.info("calling nu.cleanup()")
    # nu.cleanup(base=ROOT, DAYS=5)

    # Fetch today
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    # abu dhabi, omae fir, bateen, al dhafra
    airports = ['omaa','omae','omad','omam']
    # Files url
    airports_str = "_".join(airports)
    FILE_URL = os.path.join(ROOT, "files", f"{today_str}_notams_{airports_str}.csv")

    # Output url
    # OUTPUT_FILE = os.path.join(ROOT, "output", f"{today_str}_notams_{airports_str}.html")
    # nu.collect(base=ROOT, airports=airports_str)
    # print("faa collect ran")

    # if nu.successfull_notam_fetch(airports_str=airports_str):
    #     print("Succesfull")
    # else:
    print("running alternative")
    nu.alternative(base=ROOT, airports=airports_str)
    print("alternative ran")


if __name__ == "__main__":
    main(ROOT)
    sys.exit()