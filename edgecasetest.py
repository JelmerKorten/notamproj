# testing pdf reading.
import pypdf
import os
import re

FOLDER = "/Users/korty/coding/notamproj/files"
FILE = "OMAE_ValidNOTAM as of 27 JUN 2025 2122 UTC.pdf"
fullpath = os.path.join(FOLDER, FILE)
# Open the PDF file in binary read mode
# try:
#     with open(fullpath, 'rb') as file:
#         # Create a PdfReader object
#         reader = pypdf.PdfReader(file)


#         notams = []
    
#         page = reader.pages[3]
#         page = page.extract_text(extraction_mode="layout")
#         page = page.splitlines()


#         leftsplit = []
#         rightsplit = []


# # opt 1
#         for line in page:
#             print(line)
#             splits = re.split(r"\040{8,}", line)
#             print(splits)




try:
    with open(fullpath, 'rb') as file:
        # Create a PdfReader object
        reader = pypdf.PdfReader(file)


        notams = []
        for i in range(len(reader.pages)):
        # for i in range(0,2):

            page = reader.pages[i]
            page = page.extract_text(extraction_mode="layout")
            page = page.splitlines()
        
            leftsplit = []
            rightsplit = []
            disclaimer_finish = False
            for line in page:
                if not disclaimer_finish:
                    if re.search(r"^[A-Z]\d{4}\/\d{2}", line):
                        disclaimer_finish = True
                if disclaimer_finish:
                    splits = re.split(r"\040{9,}", line)
                    # print(splits)
                    if len(splits) == 1:
                        leftsplit.append(splits[0])
                    elif len(splits) == 2:
                        leftsplit.append(splits[0])
                        rightsplit.append(splits[1])
            
            notams.append(leftsplit)
            notams.append(rightsplit)
        

except FileNotFoundError:
    print("Error: 'your_document.pdf' not found. Please ensure the file exists.")
except Exception as e:
    print(f"An error occurred: {e}")

# exit()


notams_cleaned = []
currentnotam = []
has_started = False
for line in notams:
    for item in line:    
        if item == "":
            continue
        elif item.startswith("As of"):
            continue
        elif re.match(r"^\d{,3}$", item):
            continue
        elif re.search(r"^[A-Z]\d{4}\/\d{2}", item):
            has_started = True
            if len(currentnotam) > 2:
                notams_cleaned.append(currentnotam)
                currentnotam = []
        if has_started:
            currentnotam.append(item)
if len(currentnotam) > 2:
    notams_cleaned.append(currentnotam)

# print(notams_cleaned)
print(f"total notams found: {len(notams_cleaned)}")

with open("files/test.csv", "w") as file:
    for notam in notams_cleaned:
        for line in notam:
            file.write(line)
            file.write("\n")
        file.write("\n")
        
