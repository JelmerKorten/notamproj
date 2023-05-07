# Without UI:
# When run, finds if today plot exist
# if not, creates plot from data
# if data doesn't exist, fetches it

# Trying to add axis on X and Y with current coords of the view
# Probably will require some function to calculate \
# the current left side x and right side x
# then create an axis based on that, somehow.


## NOTE: Scroll does not seem to work on Safari
## Works fine when opened with Chrome

# imports
import notam_util as nu
from datetime import date
from os import path

def main():
    today = date.today()
    today_str = today.strftime("%Y%m%d")
    # TO CHANGE IF YOU WANT DIFFERENT AIRPORTS
    airports = "omaa omae"
    
    airports_str = "_".join(airports.split(" "))
    url = f"files/{today_str}_notams_{airports_str}.csv"
    output = f"output/{today_str}_notams_{airports_str}.html"
    if path.isfile(output):
        quit()
    elif path.isfile(url):
        nu.handle(airports_str=airports_str)
    else:
        nu.collect(airports)
        nu.handle(airports_str=airports_str)

if __name__ == "__main__":
    main()