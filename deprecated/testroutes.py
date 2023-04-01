# import for plotly
import plotly.graph_objects as go

# import for date
from datetime import date
# import notam util
import notam_util as nu


def create_traces_plot_route(df,jdata):
    """Takes in the df and the create jdata.
    Plots the required shapes on the plot.
    TODO: fix hovertemplates.
    TODO: fix axes not showing coords
    TODO: fix overlapping areas"""

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
        marker=dict(
            line=dict(color="red", width=1),
            opacity=0.5
        )
    ))

    fig.update_layout(
        title_text="Notams", title_x=0.5,
        width=1536,height=864,
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
        marker = {'size': 8},
        line=dict(color='tomato')))    
    fig.add_trace(go.Scattermapbox(
        name = "aa1",
        mode = "markers+lines",
        lon = [54.589, 54.692, 54.681, 54.6604, 54.6633, 54.6732, 54.589],
        lat = [24.6345, 24.553, 24.482, 24.4205, 24.4867, 24.5515, 24.619],
        marker = {'size': 8},
        line=dict(color='tomato')))    
    fig.add_trace(go.Scattermapbox(
        name = "ad7",
        mode = "markers+lines",
        lon = [54.4572, 54.4493, 54.4033, 54.2863 ],
        lat = [24.4133, 24.3928, 24.4122, 24.4533 ],
        marker = {'size': 8},
        line=dict(color='tomato')))   
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3143, 54.144],
        lat = [24.3, 24.3187],
        marker = {'size': 8},
        line=dict(color='tomato')))  
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3152, 54.1518],
        lat = [24.32, 24.338],
        marker = {'size': 8},
        line=dict(color='tomato'))) 

    today = date.today()
    today = today.strftime("%Y%m%d")
    fig.write_html(f'output/{today}.html', full_html=True)


df = nu.readnotams(None)
df = nu.add_polygons(df)
df = nu.add_multiple_circles(df)
df = nu.split_circles_add_indices(df)
jdata = nu.create_jdata(df)
create_traces_plot_route(df,jdata)

import re
def convert_coords(latlon: str) -> tuple:
    """Function converts coords string to decimal tuple.
    
    A function that takes a string of coords in format: 
    hhmmss.s(s)(N/S) hhhmmss.s(s)(E/W) and returns a tuple of decimal coords.
    I created this function by slicing the string multiple times.
    """

    # split
    lat, lon = latlon.split()
    #2423.58N 05436.67E 
    # lat = 2423
    x1 = lat[:4]
    x2 = f"{float(lat[-3:-1])/100*60:04.1f}"
    x3 = lat[-1]
    lat = x1+x2+x3
    # print(lat)

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
    
    
    x1 = lon[:5]
    x2 = f"{float(lon[-3:-1])/100*60:04.1f}"
    x3 = lon[-1]
    lon = x1+x2+x3
    # print(lon)
    
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

    return (round(dec_lat,4), round(dec_lon,4))



# routes
aa1in = ['2429.20N 05439.80E', '2433.09N 05440.39E', '2437.14N 05435.34E']
aa1out = ['2428.92N 05440.86E','2433.18N 05441.52E','2438.07N 05435.34E']
aa3in_bah = ['2423.58N 05436.67E','2419.84N 05432.75E','2419.64N 05427.12E','2418.00N 05418.86E','2421.43N 05411.11E']
aa3in_dab = ['2418.00N 05418.86E','2419.12N 05408.64E']
ad7in = ['2424.80N 05427.43E','2423.57N 05426.96E','2424.73N 05424.20E','2427.20N 05417.18E']
aa3out = ['2424.28N 05435.89E','2420.84N 05432.26E','2420.62N 05427.00E','2419.20N 05418.91E','2422.47N 05412.00E']
aa3out_dab = ['2419.20N 05418.91E','2420.28N 05409.11E']

for x in aa1out:
    print(convert_coords(x))
# 24.420518, 54.660418