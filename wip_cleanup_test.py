# imports
import notam_util as nu
from datetime import date
import time
import os
from pathlib import Path
import arrow
                
def arrow_cleanup(path, DAYS):
    remove_time = arrow.now().shift(days=-DAYS)
    for item in Path(path).glob("*_notams*"):
        if item.is_file():
            print(str(item.absolute()))
            if arrow.get(item.stat().st_mtime) < remove_time:
                # remove the file
                os.remove(item)
                print(f"To remove: {item}")
        


def main():
    path = os.getcwd()
    print(path)
    folders = ['files', 'output']
    for folder in folders:
        folder_path = os.path.join(path, folder)
        print(folder_path)
        print(os.listdir(folder_path))
        arrow_cleanup(folder_path, 5)
    
    # today = date.today()
    # today_str = today.strftime("%Y%m%d")
    # url = f"files/{today_str}.csv"
    # output = f"output/{today_str}_notams.html"
    # if os.path.isfile(output):
    #     quit()
    # elif os.path.isfile(url):
    #     nu.handle()
    # else:
    #     nu.collect("omaa")
    #     nu.handle()

if __name__ == "__main__":
    main()