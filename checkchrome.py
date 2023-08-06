import os

install_path = "/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome"
my_version = os.popen(f"{install_path} --version").read().strip('Google Chrome ').strip()
mainversion = my_version[:my_version.find(".")]
print(mainversion)

# chromedriver_path = 'support/chromedriver-mac-x64/chromedriver'
# chromedriver_location = 'support/chromedriver-mac-x64'
# os.chmod(chromedriver_path, 0o755)
# chromedriver_version = os.popen(f"{chromedriver_path} --version").read().split()[1]
# print(chromedriver_version)