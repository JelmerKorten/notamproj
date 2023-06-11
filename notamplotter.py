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

# imports
import notam_util as nu
from datetime import date
import os
import sys



# Func to get dir of executable
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


# main
def main(ROOT):
    # Clean up folders to save memory
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
        sys.exit()
    elif os.path.isfile(FILE_URL):
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE, airports_str=airports_str)
    else:
        nu.collect(base=ROOT, airports=airports_str)
        nu.handle(filepath_in=FILE_URL, filepath_out=OUTPUT_FILE,  airports_str=airports_str)

if __name__ == "__main__":
    main(ROOT)
    sys.exit()