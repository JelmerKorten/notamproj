    # This file is part of NotamPlotter.

    # NotamPlotter plots notams on a streetmap.
    # Copyright (C) 2023  Jelmer Korten (korty.codes)

    # NotamPlotter is free software: you can redistribute it and/or modify
    # it under the terms of the GNU General Public License as published by
    # the Free Software Foundation, either version 3 of the License, or
    # (at your option) any later version.

    # NotamPlotter is distributed in the hope that it will be useful,
    # but WITHOUT ANY WARRANTY; without even the implied warranty of
    # MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    # GNU General Public License for more details.

    # You should have received a copy of the GNU General Public License
    # along with NotamPlotter.  If not, see <https://www.gnu.org/licenses/>.

    # Contact: korty.codes@gmail.com

#%% imports
import re
import copy
import pandas as pd
import textwrap
import arrow
from pathlib import Path
from platform import system as ps
import logging
logging.basicConfig(level=logging.DEBUG, filename="plotter.log",filemode='a', format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',  datefmt='%Y-%m-%d %H:%M:%S')
logger = logging.getLogger(__name__)

# imports for Create Circle point buffer
from shapely.geometry import Point
from pyproj import Transformer
from shapely.ops import transform

# import for plotly
import plotly.graph_objects as go

# imports for collect
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from datetime import date
import os


# imports for updating chromedriver version
import json, requests, zipfile, io
from __version__ import chromedriver_mainversion, chrome_version, install_path

# chrome_version = '115.0.5790.114'
chrome_mainversion = chrome_version.split(".")[0]


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
    logger.info("Done downloading chromedriver")
    logger.info("You'll find it in the >support< folder")
    logger.info("Giving file permissions")
    print("Done downloading chromedriver")
    print("You'll find it in the >support< folder")
    print("....")
    print("Giving permissions")
    chromedriver_path = 'support/chromedriver-mac-x64/chromedriver'
    try:
        os.chmod(chromedriver_path, 0o755)
        print("permissions given")
        logger.info("File Permissions given")
    except:
        print("unable to give permissions, program might not run")
        logger.warning("Unable to give permissions, program might not run")
    

def check_update():
    """to check if update required"""
    logger.info("running check_update")
    if chromedriver_mainversion == chrome_mainversion:
        logger.info("No need to update, mainversions are the same")
        return False
    elif chromedriver_mainversion > chrome_mainversion:
        print("uhoh, your chromedriver is a higher version than chrome")
        logger.warning("Your chromedriver is a higher than chrome, program might not run")
        return
    else:
        logger.debug("Update needed..")
        return True
    

def get_versions():
    jsonpath = 'https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions-with-downloads.json'

    my_versions = requests.get(jsonpath)
    if my_versions:
        my_versions = my_versions.json()
        with open("chromeversions.json", "w") as file:
            json.dump(my_versions, file, indent = "")

        print("Done getting new versions json")
        logger.info("Getting new versions file from github")
    else:
        print("Unable to load latest versions")
        print("Please go to chromedriver.chromium.org")
        print("To update chromedriver manually")
        logger.warning("Unable to load latest versions")
        logger.warning("Please go to chromedriver.chromium.org to update manually")
        

#%% USED HERE -- dealwithchrome()
def dealwithchrome():
    logger.info("Checking to see if we need to update chromedriver")
    if check_update():
        get_versions()
        update_chromedriver()
        


#%% USED HERE -- convert_coords(latlon)
def convert_coords(latlon: str) -> tuple:
    """Function converts coords string to decimal tuple.
    
    A function that takes a string of coords in format: 
    hhmmss.s(s)(N/S) hhhmmss.s(s)(E/W) and returns a tuple of decimal coords.
    I created this function by slicing the string multiple times.
    """

    # split
    lat, lon = latlon.split()
    

    # latitude
    hemi = lat[-1]
    if '.' in lat:
        dec_lat_sec = float(re.search(r"\d{2}\.\d+", lat).group()) / 60
        dec_lat_min = (float(re.search(r"\d+\.", lat).group()[-5:-3]) + dec_lat_sec) / 60
    else:
        # no . in lat
        dec_lat_sec = float(lat[-3:-1]) / 60
        dec_lat_min = (float(lat[-5:-3]) + dec_lat_sec) / 60
        
    lat_hrs = float(lat[:2])
    dec_lat = lat_hrs + dec_lat_min
    if hemi == "S":
        dec_lat *= -1
    

    # longitude
    side_earth = lon[-1]
    if '.' in lon:
    # dec_lon_sec = float(lon[-6:-1]) / 60
    # dec_lon_min = (float(lon[-8:-6]) + dec_lon_sec) / 60
        dec_lon_sec = float(re.search(r"\d{2}\.\d+", lon).group()) / 60
        dec_lon_min = (float(re.search(r"\d+\.", lon).group()[-5:-3]) + dec_lon_sec) / 60
    else:
        # no . in lon
        dec_lon_sec = float(lon[-3:-1]) / 60
        dec_lon_min = (float(lon[-5:-3]) + dec_lon_sec) / 60
    
    lon_hrs = float(lon[:3])
    dec_lon = lon_hrs + dec_lon_min
    if side_earth == "W":
        dec_lon *= -1

    return (dec_lat, dec_lon)


# %% USED HERE -- create_circle(latlon:tuple, radius:int (in meters)) -> list
def create_circle(latlon:tuple, radius:int) -> list:
    """To convert a single point + radius into a list of coords that will draw a circle on a map.
    Takes (lat,lon) tuple in decimal coords.
    Radius in meters."""

    # isolate lat and lon
    lat, lon = latlon[0], latlon[1]
    
    # prep projection info
    local_aeqd = f"+proj=aeqd +R=6371000 +units=m +lat_0={lat} +lon_0={lon}"
    std_wgs84 = '+proj=longlat +datum=WGS84 +no_defs'

    # create projections
    wgs84_to_aeqd = Transformer.from_proj(std_wgs84, local_aeqd)
    aeqd_to_wgs84 = Transformer.from_proj(local_aeqd, std_wgs84)

    # create center point from latlon coords
    point = Point(wgs84_to_aeqd.transform(lon, lat))
    # get the buffer with radius
    buffer = point.buffer(radius)
    # transform each point in the buffer
    circle = transform(aeqd_to_wgs84.transform, buffer)
    # create list of the points of the circle
    coords = list(circle.exterior.coords)
    # return list of tuples in (lon,lat)
    return coords



# %% TO IMPORT -- readnotams(filepath = 'notams/current_notams.csv') -> df
def readnotams(filepath = None, airports_str="omaa"):
    if filepath == None:
        today = date.today().strftime("%Y%m%d")
        filepath = f"files/{today}_notams_{airports_str}.csv"

    with open(filepath) as file:
        current_notams = file.readlines()

    for idx, line in enumerate(current_notams):
        current_notams[idx] = line.replace('\n','')
        current_notams[idx] = line.strip()

    startlines = []
    endlines = []
    for i, line in enumerate(current_notams):
        # if we can find a Q) in the line
        if (line.find('Q)') != -1):
            startlines.append(i-1)
        if "CREATED:" in line:
            endlines.append(i)
        if "End of Report" in line:
            # print("All lines scanned, End of Report found")
            
            number_of_notams = ''
            for letter in line:
                if letter.isdigit():
                    number_of_notams += letter
            number_of_notams = int(number_of_notams)
    # print(f'NOTAMs found: {number_of_notams}')


    notam_dict = {}
    for i in range(len(startlines)-1):
        notam_dict.update({current_notams[startlines[i]]: current_notams[startlines[i]+1:startlines[i+1]-1]})
    try:
        notam_dict.update({current_notams[startlines[-1]]: current_notams[startlines[-1]:endlines[-1]+1]})
    except:
        print("No Notams downloaded, unable to process. This is most likely due to the new headless feature")
        logger.debug("No Notams downloaded. Check Headless feature and rewrite access code.")
        logger.debug("exiting program")
        exit()

    choices = list(notam_dict.keys())

    for i in range(len(notam_dict[choices[0]])):
        if "F)" in notam_dict[choices[0]][i]:
            idx = i


    long_dict = {}
    for key in notam_dict.keys():
        keydict = {}
        valuedictlist = []
        f_idx = 100
        created_idx = 100
        for i in range(len(notam_dict[key])):
            if "F)" in notam_dict[key][i]:
                f_idx = i
            if "CREATED: " in notam_dict[key][i]:
                created_idx = i
        e_end = min(f_idx, created_idx)

        for i, line in enumerate(notam_dict[key]):
            
            if 'Q)' in notam_dict[key][i]:
                if 'A)' in notam_dict[key][i]:
                    q_line = notam_dict[key][i][:notam_dict[key][i].find(" A)")]
                else:
                    q_line = notam_dict[key][i]
                valuedictlist.append({'short': q_line})

            if 'A)' in notam_dict[key][i]:
                a_line = notam_dict[key][i][notam_dict[key][i].find("A)")+3:notam_dict[key][i].find("B)")-1]
                b_line = notam_dict[key][i][notam_dict[key][i].find("B)")+3:notam_dict[key][i].find("C)")-1]
                c_line = notam_dict[key][i][notam_dict[key][i].find("C)")+3:]
                
                valuedictlist.append({'icao':a_line})
                valuedictlist.append({'start_date':b_line})
                valuedictlist.append({'end_date':c_line})
                
            if 'D)' in notam_dict[key][i]:
                d_line = notam_dict[key][i][notam_dict[key][i].find("D)")+3:]
                valuedictlist.append({'times':d_line})

            if 'E)' in notam_dict[key][i]:
                e_line = notam_dict[key][i][notam_dict[key][i].find("E)")+3:]
                for idx in range(i+1,e_end):
                    e_line += " " # used to be " - "
                    e_line += notam_dict[key][idx]
                valuedictlist.append({'english': e_line})
            
            if 'F)' in notam_dict[key][i]:
                f_line = notam_dict[key][i][notam_dict[key][i].find("F)")+3:notam_dict[key][i].find("G)")-1]
                g_line = notam_dict[key][i][notam_dict[key][i].find("G)")+3:]
                valuedictlist.append({'lower': f_line})
                valuedictlist.append({'upper': g_line})


        keydict.update({key:valuedictlist})

        long_dict.update(keydict)


    long_dict2 = {}
    for key in long_dict.keys():
        result = {a:b for i in long_dict[key] for a, b in i.items()}
        long_dict2.update({key: result})
    long_dict = long_dict2.copy()

    df = pd.DataFrame.from_dict(long_dict, orient='index')



    # needs debugging in case there's 1 random weird notam
    # df['lat'] = [round(int(x[-14:-9][:2]) + (float(x[-14:-9][2:4])/60),4) if x[-10] == "N" else -1 * round((int(x[-14:-9][:2]) + float(x[-14:-9][2:4])/60),4) for x in df.short]
    # df['long'] = [round(int(x[-9:-3][:3]) + (float(x[-9:-3][3:5])/60),4) if x[-4] == "E" else -1 * round((int(x[-9:-3][:3]) + float(x[-9:-3][3:5])/60),4) for x in df.short]
    # print(df.head())
    df['coords'] = ''
    
    # textwrap
    df['wrap'] = ""
    for i in range(len(df)):
        if df.loc[df.index[i],'english']:
            df.at[df.index[i],'wrap'] = df.index[i]+"<br>"+"<br>".join(textwrap.wrap(df.loc[df.index[i],'english'],width=50))+"<br>Lower: "+str(df.loc[df.index[i],'lower'])+" -- Upper: "+str(df.loc[df.index[i],'upper'])+"<br>Dates From: "+str(df.loc[df.index[i],'start_date'])+" To: "+str(df.loc[df.index[i],'end_date'])+"<br>Times: "+str(df.loc[df.index[i],'times'])
    return df

# %% TO IMPORT -- add_polygons(df) -> df
def add_polygons(df):
    """Takes the dataframe and adds coords for anything containing 'BOUNDED', returns a new df.
    The coords returned are lon,lat to work with traces plot"""

    for i in range(len(df)):
        if "BOUNDED" in df.loc[df.index[i],'english']:
            # isolate current working data
            data = df.loc[df.index[i],'english']
            # split data
            # data = data.split(' - ')
            data = [convert_coords(x) for x in re.findall(r"\d{6}(?:\.\d+)?[NS] \d{7}(?:\.\d+)?[EW]", data)]
            # call convert_coords if the split item matches the coordstring regex
            # data = [convert_coords(x) for x in data if bool(re.search(r"\d{6}(\.\d+)?[NS]", x))]
            # swap lat,lon to lon,lat for traces plotting
            data = [(x[1],x[0]) for x in data]
            # store into coords
            df.at[df.index[i],'coords'] = data
    
    return df


# %% TO IMPORT -- add_multiple_circles(df) -> df
def add_multiple_circles(df):
    """Function to add the information on circles to be drawn
    
    This will transform some of the information from regex into usable info.
    We tranform into a radius in meters with the coords of the spot.
    """

    circle_list = []
    for i in range(len(df)):
        if "CIRCLE" in df.iloc[i].english:
            cur_list = []
            lat_matches = re.finditer(r"\d{6}(?:\.\d+)?[NS]", df.iloc[i].english)
            lat_res = [m.group() for m in lat_matches]
            lon_matches = re.finditer(r"\d{7}(?:\.\d+)?[EW]", df.iloc[i].english)
            lon_res = [m.group() for m in lon_matches]
            radius_matches = re.search(r"\bRADIUS\b\s\d+(?:\.\d+)?\s?[a-zA-Z]+\b", df.iloc[i].english).group()
            coord_matches = [lat_res[i] + " " + lon_res[i] for i in range(len(lat_res))]
            cur_list.append(radius_matches)
            cur_list.append(coord_matches)
            circle_list.append(cur_list)
        elif "PSN" in df.iloc[i].english:
            cur_list = []
            lat_matches = re.finditer(r"\d{6}(?:\.\d+)?[NS]", df.iloc[i].english)
            lat_res = [m.group() for m in lat_matches]
            lon_matches = re.finditer(r"\d{7}(?:\.\d+)?[EW]", df.iloc[i].english)
            lon_res = [m.group() for m in lon_matches]    
            coord_matches = [lat_res[i] + " " + lon_res[i] for i in range(len(lat_res))]
            # TODO: Check if RADIUS match, if True: use that, else: use 300 M
            cur_list.append('RADIUS 300 M')
            cur_list.append(coord_matches)
            circle_list.append(cur_list)
        else:
            circle_list.append("")
        
    df['circles'] = circle_list

    dist_meas_map = {"M": 1,
                    "NM": 1852,
                    "KM": 1000}

    for item in df.circles:
        if item:
            dist = re.search(r"[0-9]+(?:\.\d+)?",item[0]).group()
            dist_meas = item[0][re.search(r"[0-9]+(?:\.\d+)?",item[0]).end():].strip()
            
            dist_miles = float(dist) * dist_meas_map[dist_meas]
            item[0] = dist_miles
            coord_lst = []
            for coord_set in item[1]:
                coord_lst.append(convert_coords(coord_set))
            item[1] = coord_lst

    return df


# %% TO IMPORT -- split_circles_add_indices(df) -> df
def split_circles_add_indices(df):
    """Splits rows if multiple circles are found.
    """
    
    temp_master_data = pd.DataFrame(columns=df.columns)
    for i in range(len(df)):
        if isinstance(df.iloc[i].circles,list):
            temp_df = pd.DataFrame(columns=df.columns)
            for j in range(1,len(df.iloc[i].circles[1])+1):
                newindex = f'{df.index[i]}_{j}'
                cur_df = pd.DataFrame([df.iloc[i]], columns=df.columns, index=[newindex])

                latlon = df.iloc[i].circles[1][j-1]
                radius = df.iloc[i].circles[0]

                cur_df.at[newindex,'coords'] = create_circle(latlon, radius)
                temp_df = pd.concat([temp_df,cur_df])
            temp_master_data = pd.concat([temp_master_data,temp_df])

    indexlist = list(temp_master_data.index)

    prev_index = None
    for new_index in indexlist:
        index_to_compare = new_index.split("_")[0]
        if index_to_compare != prev_index:
            df.drop(index=index_to_compare, axis=0,inplace=True)
        prev_index = index_to_compare

    df = pd.concat([df,temp_master_data])

    return df


# %% TO IMPORT -- create_jdata(df)
def create_jdata(df):
    """To create the jdata that will make our polygon plots in plotly. Take the df and uses df.coords and df.index to get the required information.
    Returns geoJSON jdata."""

    base_jdata = {
        'type': 'FeatureCollection', 'name': 'notams',
        'features': []
    }

    base_jdata_feature = {
        'type': 'Feature',
        'properties': {
            'id': 0
        },
        'geometry': {
            'type': 'Polygon',
            'coordinates': []
        }
    }

    jdata = copy.deepcopy(base_jdata)
    for i in range(len(df)):
        if df.coords.iloc[i]:

            # print(f"i = {i}: {df.index[i]}, {df.coords.iloc[i]} ")
            feat = copy.deepcopy(base_jdata_feature)
            # print(f"this is what feat looks like\n{feat}\n")
            # overwrite the id with df.index (our notam identifier)
            feat['properties'].update({'id':df.index[i]})
            # add coords to coords, have to append cz of the [[[ needed ]]]
            feat['geometry']['coordinates'].append(df.coords.iloc[i])
            # add current coord set to total jdata to create traces
            jdata['features'].append(feat)
    
    return jdata




#%% back_traces(df,jdata) -> output/yyyymmdd_notams_fields.html
def back_traces(df,jdata,airports_str, filepath_out):
    """Takes in the df and the create jdata.
    Plots the required shapes on the plot.
    TODO: fix hovertemplates.
    TODO: fix axes not showing coords
    TODO: fix overlapping areas"""
    
    ROUTECOL = "teal" # does work
    LEG_WIDTH = 25 # does not work actually

    today = date.today()
    plottitle = today.strftime("%Y %b %d")
    plottitle += f" {airports_str}"
    fig = go.Figure(go.Choroplethmapbox(
        name='Notams',
        geojson=jdata,
        text=df['wrap'], # is printed on the left in black
        locations=df.index, # is printed on the right in white
        z = [0]*len(df), # seems to be hover text?
        featureidkey='properties.id', # has to be same as df['id']
        colorscale=[[0,'tomato'],[1,'tomato']],
        showlegend=True,
        hovertemplate =
        '%{text}',
        showscale=False,
        legendwidth=25,
        marker=dict(
            line=dict(color="red", width=1),
            opacity=0.5
        )
    ))

    fig.update_layout(
        title_text=f"Notams {plottitle}", title_x=0.5,
        width=1600,height=800,
        mapbox = {
            'style': "open-street-map",
            'center': {'lon': 54.651512, 'lat': 24.442970},
            'zoom': 9
        },
        margin = {'l':0, 'r':0, 'b':0, 't':30}
    )

    # change appearance of hoverlabel
    fig.update_layout(
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Rockwell"
        )
    )
    # add commonly used routes
    fig.add_trace(go.Scattermapbox(
        name = "aa3",
        mode = "markers+lines",
        lon = [54.2, 54.3152, 54.45, 54.5377, 54.5982, 54.660418, 54.6112, 54.5458, 54.452, 54.3143, 54.1852],
        lat = [24.3745, 24.32, 24.3437, 24.3473, 24.4047, 24.420518, 24.393, 24.3307, 24.3273, 24.3, 24.3572],
        # marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))    
    fig.add_trace(go.Scattermapbox(
        name = "aa1",
        mode = "markers+lines",
        lon = [54.589, 54.692, 54.681, 54.6604, 54.6633, 54.6732, 54.589],
        lat = [24.6345, 24.553, 24.482, 24.4205, 24.4867, 24.5515, 24.619],
        # marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))    
    fig.add_trace(go.Scattermapbox(
        name = "ad7",
        mode = "markers+lines",
        lon = [54.4572, 54.4493, 54.4033, 54.2863 ],
        lat = [24.4133, 24.3928, 24.4122, 24.4533 ],
        # marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))   
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3143, 54.144],
        lat = [24.3, 24.3187],
        # marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))  
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3152, 54.1518],
        lat = [24.32, 24.338],
        # marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))


    # create grid lines
    minlon = 53.5
    maxlon = 56.5
    minlat = 24
    maxlat = 26
    gridlon = []
    # add lines on this lon
    for i in range(int(minlon*10),int(maxlon*10)):
        gridlon += [i/10]*int((maxlat-minlat)*10)
        gridlon.append(None)
    # add different lons for same lats
    for i in range(int((maxlat-minlat)*10)):
        gridlon += [i/10 for i in range(int(minlon*10),int(maxlon*10))]
        gridlon.append(None)

    gridlat = []
    # add different lats for same lons
    for i in range(int((maxlon-minlon)*10)):
        gridlat += [i/10 for i in range(int(minlat*10),int(maxlat*10))]
        gridlat.append(None)
    # add lines on this lat
    for i in range(int(minlat*10),int(maxlat*10)):
        gridlat += [i/10]*int((maxlon-minlon)*10)
        gridlat.append(None)
    # add the grid as a trace
    fig.add_trace(go.Scattermapbox(
        name = "grid",
        mode = "lines",
        lon = gridlon,
        lat = gridlat,
        below="true",
        legendwidth=50,
        line=dict(color='lightgrey', width=1)))

    # create a trace for each thing that has coords
    # make the legend "wrap"
    for i in range(len(df)):
        if df.loc[df.index[i],'coords']:
            coords = df.loc[df.index[i],'coords']
            lon = [item[0] for item in coords]
            lat = [item[1] for item in coords]
            fig.add_trace(go.Scattermapbox(
                name = df.loc[df.index[i],'wrap'],
                mode = "lines",
                lon = lon,
                lat = lat,
                fill = "toself",
                hoverinfo="skip",
                legendwidth=0.1, # inop
                line=dict(color='tomato',width=1)))


    # write file
    fig.write_html(filepath_out, full_html=True)
    logger.info('html file created in output folder')




# %% TO IMPORT -- collect(base, airports) -> write file Collects notams
def collect(base, airports:str):
    """Gets the notams in raw format from notams.faa.gov and writes to file."""
    logger.info("running collect()")
    # updates chromedriver if needed
    dealwithchrome()
    

    # check if file doesnt exist yet
    today = date.today().strftime("%Y%m%d")
    airports = airports.replace("_", " ")
    airports_str = "_".join(airports.split(" "))

    # create output url
    FILE_URL = os.path.join(base, "files", f"{today}_notams_{airports_str}.csv")
    # url = SUBURL / f"{today}_notams_{airports_str}.csv"

    options = Options()
    # do not open an instance of google chrome
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    # get system name
    sys_name = ps()
    chromedriver_url = os.path.join(base, "support")
    
    # system dependent
    if sys_name == "Windows":
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver_win32", "chromedriver.exe")
        logger.info("running on windows")
    else:
        chromedriver_url = os.path.join(chromedriver_url, "chromedriver-mac-x64", "chromedriver")
    
    # fix needed since chrome 115
    options.binary_location = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    ser = Service(chromedriver_url)
    driver = webdriver.Chrome(service=ser, options=options)



    # navigate to site
    URL = "https://www.notams.faa.gov/dinsQueryWeb/"
    driver.get(URL)

    # click away the I Agree button for the disclaimer
    XPATH = '/html/body/div[3]/div[3]/button'
    inputElement = driver.find_element('xpath',XPATH)
    inputElement.click()

    # click RAW
    XPATH = '/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[3]/td/input[2]'
    inputElement = driver.find_element('xpath',XPATH)
    inputElement.click()

    # input selection of aerodromes
    XPATH = '/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[4]/td/textarea'
    inputElement = driver.find_element('xpath',XPATH)
    inputElement.send_keys(airports)

    # click view notams
    XPATH = '/html/body/table[3]/tbody/tr/td[1]/table/tbody/tr[1]/td/form/table/tbody/tr/td[2]/table/tbody/tr[5]/td/input[1]'
    inputElement = driver.find_element('xpath',XPATH)
    inputElement.click()

    # close current tab
    driver.close()

    # switch focus to new tab
    driver.switch_to.window(driver.window_handles[0])
    current_notams = driver.find_element('xpath',"/html/body").text
    # close tab
    driver.close()

    # write notams to file


    with open(FILE_URL, 'w') as file: # original: url,  mode: "w+"
        file.write(current_notams)
    logger.info("csv file created")

# %% TO IMPORT -- handle() file -> notams output
def handle(filepath_in=None, filepath_out=None, airports_str="omaa"):
    logger.info("running handle()")
    df = readnotams(filepath_in, airports_str)
    logger.info("Notams read.")
    df = add_polygons(df)
    logger.info("polygons added")
    df = add_multiple_circles(df)
    logger.info("multiple circles added")
    df = split_circles_add_indices(df)
    logger.info("circles split")
    jdata = create_jdata(df)
    logger.info("jdata created")
    back_traces(df,jdata,airports_str,filepath_out)


# %% TO IMPORT IN NOTAMPLOTTER -- cleanup() projectdir -> deletes files older than 5 days                
def cleanup(base, DAYS):
    """To walk through files and output dir to delete files older than DAYS days."""
    logger.info("running cleanup")
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
            # ONLY works on the creation time. Not on file name.
            if arrow.get(item.stat().st_mtime) < remove_time:
                # Remove the file
                os.remove(item)
                logger.info(f"Removing {item}")

