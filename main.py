import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import os
from dash import Dash, html, dcc, Input, Output, State
import plotly.graph_objects as go
import plotly.express as px
import plotly.figure_factory as ff

import censusgeocode as cg
from nrel_dev_api import set_nrel_api_key
from nrel_dev_api.solar import SolarResourceData, PVWattsV6
from census import Census
from us import states

import json

#Import API Keys
census_key = "643fe7b4cd4581823fb346ee10ece4257c656e88"
set_nrel_api_key("HSgd1b4hnY5JLV0uq3eXXZdiAZKt0GaEShXEYzsQ")

c = Census(census_key)

# Initial Data Preprocessing Into CSV Files

# fips = pd.read_table("fips2county.tsv")
# fips["Address"] = fips["CountyName"].str.cat(fips["StateAbbr"], sep = ", ")

# Use Census library to query Census data to get energy consumption percentages by county

# countydata = pd.DataFrame(c.acs5.get('NAME', {'for': 'county:*'}))
# countydata.to_csv("countydata.csv")

# energy = pd.DataFrame(c.acs5.get([
#     'B25040_001E',
#     'B25040_002E',
#     'B25040_003E',
#     'B25040_004E' ,
#     'B25040_005E',
#     'B25040_006E',
#     'B25040_007E',
#     'B25040_008E',
#     'B25040_009E'
# ], {'for': 'county:*'}))
#
# dict = {
#     'B25040_001E': 'Total',
#     'B25040_002E': 'Utility_Gas',
#     'B25040_003E': 'BottledTankLPGas',
#     'B25040_004E': 'Electricity',
#     'B25040_005E': 'Fuel',
#     'B25040_006E': 'Coal',
#     'B25040_007E': 'Wood',
#     'B25040_008E': 'Solar',
#     'B25040_009E': 'Other'
# }
# energy.rename(columns=dict, inplace=True)
# energy.to_csv("energy.csv")

# Reading in all data files

energy = pd.read_csv("energy.csv")
countydata = pd.read_csv("countydata.csv")
countydata.NAME = countydata.NAME.str.replace(" County", "")

energycounty = pd.read_csv("energycounty.csv")

# Convert MMBTU units to kwH

kw = 293.07107
energycounty['consumption_kw'] = energycounty['Consumption MMBtu'] * kw
energycounty["Address"] = energycounty["County Name"].str.cat(energycounty["State Name"], sep = ", ")

# Filter County energy data to get most recent available year

energycounty2021 = energycounty[energycounty.Year == 2021]

# Create list of all US counties for user selection

options = countydata.NAME.unique()

def fetch_data(choice):

    # Query NREL database to get solar irradiation data

    solar_resource_data = SolarResourceData(address=choice).outputs

    # Query NREL database to get esimated power

    pv_data = PVWattsV6(system_capacity=50, module_type=0, losses=.3, array_type=0, tilt=30, azimuth=0, address=choice)

    # Filter data by user selection

    filtered_county = countydata[countydata['NAME'] == choice]
    state_choice = filtered_county.state.values[0]
    county_choice = filtered_county.county.values[0]

    energy_county = energy[(energy.county == county_choice) & (energy.state == state_choice)]
    energycounty2021_county = energycounty2021[energycounty2021['Address'] == choice]

    # Extract all data from query response

    ac_kw = pv_data.outputs['ac_annual']
    ec_2021tng = energycounty2021[(energycounty2021.Address == choice)&(energycounty2021.Source == 'ng')].consumption_kw.sum()
    ec_2021elec = energycounty2021[(energycounty2021.Address == choice)&(energycounty2021.Source == 'elec')].consumption_kw.sum()
    consumption = ec_2021tng + ec_2021elec
    solar_pct = ac_kw / consumption
    ghi = solar_resource_data['avg_ghi']['annual']
    dni = solar_resource_data['avg_dni']['annual']
    total = energy_county.Total.values[0]
    utility_gas = energy_county.Utility_Gas.values[0]
    bottled = energy_county.BottledTankLPGas.values[0]
    electricity = energy_county.Electricity.values[0]
    fuel = energy_county.Fuel.values[0]
    solar = energy_county.Solar.values[0]
    other = energy_county.Other.values[0]

    #Create data dictionary to accumulate all relevant data

    data = {
        'ac_kw': ac_kw,
        'consumption': consumption,
        'solar_pct': solar_pct,
        'ghi': ghi,
        'dni': dni,
        'total': total,
        'utility_gas': utility_gas,
        'bottled': bottled,
        'electricity': electricity,
        'fuel': fuel,
        'solar': solar,
        'other': other
    }

    return data

def get_sector_data(choice):

    #Break down and summarize energy consumption by sector

    energycounty2021_county = energycounty2021[energycounty2021['Address'] == choice]

    sector_data = energycounty2021_county.groupby('Sector', as_index=False).agg({"consumption_kw": "sum"})

    return sector_data

