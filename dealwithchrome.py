import json, os, requests, zipfile, io

# get my chrome version
chrome_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

chrome_version = os.popen(f"{chrome_path} --version").read().strip('Google Chrome ').strip()

# my_version = '115.0.5790.114'
chrome_mainversion = chrome_version.split(".")[0]

def check_update():
    """to check if update required"""
    

    # # get my chrome version
    # chrome_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"

    # chrome_version = os.popen(f"{chrome_path} --version").read().strip('Google Chrome ').strip()

    # # my_version = '115.0.5790.114'
    # chrome_mainversion = chrome_version.split(".")[0]


    # get chromedriver version
    # chromedriver_version = 113.0.5672.63
    chromedriver_path = 'support/chromedriver_mac64/chromedriver'
    chromedriver_version = os.popen(f"{chromedriver_path} --version").read().split()[1]
    
    chromedriver_mainversion = chromedriver_version.split(".")[0]


    if chromedriver_mainversion == chrome_mainversion:
        return False
    elif chromedriver_mainversion > chrome_mainversion:
        print("uhoh, your chromedriver is a higher version than chrome")
        return
    else:
        return True
    

def get_versions():
    jsonpath = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'

    my_versions = requests.get(jsonpath)
    if my_versions:
        my_versions = my_versions.json()
        with open("chromeversions.json", "w") as file:
            json.dump(my_versions, file, indent = "")

        print("Done getting new versions json")
    else:
        print("Unable to load latest versions")
        print("Please go to chromedriver.chromium.org")
        print("To update chromedriver manually")


def update_chromedriver():
    with open("chromeversions.json", "r") as file:
        dct = json.load(file)

    for item in dct['channels']['Stable']['downloads']['chromedriver']:
        if item['platform'] == 'mac-x64':
            if chrome_mainversion in item['url']:
                zip_file_url = item['url']
            
    r = requests.get(zip_file_url)
    if r.ok:
        z = zipfile.ZipFile(io.BytesIO(r.content))
        z.extractall("support")
    print("Done downloading chromedriver")
    print("You'll find it in the >support< folder")


if check_update():
    get_versions()
    update_chromedriver()
    




