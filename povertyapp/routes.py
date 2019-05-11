import json

import plotly
from flask import render_template, request

from povertyapp import app
from wrangling_scripts.plotting import return_figures

@app.route("/", methods=['POST', 'GET'])
@app.route("/index", methods=['POST', 'GET'])
def index():

    country_options = [['Argentina'], ['Australia'], ['Belgium'], ['Brazil'], 
      ['Canada'], ['Chile'], ['Denmark'], ['Egypt, Arab Rep.'], 
      ['El Salvador'], ['Finland'], ['France'], ['Germany'], ['Greece'], 
      ['Iceland'], ['Iran, Islamic Rep.'], ['Ireland'], ['Italy'], ['Israel'], 
      ['Korea, Rep.'], ['Malaysia'], ['Mexico'], ['Netherlands'], ['Norway'],
      ['Pakistan'], ['Portugal'], ['Romania'], ['Russian Federation'], 
      ['South Africa'], ['Spain'], ['Sweden'], ['Thailand'], ['Uganda'], 
      ['United Kingdom'], ['United States'], ['Vietnam']]
    
    if (request.method == 'POST') and request.form:
        figures = return_figures(request.form)
        countries_selected = []

        for country in request.form.lists():
            countries_selected.append(country[0])
        
        scroll = 'country-filter'
    
    else:
        figures = return_figures()
        countries_selected = ['United States']

        scroll = None

    # plot ids for the html id tag
    ids = ['figure-{}'.format(i) for i, _ in enumerate(figures)]

    # Convert the plotly figures to JSON for javascript in html template
    figuresJSON = json.dumps(figures, cls=plotly.utils.PlotlyJSONEncoder)

    return render_template("index.html", 
                           ids=ids, 
                           figuresJSON=figuresJSON,
                           all_countries=country_options,
                           countries_selected=countries_selected,
                           scroll=scroll)

#app.run(host='127.0.0.1', port=5000, debug=True)