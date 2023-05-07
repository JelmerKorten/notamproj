# imports
import notam_util as nu
from datetime import date
import os
from pathlib import Path
import arrow
                
def cleanup(DAYS):
    # Get path, so that we can dynamically create the file paths
    # for current OS
    path = os.getcwd()
    # Folders to check
    folders = ['files', 'output']
    # Set the time from when to remove
    remove_time = arrow.now().shift(days=-DAYS)
    for folder in folders:
        # Join path of folders with cwd
        folder_path = os.path.join(path, folder)
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
    nu.cleanup(days = 5)
    
    # Fetch days
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    url = f"files/{today_str}.csv"
    output = f"output/{today_str}_notams.html"
    if os.path.isfile(output):
        quit()
    elif os.path.isfile(url):
        nu.handle()
    else:
        nu.collect("omaa")
        nu.handle()

if __name__ == "__main__":
    main()