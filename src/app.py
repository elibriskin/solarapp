import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from dash import Dash, html, dcc, Input, Output, State
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff

import censusgeocode as cg
from nrel_dev_api import set_nrel_api_key
from nrel_dev_api.solar import SolarResourceData, PVWattsV6
from census import Census
from us import states

import json

from main_v2 import fetch_data, get_sector_data, get_solar_data

#Read in all data files and set up APIs

census_key = "643fe7b4cd4581823fb346ee10ece4257c656e88"
set_nrel_api_key("HSgd1b4hnY5JLV0uq3eXXZdiAZKt0GaEShXEYzsQ")
c = Census(census_key)

# countydata = pd.read_csv("src/countydata.csv")
# countydata.NAME = countydata.NAME.str.replace(" County", "")
# energy = pd.read_csv("src/energy.csv")
# energycounty = pd.read_csv("src/energycounty.csv")

energy = pd.read_csv("https://raw.githubusercontent.com/elibriskin/solarapp/main/src/energy.csv")
countydata = pd.read_csv("https://raw.githubusercontent.com/elibriskin/solarapp/main/src/countydata.csv")
countydata.NAME = countydata.NAME.str.replace(" County", "")

energycounty = pd.read_csv("https://raw.githubusercontent.com/elibriskin/solarapp/main/src/energycounty.csv")

kw = 293.07107
energycounty['consumption_kw'] = energycounty['Consumption MMBtu'] * kw

# ac_kw = 0
# consumption = 0
# solar_pct = 0
# ghi = 0
# dni = 0

# Create user options list

options = countydata.NAME.unique()

array_options = {
    "Fixed Open Rack": 0,
    "Fixed Roof Mounted": 1,
    "One Axis": 2,
    "One Axis Backtracking": 3,
    "Two Axis": 4
}

app = Dash(__name__)
server = app.server

# Create user layout

app.layout = html.Div(children=[
    html.Div(className="container", children=[
        html.Div(className="container-main", children=[
            html.H1("Solar Energy - County Analysis"),
            html.P("This application provides a rough overview of solar radiation estimates in relation to current county energy needs."),
            html.Br(),
            html.H3("Select a county"),
            html.Br(),
            dcc.Dropdown(id='county-search', options=options, style=dict(
                color='white'
            )),
            html.Br(),
            html.Br(),
            html.H3('Select Solar Array Type'),
            html.Br(),
            dcc.Dropdown(id='solar_type', options=list(array_options.keys()), style=dict(
                color='white'
            )),
            html.Br(),
            html.Br(),
            html.Br(),
            html.H3("Nameplate Capacity (kw)"),
            dcc.Slider(0, 4, .2, value=10, marks=None, id='capacity',  tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.H3("Losses"),
            dcc.Slider(0, 100, 1, value=10, marks=None, id='losses',  tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.H3("Azimuth Angle (Degrees)"),
            dcc.Slider(0, 180, 1, value=10, marks=None, id='azimuth_angle',  tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.H3("Tilt Angle (Degrees)"),
            dcc.Slider(0, 180, 1, value=10, marks=None, id='tilt_angle',  tooltip={"placement": "bottom", "always_visible": True}),
            html.Br(),
            html.Button(id="submit-button", n_clicks=0, children="Submit"),
            dcc.Store(id='query-data')
        ]),
        html.Div(className="container-top", children=[
            html.Div(className="dash", id="box-top1", children=[
                html.P("Energy Consumption By Sector"),
                dcc.Loading(
                            id="loading-sector",
                            type="default",
                            children=dcc.Graph(
                                id='sectorPlot'
                            )
                        )
            ]),
            html.Div(className="dash", id="box-top2", children=[
                html.P("Percentage of Annual Needs"),
                html.H3(id="pv_output"),
                dcc.Loading(
                            id="loading-1",
                            type="default",
                            children=dcc.Graph(
                                id='piePlot',
                                # style = dict(
                                #     height='400px'
                                # ),
                            )
                        )
            ]),
            html.Div(className="dash", id="box-top3", children=[
                html.P("Solar Irradiance"),
                dcc.Loading(
                            id="loading-2",
                            type="default",
                            children=dcc.Graph(
                                id='barPlot'
                            ),
                            style = dict(display='grid')
                        )
            ])
        ]),
        html.Div(className="container-dashboard", children=[
            html.H1("Current County Energy Consumption"),
            html.Div(className="dash", id="box1", children=[
                html.P("Electricity"),
                html.H1(id='electricity')
            ]),
        html.Div(className="dash", id="box2", children=[
                html.P("Gas (Utility)"),
                html.H1(id='utilitygas')
            ]),
        html.Div(className="dash", id="box3", children=[
                html.P("Gas (Bottled, Tank, LP)"),
                html.H1(id='bottled')
            ]),
        html.Div(className="dash", id="box4", children=[
                html.P("Fuel"),
                html.H1(id='fuel')
            ]),
        html.Div(className="dash", id="box5", children=[
                html.P("Solar"),
                html.H1(id='solar')
            ]),
        html.Div(className="dash", id="box6", children=[
                html.P("Other"),
                html.H1(id='other')
            ])
        ])
    ])

])

@app.callback(
    Output('query-data', 'data'),
    Input('submit-button', 'n_clicks'),
    State('county-search', 'value'), prevent_initial_call=True)

def collect_data(n_clicks, value):
    if n_clicks is None:
        raise PreventUpdate
    else:
        data = fetch_data(str(value))
        return data

@app.callback(
    Output('electricity', 'children'),
    Output('utilitygas', 'children'),
    Output('bottled', 'children'),
    Output('fuel', 'children'),
    Output('solar', 'children'),
    Output('other', 'children'),
    Input('query-data', 'data'))

def update_data(collected_data):
    if collected_data is not None:
        total_data = collected_data
        electricity = total_data["electricity"]
        return f'{round(((total_data["electricity"] / total_data["total"]) * 100), 2)}%', \
               f'{round(((total_data["utility_gas"] / total_data["total"]) * 100), 2)}%',\
               f'{round(((total_data["bottled"] / total_data["total"]) * 100), 2)}%', \
               f'{round(((total_data["fuel"] / total_data["total"]) * 100), 2)}%', \
               f'{round(((total_data["solar"] / total_data["total"]) * 100), 2)}%', \
               f'{round(((total_data["other"] / total_data["total"]) * 100), 2)}%'

@app.callback(Output('piePlot', 'figure'),
              Output('barPlot', 'figure'),
              Output('sectorPlot', 'figure'),
              Output('pv_output', 'children'),
              Input('submit-button', 'n_clicks'),
              Input('solar_type', 'value'),
              Input('losses', 'value'),
              Input('capacity', 'value'),
              Input('tilt_angle', 'value'),
              Input('azimuth_angle', 'value'),
              State('county-search', 'value'))

def update_graph(n_clicks,solar_value, loss_value, capacity_value, tilt_value, azimuth_value, value):
    if n_clicks is None:
        raise PreventUpdate
    if value is None:
        ac_kw = 0
        consumption = 0
        solar_pct = 0
        ghi = 0
        dni = 0
    else:
        ac_kw, consumption, solar_pct, ghi, dni = get_solar_data(choice=value,
                                                                 solar_type=array_options[solar_value],
                                                                 losses=int(loss_value),
                                                                 capacity=int(capacity_value),
                                                                 tilt_angle=int(tilt_value),
                                                                 azimuth_angle=int(azimuth_value))

    bar_data = pd.DataFrame(
            {
                'Name': ['Ghi', 'Dni'],
                'Radiance': [ghi, dni]
            }
        )
    fig1 = go.Figure(
            data=[go.Pie(labels=['PV Power', 'Total consumption'], values=[ac_kw, consumption], hole=.7)])
    fig1.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)',
            'autosize': True
        })

    figure1 = fig1

    fig2 = px.bar(bar_data, y='Name', x='Radiance', orientation='h')
    fig2.update_layout({
        'plot_bgcolor': 'rgba(0, 0, 0, 0)',
        'paper_bgcolor': 'rgba(0, 0, 0, 0)'
    })

    figure2 = fig2

    sector_data = get_sector_data(value)
    fig3 = px.bar(sector_data, x='consumption_kw', y='Sector')
    fig3.update_layout({
            'plot_bgcolor': 'rgba(0, 0, 0, 0)',
            'paper_bgcolor': 'rgba(0, 0, 0, 0)'
        })

    figure3 = fig3

    return figure1, figure2, figure3, f'Esimated Photovoltaic Power Output: {round(ac_kw,2)}kW'


if __name__ == '__main__':
    app.run_server(debug=True)
