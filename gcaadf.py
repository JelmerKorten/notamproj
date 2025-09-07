# imports
import pandas as pd
import os
from datetime import date
import textwrap
import re

def readgcaacsv(filepath = None):
    today = date.today().strftime("%Y%m%d")

    with open(filepath) as file:
        notams = file.readlines()
    
    for idx, line in enumerate(notams):
        # delete newlines and trailing spaces
        notams[idx] = line.replace("\n", "").strip()
    
    notam_dict = {}
    # dict layout:
    # {A1000/00: notams}

    # long dict layout:
    # {A1000/00: {  Q:abc,
    #               A: abc,
    #               B: abc,
    #               C: abc,
    #               D: abc,
    #               E: abc,
    #               F: abc,
    #               G: abc}}

    current_notam = {}
    prevkey = False
    currentline = ""
    currentkey = ""
    for line in notams:
        if re.search(r"^[A-Z]\d{4}\/\d{2}", line):
            name = line
            endfound = False
            # current_notam.update({name:{}})
        elif line.startswith("Q)"):
            current_notam.update({"short":line[2:]})
            currentkey = "Q"
            currentline = ""
        elif line.startswith("A)"):
            icao = line
            current_notam.update({"icao":line[2:]})
            currentkey = "A"
            currentline = ""
        elif line.startswith("B)"):
            start_date = line
            current_notam.update({"start_date":line[2:]})
            currentkey = "B"
            currentline = ""
        elif line.startswith("C)"):
            end_date = line
            current_notam.update({"end_date":line[2:]})
            currentkey = "C"
            currentline = ""
        elif line.startswith("D)"):
            times = line
            current_notam.update({"times":line[2:]})
            currentkey = "D"
            currentline = ""
        elif line.startswith("E)"):
            english = True
            # current_notam.update({"english":line[2:]})
            currentkey = "E"
            englishline = line[2:]
        elif line.startswith("F)"):
            if english:
                current_notam.update({"english": englishline})
                english = False
            lower = line
            current_notam.update({"lower":line[2:]})
            currentkey = "F"
            currentline = ""
        elif line.startswith("G)"):
            upper = line
            current_notam.update({"upper":line[2:]})
            currentkey = "G"
            currentline = ""
        elif line == "":
            endfound = True
        else: # none of the above are true, so we're still on the previous key
            englishline += f" {line}"
        
    
        if endfound:
            if english:
                current_notam.update({"english": englishline})
            # print(current_notam)
            notam_dict.update({name:current_notam})
            current_notam = {}
            # print(notam_dict)


    notam_dict.update(current_notam)

    for k,v in notam_dict.items():
        print(f"name {k}")
        print(v)
        print()


    # print(notams)


readgcaacsv("files/test.csv")