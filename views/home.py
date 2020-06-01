from flask import Blueprint, render_template, request
import requests
import json
import csv

import pandas as pd
import numpy as np


home = Blueprint('home', __name__)




def count_movies(watchlist):
    return len(watchlist)


def get_total_minutes(watchlist):
    return sum(watchlist[watchlist['Runtime (mins)'].notnull()]['Runtime (mins)'])


def avg_rating_imdb(watchlist):
    return "%.2f" %np.mean(watchlist['IMDb Rating'])


def avg_user_rating(watchlist):
    return "%.2f" %np.mean(watchlist[watchlist['Your Rating'].notnull()]['Your Rating'])


def generate_genres(watchlist):

    def clear_title(title):
        return title.replace("'", "")

    def get_decade(year):
        return year - year % 10

    def split_genres(genres):
        return genres.split(",")

    watchlist["Title"] = watchlist["Title"].apply(clear_title)
    watchlist["Year"] = watchlist["Year"].apply(get_decade)
    watchlist["Genres"] = watchlist["Genres"].apply(split_genres)

    genres = dict()
    for _, movie in watchlist.iterrows():
        for genre in movie['Genres']:
            if genre[0] == " ":
                genre = genre.replace(" ","")
            if genre in genres.keys():
                genres[genre] = genres[genre] + 1
            else:
                genres[genre] = {}
                genres[genre] = 0

    return genres


def top10_genres_stats(genres):
    genres_sorted = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    top10_genres = genres_sorted[:10]

    total_count = sum(row[1] for row in top10_genres)

    top10_chart_data = []
    for row in top10_genres:
        top10_chart_data.append({
            "name": row[0] + " ("+ str(row[1]) +")",
            "y": float('%.2f' %(int(row[1]) * 100 / total_count))
        })

    return top10_chart_data


def decade_stats(watchlist):
    decade_dict = watchlist.groupby(['Year']).agg({'Title':"count"}).to_dict()['Title']
    total_count = sum(decade_dict.values())

    decade_chart_data = []
    for year in decade_dict.keys():
        decade_chart_data.append({
            "name": str(year) + " ("+ str(decade_dict[year]) +")",
            "y": float('%.2f' %(int(decade_dict[year]) * 100 / total_count))
        })

    return decade_chart_data


def get_movies(watchlist):

    movie_list = []
    for _, movie in watchlist.iterrows():
        movie_list.append({
            "title": movie["Title"],
            "IMDB Rating": movie["IMDb Rating"],
            "Rating Count": movie["Num Votes"],
        })

    return movie_list


def top_directors(watchlist):
    top_directors = watchlist.groupby(['Directors']).agg({'Title':"count"}).to_dict()['Title']
    top_directors = {k: top_directors[k] for k in sorted(top_directors, key=top_directors.get, reverse=True)}
    top_directors = list(top_directors.items())

    print(top_directors[:12])

    return None



@home.route('/')
def index():

    watchlist = pd.read_csv("datasets/WATCHLIST_vahab.csv",encoding="ISO-8859-1")
    genres = generate_genres(watchlist)

    top_directors(watchlist)

    general = [
        {
            'title': 'Total Movies',
            'number': count_movies(watchlist),
            'icon': 'movie',
        },
        {
            'title': 'Total Minutes',
            'number': get_total_minutes(watchlist),
            'icon': 'av_timer',
        },
        {
            'title': 'IMDB Ranking',
            'number': avg_rating_imdb(watchlist),
            'icon': 'theaters',
        },
        {
            'title': 'User ranking',
            'number': avg_user_rating(watchlist),
            'icon': 'analytics',
        }
    ]

    return render_template("home.html",
        stats=general,
        genresData=json.dumps(top10_genres_stats(genres)),
        decadesData=json.dumps(decade_stats(watchlist)),
        movieList=json.dumps(get_movies(watchlist))
    )
