# Trying to add axis on X and Y with current coords of the view
# Probably will require some function to calculate \
# the current left side x and right side x
# then create an axis based on that, somehow.


## NOTE: Scroll does not seem to work on Safari
## Works fine when opened with Chrome

# imports
import notam_util as nu
from datetime import date

# import for plotly
import plotly.graph_objects as go


df = nu.readnotams(None)
df = nu.add_polygons(df)
df = nu.add_multiple_circles(df)
df = nu.split_circles_add_indices(df)
jdata = nu.create_jdata(df)

#%% back_trace(df,jdata) -> output/notamsyyyymmdd.html
def back_traces(df,jdata):
    """Takes in the df and the create jdata.
    Plots the required shapes on the plot.
    TODO: fix hovertemplates.
    TODO: fix axes not showing coords
    TODO: fix overlapping areas"""
    
    ROUTECOL = "teal"
    LEG_WIDTH = 50 # Actually based on widest legend name as per df['wrap']
                    # Which is 50 as per wrap, should be fine with big screen

    today = date.today()
    plottitle = today.strftime("%Y %b %d")
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
        legendwidth=LEG_WIDTH,
        marker=dict(
            line=dict(color="red", width=1),
            opacity=0.5
        )
    ))

    fig.update_layout(
        title_text=f"Notams {plottitle}", title_x=0.5,
        width=1400,height=680,
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
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))    
    fig.add_trace(go.Scattermapbox(
        name = "aa1",
        mode = "markers+lines",
        lon = [54.589, 54.692, 54.681, 54.6604, 54.6633, 54.6732, 54.589],
        lat = [24.6345, 24.553, 24.482, 24.4205, 24.4867, 24.5515, 24.619],
        marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))    
    fig.add_trace(go.Scattermapbox(
        name = "ad7",
        mode = "markers+lines",
        lon = [54.4572, 54.4493, 54.4033, 54.2863 ],
        lat = [24.4133, 24.3928, 24.4122, 24.4533 ],
        marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))   
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3143, 54.144],
        lat = [24.3, 24.3187],
        marker = {'size': 8},
        legendwidth=LEG_WIDTH,
        line=dict(color=ROUTECOL)))  
    fig.add_trace(go.Scattermapbox(
        name = "aa3_dab",
        mode = "markers+lines",
        lon = [54.3152, 54.1518],
        lat = [24.32, 24.338],
        marker = {'size': 8},
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
        legendwidth=LEG_WIDTH,
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
                legendwidth=LEG_WIDTH, # inop
                line=dict(color='tomato',width=1)))



    # filename = today.strftime("%Y%m%d")
    fig.write_html(f'axis_test.html', full_html=True)
    # fig.show()

counter = 0
for i in range(len(df)):
    if df.iloc[i].wrap != "":
        counter += 1

print(f"len: {len(df)}, counter: {counter}")

back_traces(df,jdata)