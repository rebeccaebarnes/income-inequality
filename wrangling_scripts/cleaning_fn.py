import json
import os
import requests

import pandas as pd

def api_query(data_code, params):
    """
    Retrieves a query from the World Bank Data API.

    Args:
        data_code: (str) World Bank reference code for data source.
        params: (dict) Query parameters.
    Returns:
        json object.
    """
    link = 'https://api.worldbank.org/v2/en/country/all/indicator/'
    r = requests.get(link + data_code, params=params)
    return r.json()

def full_query(data_code, params, folder_name):
    """
    Retrieves all results for a data source from the World Bank Data API 
    by conducting a query for each page. Saves the query results in a json file.

    Args:
        data_code: (str) World Bank reference code for data source.
        params: (dict) Query parameters.
        folder_name: (str) Location for saving files.
    Returns:
        json object.
    """
    # Complete initial query
    initial = api_query(data_code, params)
    
    # Determine number of pages for full results
    num_pages = initial[0]['pages']
    
    # Create data directory
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    
    for i in range(num_pages):
        # Save file
        file_name = data_code + '_pg_' + str(i + 1) + '.txt'
        file_path = os.path.join(folder_name, file_name)
        if not os.path.isfile(file_path):
            open(file_path, 'w').close()
        
        # Update params
        params['page'] = i + 1
        
        # Complete query and save
        results = api_query(data_code, params)
        with open(file_path, 'w') as file:
            json.dump(results, file)

def extract_data(folder_name):
    """
    Creates a dataframe from the .txt files in the specified folder. 
    Files are originally extracted from the World Bank Data API.
    """
    df_list = []
    
    directory = os.fsencode(folder_name)
    for file in os.listdir(directory):
        file_name = os.fsdecode(file)
        if file_name.endswith(".txt"):
            file_path = os.path.join(folder_name, file_name)
            with open(file_path) as json_file:
                data = json.load(json_file)
                for entry in data[1]:
                    df_list.append({
                        'country': entry['country']['value'],
                        'code': entry['country']['id'],
                        'year': entry['date'],
                        'value': entry['value']
                    })
    
    df = pd.DataFrame(df_list, columns=['country', 'code',
                                        'year', 'value'])
    
    return df

def select_countries(df, 
                     select_years=[str(x) for x in range(2005, 2016)],
                     threshold=3, values='value'):
    """
    Extract a list of countries that has sufficient data for the selected years.

    Args:
        df: (DataFrame) Created by "extract_data".
        select_years: (list) Years (str) to be included in analysis.
        threshold: (int) Threshold for dropping rows with missing values as
                   implemented in the pandas .dropna() method.
        values: (str or list) Name of column that will be used for values in the
                pandas .pivot() method.
    Returns:
        pandas Series.
    """
    # Filter for only relevant years
    df = df[df.year.isin(select_years)]

    # Find countries with sufficient data for select years
    df_pivot = df.pivot(index='country', columns='year', values=values)\
        .reset_index()
    df_pivot.dropna(subset=select_years, thresh=threshold, inplace=True)
    countries = df_pivot['country']

    return countries

def convert_country_code(data_df):
    """Adds 3 letter country code to dataframe with 2 letter country code."""
    country_df = pd.read_csv('data/country_map.txt', sep='\t')
    df = data_df.merge(country_df, left_on='code', right_on='2let')

    return df