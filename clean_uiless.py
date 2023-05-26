# imports
import notam_util as nu
from datetime import date
import os
from pathlib import Path
import arrow
import sys

base = os.path.dirname(os.path.abspath(__file__))

def cleanup(DAYS):
    # Get path, so that we can dynamically create the file paths
    # for current OS
    # path = os.getcwd()
    
    # Folders to check
    folders = ['files', 'output']
    # Set the time from when to remove
    remove_time = arrow.now().shift(days=-DAYS)
    for folder in folders:
        # Join path of folders with cwd
        folder_path = os.path.join(base, folder)
        # For item in path that has _notams
        for item in Path(folder_path).glob("*_notams*"):
            # Double check if it's a file and not a directory
            if not item.is_file():
                continue
            # Check if creation time of that file is more than DAYS days away
            if arrow.get(item.stat().st_mtime) < remove_time:
                # Remove the file
                os.remove(item)
        


def main():
    # Clean up folders to save memory
    nu.cleanup(5)
    
    # Fetch today
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    # abu dhabi, omae fir, bateen, al dhafra
    airports = ['omaa','omae','omad','omam']
    # Files url
    airports_str = "_".join(airports)
    url = os.path.join(base, f"files/{today_str}_notams_{airports_str}.csv")
    # Output url
    output = os.path.join(base, f"output/{today_str}_notams_{airports_str}.html")
    
    
    if os.path.isfile(output):
        sys.exit()
    elif os.path.isfile(url):
        nu.handle(filepath_in=url, filepath_out=output ,airports_str=airports_str)
    else:
        nu.collect(airports=airports_str)
        nu.handle(filepath_in=url, filepath_out=output, airports_str=airports_str)

if __name__ == "__main__":
    main()
    sys.exit()