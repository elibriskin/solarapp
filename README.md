# Solar Energy Application
This is an application that is designed to allow users to briefly survey the energy needs/consumptions patterns in the US by county, and estimates photovoltaic energy that can be generated. The idea is to make a tool that can identify the feasibility of implementing solar energy technology in certain regions.

## How does it work?

On the right hand side the user can select any county in the United States. Then click the submit button at the bottom. Then, there is a series of parameters pertaining to solar technology options, such as type of solar racking, angles, losses, and capacity factor. On the upper section, the user will see the current energy consumption patterns of the county broken down by section. Then, there is data showing the estimated PV power that can be generated and its percentage relative to overall energy consumption of the county. Beneath there is solar irradiance data. Then, at the bottom there is a series of data showing percentage of households in the county that primarily use a speciic type of energy, such as electricitry, natural gas, solar etc.

## What is going on behind the scenes?

The application uses Python as the back end. There are a number of libraries that query databases to get the data for the dashboard. One such library, nrel-dev-api, queries data from the National Renewable Energy Lab. This is where information pertaining to PV output and solar irradiance comes from. Another library, census, queries the American Community Survey to get the household energy characteristics. 

While there are a number of files involved in the repo, there are two main ones: app.py and main_v2.py

App.py is the Python file responsible for running the backend of the dashboard. It utilizes Dash, a dashboard library, to interactively filter data and draw plots based off of the user selection. A user will select a county, the input will be stored and then used as a query to gather and filter the appropriate data. Then, the app will update and plots will be updated.

Main_v2.py is a Python script that has a series of functions that serve to query the data. By creating a separate file for such utility functions, it helps to make scripts more efficient and clearly delineated. The functions are then imported into app.py and used whenever a selection is made.

### What are the datasets involved?

There are 3 datasets used for this dashboard. They all can be located in the src folder. One dataset was queried from the ACS - this is the household energy data. Another dataset is the energy consumption patterns (energy.csv) and a final dataset containted county identification data.

## What are the sources involved?

Here are links to sources of data for the project:

National Renewable Energy Lab
https://developer.nrel.gov/

American Community Survey
https://www.census.gov/programs-surveys/acs

Consumption Data
https://www.eia.gov/consumption/data.php





https://github.com/SarthakJariwala/nrel_dev_api
