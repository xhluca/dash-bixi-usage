import os
from io import BytesIO
from textwrap import dedent
from zipfile import ZipFile

import dash
import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
import requests
from dash.dependencies import Input, Output, State

import dash_reusable_components as drc

COL_NAME_MAP = {
    # Maps the column name in the data_df to a more verbose name
    'start_station_code': 'Start Station ID',
    'end_station_code': 'End Station ID',
    'start_date': 'Starting Time of Trip',
    'end_date': 'End Time of Trip',
    'duration_sec': 'Duration of Trip (in seconds)'
}


app = dash.Dash(__name__)
server = app.server


def get_trip_count(original_df):
    """Utils function to get the dataframe containing the trip count for each trip, which is the combination of
    a starting and an ending station"""
    trip = original_df['start_station_code'].astype('str') + " " + original_df['end_station_code'].astype('str')
    trip_count = pd.DataFrame(trip.value_counts(), columns=['trip_count'])
    parsed_codes = pd.DataFrame([string.split(" ") for string in trip_count.index.values],
                                columns=['start_station_code', 'end_station_code'])
    trip_df = trip_count.reset_index().join(parsed_codes).set_index('index')

    trip_df[['start_station_code', 'end_station_code']] = trip_df[['start_station_code', 'end_station_code']].astype(
        int)
    trip_df.sort_values(['start_station_code', 'end_station_code'], inplace=True, axis=0, ascending=True)

    return trip_df


def generate_figure_2d(data_df, xaxis, yaxis, xaxis_name, yaxis_name, sample=10000):

    if data_df.shape[0] > sample:
        data_df = data_df.sample(n=sample)

    ls = list(data_df.groupby('is_member'))
    name_map = {0: 'Not Member', 1: 'Member'}

    data = []

    for i in range(len(ls)):
        name = name_map[i]
        df = ls[i][1]

        trace = go.Scattergl(
            x=df[xaxis],
            y=df[yaxis],
            mode='markers',
            name=name,
            marker=go.Marker(
                symbol='circle',
                opacity=0.8
            )
        )

        data.append(trace)

    layout = go.Layout(
        title=f'Bixi Usage in 2017, {data_df.shape[0]} trips plotted',
        margin=go.Margin(r=5),
        legend=dict(x=0, y=1.05, orientation="h"),
        xaxis=dict(title=xaxis_name),
        yaxis=dict(title=yaxis_name)
    )

    return go.Figure(data=data, layout=layout)


# Custom Script for Heroku
if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })

app.layout = html.Div(children=[
    # .container class is fixed, .container.scalable is scalable
    html.Div(className="banner", children=[
        html.H2('Bixi Trips Explorer'),

        html.Img(
            src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png"
        )
    ]),


    html.Div(id='body', className='container scalable', children=[
        html.Div(className='seven columns unselect', children=[
            dcc.Graph(
                id='bixi-plot',
                style={'height': '85vh'}
            )
        ]),

        html.Div(className='five columns', style={'float': 'right'}, children=[
            drc.Card(className="unselect", children=[
                drc.NamedDropdown(
                    name="Select a column to be the x-axis",
                    id='dropdown-selection-xaxis',
                    options=[{'value': val, 'label': COL_NAME_MAP[val]} for val in COL_NAME_MAP.keys()],
                    value='start_date',
                    searchable=False,
                    clearable=False
                ),

                drc.NamedDropdown(
                    name="Select a column to be the y-axis",
                    id='dropdown-selection-yaxis',
                    options=[{'value': val, 'label': COL_NAME_MAP[val]} for val in COL_NAME_MAP.keys()],
                    value='duration_sec',
                    searchable=False,
                    clearable=False
                ),

                drc.NamedSlider(
                    id='slider-sample-size',
                    name='Choose Sample Size',
                    min=0,
                    max=1000000,
                    step=None,
                    marks={i: i for i in [20000, 250000, 500000, 750000, 1000000]},
                    value=500000
                )
            ]),

            drc.Card(children=[
                html.P("Click a data point to get more information...", id='p-display-message'),

                html.Div(id='div-plot-click-result')

            ])
        ])
    ])
])


@app.server.before_first_request
def load_data():
    global data_df

    # If file doesn't exist, we download from the bixi website
    if not os.path.exists('data'):
        # Get the 2017 data
        r = requests.get('https://www.bixi.com/c/bixi/file_db/data_all.file/BixiMontrealRentals2017.zip')
        z = ZipFile(BytesIO(r.content))
        z.extractall(path='data')

    # Load Data
    data_df = pd.concat(
        [pd.read_csv(f"data/2017/OD_2017-{month:02d}.csv") for month in range(4, 11)]
    )


@app.callback(Output('bixi-plot', 'figure'),
              [Input('dropdown-selection-xaxis', 'value'),
               Input('dropdown-selection-yaxis', 'value'),
               Input('slider-sample-size', 'value')])
def update_graph(xaxis_value, yaxis_value, sample_size):
    return generate_figure_2d(
        data_df=data_df,
        xaxis=xaxis_value,
        xaxis_name=COL_NAME_MAP[xaxis_value],
        yaxis=yaxis_value,
        yaxis_name=COL_NAME_MAP[yaxis_value],
        sample=sample_size
    )


@app.callback(Output('div-plot-click-result', 'children'),
              [Input('bixi-plot', 'clickData')],
              [State('dropdown-selection-xaxis', 'value'),
               State('dropdown-selection-yaxis', 'value')])
def display_plot_click_message(clickData, xaxis_value, yaxis_value):
    if clickData:
        x = clickData['points'][0]['x']
        y = clickData['points'][0]['y']

        selected_series = data_df[(data_df[xaxis_value] == x) & (data_df[yaxis_value] == y)].iloc[0]

        start_date = selected_series['start_date']
        end_date = selected_series['end_date']
        start_station_code = selected_series['start_station_code']
        end_station_code = selected_series['end_station_code']
        duration_sec = selected_series['duration_sec']
        is_member = selected_series['is_member']

        if is_member == 1:
            membership_str = "The trip was effectuated by a Bixi member."
        else:
            membership_str = "The trip was not effectuated by a Bixi member."

        return dcc.Markdown(
            dedent(f'''
                The trip started at the station {start_station_code}, on {start_date}.
                
                It ended at the station {end_station_code}, on {end_date}.
                
                It last {duration_sec} seconds.
                
                {membership_str}
            ''')
        )


@app.callback(Output('p-display-message', 'style'), [Input('div-plot-click-result', 'children')])
def hide_default_display_message(children):
    if children:
        return {'display': 'none'}
    else:
        return None


external_css = [
    # Normalize the CSS
    "https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",
    # Fonts
    "https://fonts.googleapis.com/css?family=Open+Sans|Roboto",
    "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
    # Base Stylesheet
    "https://cdn.rawgit.com/xhlulu/9a6e89f418ee40d02b637a429a876aa9/raw/base-styles.css",
    # Custom Stylesheet
    "https://rawgit.com/xhlulu/dash-bixi-usage/dev/custom-styles.css"
]

for css in external_css:
    app.css.append_css({"external_url": css})

# Running the server
if __name__ == '__main__':
    app.run_server(debug=True)
