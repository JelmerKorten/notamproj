# NotamPlotter

Creating a program which outputs a .html from scraped data.
This is for notams and should be able to work for any airport in the world that has notams pushed to notams.faa.gov

# notamui.py
This is the version of the program with a small interface. Using notamui is straight foward. Enter the required airports seperated by spaces. Click one of the buttons.

# notamplotter.py
This is without a ui, designed to run in the background and just produce the output in the folders, which can be loaded remotely. There is a built-in cleanup to delete any file with \*\_notams\_\* that is older than 5 days.


