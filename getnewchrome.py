# import requests, zipfile, io, json





# jsonpath = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'

# my_versions = requests.get(jsonpath)
# if my_versions:
#     my_versions = my_versions.json()
#     with open("chromeversions.json", "w") as file:
#         json.dump(my_versions, file, indent = "")

# print("all done")
    
    


# # version = '115.0.5790.102'
# # zip_file_url = f"https://edgedl.me.gvt1.com/edgedl/chrome/chrome-for-testing/{version}/mac-x64/chrome-mac-x64.zip"

# # r = requests.get(zip_file_url)
# # if r.ok:
# #     z = zipfile.ZipFile(io.BytesIO(r.content))
# #     z.extractall("support")
# # print("All done")