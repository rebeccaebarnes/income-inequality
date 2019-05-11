from collections import OrderedDict
from datetime import date, datetime

import pandas as pd
import plotly.graph_objs as go
import plotly.plotly as py

from wrangling_scripts.cleaning_fn import extract_data, select_countries,\
    convert_country_code, api_query, full_query

country_default = OrderedDict([('United States', 'United States')])

def return_figures(country=country_default):
    # When the countries variable is empty, use the country_default
    if not bool(country):
        country=country_default
    
    country_filter = list(country.values())

    # Complete API extraction
    data_date = datetime(2019, 5, 11)
    current_year = str(date.today().year)
    
    params = {'format': 'json', 'per_page': '1000', 
              'date': '1990:' + current_year}
    
    results = api_query('SI.DST.10TH.10', params)
    last_update = results[0]['lastupdated']
    last_update = datetime.strptime(last_update, '%Y-%m-%d')
    if last_update > data_date:
        for data_code, file_name in zip(
            ['SI.DST.10TH.10', 'SI.DST.FRST.10'], ['highest_10', 'lowest_10']):
            full_query(data_code, params, './data/' + file_name)

    # Extract data from files
    df_highest = extract_data('data/highest_10')
    df_lowest = extract_data('data/lowest_10')
    df_combined = df_highest.merge(df_lowest, on=['country', 'code', 'year'])
    df_combined['diffs'] = df_combined['value_x'] - df_combined['value_y']

    selected_countries = select_countries(df_highest)

    df_final = df_combined[df_combined.country.isin(selected_countries)]
    df_final = convert_country_code(df_final)
    df_2015 = df_final.query('year == "2013"').dropna()

    # Create first chart - choropleth 2013
    # https://plot.ly/python/choropleth-maps/
    graph_one = [dict(
        type = 'choropleth',
        locations = df_2015['3let'],
        z = df_2015['diffs'],
        text = df_2015['country'],
        colorscale = 'Viridis',
        autocolorscale = False,
        reversescale = True,
        marker = dict(
            line = dict (
                color = 'rgb(180,180,180)',
                width = 0.5
            ) ),
        colorbar = dict(
            title = 'Difference in <br>Share of Income<br>(%)'),
    )]

    layout_one = dict(
        margin = dict(
            l = 30,
            r = 10, 
            b = 0,
            t = 10,
            pad = 4
        ),
        geo = dict(
            # https://community.plot.ly/t/how-to-change-colors-for-na-values-to-gray-in-a-choropleth-map/15746/4
            landcolor = 'lightgray',
            showland = True,
            showcountries = True,
            countrycolor = 'gray',
            countrywidth = 0.5,
            showframe = False,
            showcoastlines = False,
            projection = dict(
                type = 'Mercator'
            )
        )
    )

    # Create second chart - line chart worst 10 countries
    # Start plots at 2000
    selected_years = [str(x) for x in range(2000, date.today().year)]
    df_years = df_final[df_final.year.isin(selected_years)]

    # Sort countries by average difference over years
    average_diff = df_years.groupby('country')['diffs'].mean().reset_index()\
        .sort_values(by='diffs')
    worst_6_countries = average_diff.country[-6:].tolist()
    worst_6_countries.sort()

    graph_two = []

    for country in worst_6_countries:
        x_val = df_years[df_years['country'] == country].year.tolist()
        y_val = df_years[df_years['country'] == country].diffs.tolist()
        graph_two.append(
            go.Scatter(x=x_val, 
                       y=y_val, 
                       mode='lines+markers', 
                       marker = dict(
                           size=4,
                       ),
                       line=dict(
                           width=4,
                           shape='spline',
                           smoothing=0.3,
                       ),
                       name=country)
        )
    
    layout_two = dict(
        title = '<b>Highest Income Inequality</b>',
        xaxis = dict(
            title = 'Year',
            autotick = False,
            dtick = 5
        ),
        yaxis = dict(
            title = 'Difference in Income Share (%)'
        ),
        hovermode = 'closest',
    )

    # Create third chart - best 10 countries
    best_6_countries = average_diff.country[:6].tolist()
    best_6_countries.sort()

    graph_three = []

    for country in best_6_countries:
        x_val = df_years[df_years['country'] == country].year.tolist()
        y_val = df_years[df_years['country'] == country].diffs.tolist()
        graph_three.append(
            go.Scatter(x=x_val, 
                       y=y_val, 
                       mode='lines+markers', 
                       marker = dict(
                           size=4,
                       ),
                       line = dict(
                           width=4,
                           shape='spline',
                           smoothing=0.3,
                       ),
                       name=country)
        )
    
    layout_three = dict(
        title = '<b>Lowest Income Inequality</b>',
        xaxis = dict(
            title = 'Year',
            autotick = False,
            dtick = 5
        ),
        yaxis = dict(
            title = 'Difference in Income Share (%)'
        ),
        hovermode = 'closest',
    )

    # Create fourth chart - G10 countries
    g10_countries = ['Belgium', 'Canada', 'France', 'Germany', 'Italy', 'Japan',
                     'Netherlands', 'Sweden', 'Switzerland', 'United Kingdom', 
                     'United States']

    graph_four = []

    for country in g10_countries:
        x_val = df_years[df_years['country'] == country].year.tolist()
        y_val = df_years[df_years['country'] == country].diffs.tolist()
        graph_four.append(
            go.Scatter(x=x_val, 
                       y=y_val, 
                       mode='lines+markers', 
                       marker = dict(
                           size=4,
                       ),
                       line = dict(
                           width=4,
                           shape='spline',
                           smoothing=0.3,
                       ),
                       name=country)
        )
    
    layout_four = dict(
        title = '<b>G10 Countries</b>',
        xaxis = dict(
            title = 'Year',
            autotick = False,
            dtick = 5
        ),
        yaxis = dict(
            title = 'Difference in Income Share (%)'
        ),
        hovermode = 'closest',
    )

    # Create fifth chart - individual country over time, stacked area chart
    # https://plot.ly/python/filled-area-plots/
    df_country = df_years[df_years['country'] == country_filter[0]].copy()
    low_median = round(df_country.value_y.median(), 2)
    high_median = round(df_country.value_x.median(), 2)
    df_country.fillna(method='ffill', inplace=True)
    df_country.fillna(method='bfill', inplace=True)
    country_years = df_country.year.tolist()

    trace1 = dict(
        x=country_years,
        y=df_country.value_y.tolist(),
        hoverinfo='x+y',
        mode='lines',
        line = dict(
            width=4,
            shape='spline',
            smoothing=0.3,
                    ),
        stackgroup='one',
        name='Lowest 10%'
    )
    trace2 = dict(
        x=country_years,
        y=df_country.value_x.tolist(),
        hoverinfo='x+y',
        mode='lines',
        line = dict(
            width=4,
            shape='spline',
            smoothing=0.3,
                    ),
        stackgroup='one',
        name='Highest 10%'
    )

    graph_five = [trace1, trace2]

    layout_five = dict(
        title='<b>Income Distribution for Highest and Lowest 10%</b>* <br> -- <b>{}</b> --'\
            .format(country_filter[0]),
        xaxis = dict(
            title = 'Year',
            autotick = False,
            dtick = 5
        ),
        yaxis = dict(
            title = 'Income Share (%)'
        ),
        annotations = [
            dict(
                x=2007,
                y=10,
                text=' Median for lowest 10%: {} <br> Median for highest 10%: {}'\
                    .format(low_median, high_median),
                font = dict(
                    size = 15
                ),
                showarrow=False,
                align='left'
            ),
        ]
    )

    # Append figures
    figures = []
    graphs = (graph_one, graph_two, graph_three, graph_four, graph_five)
    layouts = (layout_one, layout_two, layout_three, layout_four, layout_five)
    config = dict(responsive = True)

    for graph, layout in zip(graphs, layouts):
        figures.append(dict(data=graph, layout=layout, config=config))

    return figures
