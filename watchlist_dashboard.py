#Import the essential packages
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import math
import io
import base64
from operator import itemgetter



import dash
from dash.dependencies import Input, Output
import dash_core_components as dcc
import dash_html_components as html
import plotly.express as px
import plotly.graph_objects as go
import dash_table
from dash.exceptions import PreventUpdate





#analysis and data
def get_analysis(watchlist):

    def get_decade(year):
        return year - year%10

    def split_genres(genres):
        return genres.split(",")

    watchlist["Year"] = watchlist["Year"].apply(get_decade)
    watchlist["Genres"] = watchlist["Genres"].apply(split_genres)

    genres_dict = dict()
    for i in range(len(watchlist["Genres"])):
            #Remove ' from titles
            watchlist['Title'].loc[i] = watchlist['Title'].loc[i].replace("'","")

            # Split Genres and store them in dictionaries
            for k in watchlist["Genres"].loc[i]:
                if k[0] == " ":
                    k = k.replace(" ","")
                if k not in genres_dict.keys():
                    genres_dict[k] = {'count':0,'Title':[]}
                genres_dict[k]['count'] = genres_dict[k]['count']  +1
                genres_dict[k]['Title'].append(watchlist["Title"].iloc[i])

    genre_count_dict = dict()
    for k in genres_dict.keys():
        genre_count_dict[k] = genres_dict[k]['count']
    genre_count_dict = {k: genre_count_dict[k] for k in sorted(genre_count_dict, key=genre_count_dict.get, reverse=True)}

    decade_dict = watchlist.groupby(['Year']).agg({'Title':"count"}).to_dict()['Title']

    avg_rating_imdb = "%.2f" %np.mean(watchlist['IMDb Rating'])
    avg_my_rating = "%.2f" %np.mean(watchlist[watchlist['Your Rating'].notnull()]['Your Rating'])
    sum_run_time = sum(watchlist[watchlist['Runtime (mins)'].notnull()]['Runtime (mins)'])
    total_movies = len(watchlist)


    general_info = [avg_rating_imdb, avg_my_rating, sum_run_time, total_movies]

    return (general_info, decade_dict, genres_dict, genre_count_dict)


#Parsing the Uploaded contents
def parse_contents(contents, filename):
    content_type, content_string = contents.split(',')

    decoded = base64.b64decode(content_string)

    try:
        if 'csv' in filename:
            # Assume that the user uploaded a CSV file
            watchlist = pd.read_csv(io.StringIO(decoded.decode('ISO-8859-1')))

    except Exception as e:
        print(e)
        return html.Div([
            'There was an error processing this file. Please upload CSV file from provided by IMDB'
        ])

    general_info, decade_dict, genres_dict, genre_count_dict =  get_analysis(watchlist)
    return (general_info, decade_dict, genres_dict, genre_count_dict, watchlist)



#Read the Data and Get the analysis
watchlist = pd.read_csv("/Users/choobani/Downloads/WATCHLIST.csv",encoding="ISO-8859-1")
general_info, decade_dict, genres_dict, genre_count_dict =  get_analysis(watchlist)


#Get Genres Options
genre_options = []
for k in genre_count_dict.keys():
    temp_dict = {'label':k,'value':k}
    genre_options.append(temp_dict)

#Get movie titles in each genre
def get_titles(title_list):

    title_data = []
    for i in range(len(title_list)):
        rank = float((watchlist.loc[watchlist['Title']== title_list[i]]['IMDb Rating']).to_list()[0])
        temp_dict = {'Title':title_list[i], 'Rank': rank}
        title_data.append(temp_dict)
    #return title_data
    return sorted(title_data, key=itemgetter('Rank'), reverse=True)


#create the Dashboard
external_stylesheets = [
    'https://maxcdn.bootstrapcdn.com/bootstrap/4.0.0/css/bootstrap.min.css',
    'https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

app.layout = html.Div([ # container

    #Title and Subtitle of the Dashboard
    html.Div([
        html.Div([
            #html.H1(children='Watchlist Dashboard', className="float-left"),

            html.Img(
                    src="https://cdn.freebiesupply.com/images/large/2x/imdb-logo-transparent.png",
                    className='navbar-brand sd_logo'),
        ], className="header mb-4"),
    ], className="row"),


    #Upload file
    html.Div([
        html.Div([
        dcc.Upload(
        id='upload-data',
        children=html.Div([
            'Drag and Drop or ',
            html.A('Upload your Watchlist here')
            ]),
        # Allow multiple files to be uploaded
        multiple=False
    ),

        ], className="col-md-12 upload"),
    ], className="row"),





    #Visualising stats and some General Information
    html.Div([
        html.Div([ # row
            #Total Movies
            html.Div([
                html.Div([
                html.Div([
                    html.P("Total Movies", className="card-title"),
                    html.H2(children=str(general_info[3]), className="card-text", id='total_movies'),
                ], className="card-body"),
                ], className="card sd_card"),
            ], className='col-md-3 col-sm-6'),


            #Total Minutes
            html.Div([
                html.Div([
                html.Div([
                    html.P("Total Minutes", className="card-title"),
                    html.H2(children=str(general_info[2]), className="card-text", id='total_minutes'),
                ], className="card-body"),
                ], className="card sd_card"),
            ], className='col-md-3 col-sm-6'),

            #Average IMDB ranking
            html.Div([
                html.Div([
                html.Div([
                    html.P("Average IMDB ranking", className="card-title"),
                    html.H2(children=str(general_info[0]), className="card-text", id='avg_rating_imdb'),
                ], className="card-body")
                ], className="card sd_card")
            ], className='col-md-3 col-sm-6'),

            #Average User ranking
            html.Div([
                html.Div([
                html.Div([
                    html.P("Average user ranking", className="card-title"),
                    html.H2(children=str(general_info[1]), className="card-text", id='avg_my_rating'),
                ], className="card-body"),
                ], className="card sd_card"),
            ], className='col-md-3 col-sm-6'),

        ], className="row"),
    ], className="stats"),


    #Genres and Decades Pie Charts
    html.Div([ # row

        html.Div([
            html.Div([
                dcc.Graph(
                    id='genres_pie',
                    figure=go.Figure(
                    data=[go.Pie(labels=list(genre_count_dict.keys())[:10], values=list(genre_count_dict.values())[:10], hole=.3)],
                    layout=go.Layout(title='Top 10 Genres', titlefont=dict(size=20))))
            ], className='cart-block'),
        ], className='col-md-4 col-sm-6'),


        html.Div([
            html.Div([
                dcc.Graph(
                    id='decades_pie',
                    figure=go.Figure(
                    data=[go.Pie(labels=list(decade_dict.keys()), values=list(decade_dict.values()), hole=.3)],
                    layout=go.Layout(title='Decades',  titlefont=dict(size=20))))
            ], className='chart-block'),
        ], className='col-md-4 col-sm-6'),


        html.Div([
            html.Div([

                html.Div([
                    #html.P('Choose The Genre to see Best Movies:'),
                    dcc.Dropdown(
                        id='pick_genre',
                        options=genre_options,
                        value="Drama"),
                ], className="sd_dt_select mb-2"),

                html.Div([
                    dash_table.DataTable(
                        id='title_table',
                        columns=[{"name": 'Movie Title', "id": 'Title'},
                                {"name": 'IMDB Rank', "id": 'Rank'}] ,
                        data=get_titles(genres_dict['Drama']['Title']),
                        style_cell={'textAlign': 'left', 'fontSize':14, 'font-family':'sans-serif'},
                        page_size=10,
                        style_header={'fontWeight': 'bold'},)
                ], className="sd_dt_table"),


            ], className='sd_datatable'),
        ], className='col-md-4 col-sm-12'),

    ], className="row"),

], className="container")



@app.callback(
    [dash.dependencies.Output('total_movies', 'children'),
    dash.dependencies.Output('total_minutes', 'children'),
    dash.dependencies.Output('avg_rating_imdb', 'children'),
    dash.dependencies.Output('avg_my_rating', 'children'),
    dash.dependencies.Output('genres_pie', 'figure'),
    dash.dependencies.Output('decades_pie', 'figure'),
    dash.dependencies.Output('title_table', 'data')],
    [dash.dependencies.Input('upload-data', 'contents')],
    [dash.dependencies.State('upload-data', 'filename')])
def update_output(contents, filename):
    if contents is None:
        raise PreventUpdate

    if contents is not None:
        global watchlist
        general_info, decade_dict, genres_dict, genre_count_dict, watchlist =  parse_contents(contents, filename)
        return (general_info[3],
                general_info[2],
                general_info[0],
                general_info[1],
                {"data": [go.Pie(labels=list(genre_count_dict.keys())[:10], values=list(genre_count_dict.values())[:10], hole=.3)]},
                {"data": [go.Pie(labels=list(decade_dict.keys()), values=list(decade_dict.values()), hole=.3)]},
                get_titles(genres_dict['Drama']['Title'])
                )

#
# @app.callback(
#     dash.dependencies.Output('title_table', 'data'),
#     [dash.dependencies.Input('pick_genre', 'value')])
# def update_title_table(value):
#     return get_titles(genres_dict[value]['Title'])


if __name__ == '__main__':
    app.run_server(debug=True, use_reloader=False)
