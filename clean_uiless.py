# imports
import notam_util as nu
from datetime import date
import os
# from pathlib import Path
# import arrow
import sys

# create a base:
# ROOT = Path(__file__).parent.resolve()
# FILES = ROOT / "files"
# my_file = FILES / "my_filename.txt"
# print(my_file)


def find_data_file():
    if getattr(sys, "frozen", False):
        # The application is frozen
        datadir = os.path.dirname(sys.executable)
    else:
        # The application is not frozen
        # Change this bit to match where you store your data files:
        datadir = os.path.dirname(__file__)
    return datadir

ROOT = find_data_file()
print("baseurl from find datafile ", ROOT)



# my_file.touch()

# with my_file.open("w") as file:
#     ...

# base = os.path.dirname(os.path.abspath(__file__))

def main(ROOT):
    # Clean up folders to save memory
    nu.cleanup(base=ROOT, DAYS=5)
    print(ROOT)
    print(__file__)
    # Fetch today
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    # abu dhabi, omae fir, bateen, al dhafra
    airports = ['omaa','omae','omad','omam']
    # Files url
    airports_str = "_".join(airports)
    FILES = os.path.join(ROOT,"files")
    FILE_URL = os.path.join(FILES, f"{today_str}_notams_{airports_str}.csv")
    # url = os.path.join(url, f"{today_str}_notams_{airports_str}.csv")
    # Output url
    OUTPUT = os.path.join(ROOT, "output")
    OUTPUT_FILE = os.path.join(OUTPUT, f"{today_str}_notams_{airports_str}.html")
    # output = os.path.join(base, "output")
    # output = os.path.join(output, f"{today_str}_notams_{airports_str}.html")
    
    
    if os.path.isfile(OUTPUT_FILE):
        sys.exit()
    elif os.path.isfile(FILE_URL):
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE, airports_str=airports_str)
    else:
        nu.collect(base=ROOT, airports=airports_str)
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE,  airports_str=airports_str)

if __name__ == "__main__":
    main(ROOT)
    sys.exit()