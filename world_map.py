
# coding: utf-8

# # Interactive Map using Python
# ## World population data

# In[1]:


from IPython.core.display import display, HTML
display(HTML("<style>.container { width:100% !important; }</style>"))


# In[2]:


# https://towardsdatascience.com/how-to-create-an-interactive-geographic-map-using-python-and-bokeh-12981ca0b567


# In[3]:


# Import libraries
import pandas as pd
import numpy as np
import math

import geopandas
import json

from bokeh.io import output_notebook, show, output_file
from bokeh.plotting import figure
from bokeh.models import GeoJSONDataSource, LinearColorMapper, ColorBar, NumeralTickFormatter
from bokeh.palettes import brewer

from bokeh.io.doc import curdoc
from bokeh.models import Slider, HoverTool, Select
from bokeh.layouts import widgetbox, row, column


# ### Import cleaned data

# In[4]:


neighborhood_data = pd.read_csv('https://raw.githubusercontent.com/JimKing100/SF_Real_Estate_Live/master/data/neighborhood_data.csv')


# In[5]:


world = geopandas.read_file('world_map.geo.json')
world.head()


# In[6]:


df_world = world[['id', 'name', 'geometry']].copy()


# In[7]:


df_world = df_world.rename({'name':'country'}, axis=1)
df_world.head()


# In[8]:


world_population = pd.read_csv('world_population.csv', sep=';')
world_population.head()


# In[9]:


df_world_population = world_population[['Country Name', '2018']].copy()
df_world_population = df_world_population.rename({'Country Name':'country', '2018':'population'}, axis=1)
df_world_population.head()


# In[10]:


df_world = pd.merge(df_world, df_world_population, on="country")


# ## Geodata

# In[11]:


# Read the geojson map file for Realtor Neighborhoods into a GeoDataframe object
sf = geopandas.read_file('https://raw.githubusercontent.com/JimKing100/SF_Real_Estate_Live/master/data/Realtor%20Neighborhoods.geojson')


# Set the Coordinate Referance System (crs) for projections
# ESPG code 4326 is also referred to as WGS84 lat-long projection
sf.crs = {'init': 'epsg:4326'}
world.crs = {'init': 'epsg:4326'}
# Rename columns in geojson map file
sf = sf.rename(columns={'geometry': 'geometry','nbrhood':'neighborhood_name', 'nid': 'subdist_no'}).set_geometry('geometry')

# Change neighborhood id (subdist_no) for correct code for Mount Davidson Manor and for parks
sf.loc[sf['neighborhood_name'] == 'Mount Davidson Manor', 'subdist_no'] = '4n'
sf.loc[sf['neighborhood_name'] == 'Golden Gate Park', 'subdist_no'] = '12a'
sf.loc[sf['neighborhood_name'] == 'Presidio', 'subdist_no'] = '12b'
sf.loc[sf['neighborhood_name'] == 'Lincoln Park', 'subdist_no'] = '12c'

sf.sort_values(by=['subdist_no'])
df_world.head()


# ### The ColorBar

# In[12]:


df_world.population.max()


# In[13]:


# This dictionary contains the formatting for the data in the plots
format_data = [('population', df_world_population.population.min(), df_world.population.max(),'0,0', 'Population'),
              ]

#Create a DataFrame object from the dictionary
format_df = pd.DataFrame(format_data, columns = ['field' , 'min_range', 'max_range' , 'format', 'verbage'])


# In[14]:


format_df


# ### Create a function that returns json_data for the year selected by the user

# In[15]:


# Create a function the returns json_data for the year selected by the user
def json_data(selectedYear):
    yr = selectedYear

    # Pull selected year from neighborhood summary data
    df_yr = neighborhood_data[neighborhood_data['year'] == yr]

    # Merge the GeoDataframe object (sf) with the neighborhood summary data (neighborhood)
    merged = pd.merge(sf, df_yr, on='subdist_no', how='left')

    # Fill the null values
    values = {'year': yr, 'sale_price_count': 0, 'sale_price_mean': 0, 'sale_price_median': 0,
              'sf_mean': 0, 'price_sf_mean': 0, 'min_income': 0}
    merged = merged.fillna(value=values)

    # Bokeh uses geojson formatting, representing geographical features, with json
    # Convert to json
    merged_json = json.loads(merged.to_json())

    # Convert to json preferred string-like object
    json_data = json.dumps(merged_json)
    return json_data


# In[16]:


#merged_json


# In[17]:


df_world.head()


# ## Convert df to json

# In[22]:


def world_json_data():

    #df_world_merged = pd.merge(df_world, df_world_population, on='country')
    #display(df_world_merged.head())

    df_world_json = json.loads(df_world.to_json())
    world_json_data = json.dumps(df_world_json)

    return world_json_data


# ### Plotting Function

# In[23]:


format_df.loc[format_df['field'] == 'population', 'format'].iloc[0]


# In[24]:


# Create a plotting function
def make_plot(field_name):
    # Set the format of the colorbar
    min_range = format_df.loc[format_df['field'] == field_name, 'min_range'].iloc[0]
    max_range = format_df.loc[format_df['field'] == field_name, 'max_range'].iloc[0]
    field_format = format_df.loc[format_df['field'] == field_name, 'format'].iloc[0]

    # Instantiate LinearColorMapper that linearly maps numbers in a range, into a sequence of colors.
    color_mapper = LinearColorMapper(palette = palette, low = min_range, high = max_range)

    # Create color bar.
    format_tick = NumeralTickFormatter(format=field_format)
    color_bar = ColorBar(color_mapper=color_mapper, label_standoff=18, formatter=format_tick,
    border_line_color=None, location = (0, 0))

    # Create figure object.
    verbage = format_df.loc[format_df['field'] == field_name, 'verbage'].iloc[0]

    p = figure(title = 'World Population 2018 by Country',
             plot_height = 650, plot_width = 1200,
             toolbar_location = None)
    p.xgrid.grid_line_color = None
    p.ygrid.grid_line_color = None
    p.axis.visible = False

    # Add patch renderer to figure.
    p.patches('xs','ys', source = geosource, fill_color = {'field' : field_name, 'transform' : color_mapper},
          line_color = 'black', line_width = 0.25, fill_alpha = 1)

    # Specify color bar layout.
    p.add_layout(color_bar, 'right')

    # Add the hover tool to the graph
    p.add_tools(hover)
    return p


# ## Main code

# In[25]:


# Input geojson source that contains features for plotting for:
# initial year 2018 and initial criteria sale_price_median
#geosource = GeoJSONDataSource(geojson = json_data(2018))
input_field = 'field_name'

geosource = GeoJSONDataSource(geojson = world_json_data())

# Define a sequential multi-hue color palette.
palette = brewer['Blues'][8]

# Reverse color order so that dark blue is highest population.
palette = palette[::-1]


# ### The HoverTool

# In[26]:


# Add hover tool
hover = HoverTool(tooltips = [ ('Country','@country'),

                             ])


# ### Widgets and The Callback Function

# In[27]:


input_field


# In[28]:


# Call the plotting function
p = make_plot('population')

# Make a slider object: slider
slider = Slider(title = 'Year',start = 2009, end = 2018, step = 1, value = 2018)
#slider.on_change('value', update_plot)

# Make a selection object: select
select = Select(title='Select Criteria:', value='Median Sales Price', options=['Median Sales Price', 'Minimum Income Required',])
                                                                              # 'Average Sales Price', 'Average Price Per Square Foot',
                                                                              # 'Average Square Footage', 'Number of Sales'])
#select.on_change('value', update_plot)

# Make a column layout of widgetbox(slider) and plot, and add it to the current document
# Display the current document
layout = column(p)#, widgetbox(select), widgetbox(slider))
curdoc().add_root(layout)


# ## Test notebook

# In[29]:


# Use the following code to test in a notebook, comment out for transfer to live site
# Interactive features will not show in notebook
output_notebook()
show(p)


# ## To run locally using Bokeh do following in terminal:
# ```
# bokeh serve -- notebook.ipynb
# ```
