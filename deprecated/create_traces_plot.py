# with imports for this piece of code:
import plotly.graph_objects as go
from datetime import date

# %% TO IMPORT -- create_traces_plot(df,jdata)
def create_traces_plot(df,jdata):
    """Takes in the df and the create jdata.
    Plots the required shapes on the plot.
    TODO: fix hovertemplates. # semi fixed
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
        hovertemplate =
        '%{text}',
        showscale=False,
        marker=dict(
            line=dict(color="red", width=1),
            opacity=0.5
        )
    ))

    # update map sytle and intial view
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

    # create file name
    today = date.today()
    today = today.strftime("%Y%m%d")
    fig.write_html(f'output/{today}.html', full_html=True)
    # fig.show() # not sure which way we're doing it yet
    # fig.save() ? if possible
    # will need to host this somewhere, maybe on my site?
