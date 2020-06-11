from flask import Blueprint, render_template, request
from werkzeug.utils import secure_filename

# import requests
import json
import csv

import os
import pandas as pd
import numpy as np
from random import choice
from string import ascii_uppercase


home = Blueprint('home', __name__)



def count_movies(watchlist):
    return len(watchlist)


def get_total_minutes(watchlist):
    return sum(watchlist[watchlist['Runtime (mins)'].notnull()]['Runtime (mins)'])


def avg_rating_imdb(watchlist):
    return "%.2f" %np.mean(watchlist['IMDb Rating'])


def avg_user_rating(watchlist):
    try:
        return "%.2f" %np.mean(watchlist[watchlist['Your Rating'].notnull()]['Your Rating'])
    except:
        return 0

def director_count(watchlist):
    total_directors = watchlist.groupby(['Directors']).agg({'Title':"count"}).to_dict()['Title']
    return len(total_directors)
    #return "%.2f" %np.mean(watchlist[watchlist['Your Rating'].notnull()]['Your Rating'])


def add_img_path(director):
    img_path = str(director).replace(" ","_")
    img_path = img_path+".jpg"
    #watchlist["img_path"] = watchlist["Directors"].apply(add_img_path)
    return img_path



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
    #
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

    #print (genres_dict)
    # print (genres)
    return genres


def generate_genres_year(watchlist):

    def clear_title(title):
        return title.replace("'", "")

    def get_decade(year):
        return year - year % 10

    # def split_genres(genres):
    #     return genres.split(",")

    watchlist["Title"] = watchlist["Title"].apply(clear_title)
    watchlist["Year"] = watchlist["Year"].apply(get_decade)
    #watchlist["Genres"] = watchlist["Genres"].apply(split_genres)

    genres_dict = dict()
    for i in range(len(watchlist["Genres"])):
            watchlist['Title'].loc[i] = watchlist['Title'].loc[i].replace("'","")
            for k in watchlist["Genres"].loc[i]:
                if k[0] == " ":
                    k = k.replace(" ","")
                if k not in genres_dict.keys():
                    genres_dict[k] = {'count':0,'movies':{watchlist["Title"].iloc[i]:0}}
                genres_dict[k]['count'] = genres_dict[k]['count']  +1
                genres_dict[k]['movies'][watchlist["Title"].iloc[i]] = watchlist["Year"].iloc[i]

    #print (genres_dict)
    return genres_dict


def top10_genres_stats(genres):
    genres_sorted = sorted(genres.items(), key=lambda x: x[1], reverse=True)
    top10_genres = genres_sorted

    total_count = sum(row[1] for row in top10_genres)

    top10_chart_data = []
    for row in top10_genres:
        top10_chart_data.append({
            "name": row[0] + " ("+ str(row[1]) +")",
            "y": float('%.2f' %(int(row[1]) * 100 / total_count))
        })

    return top10_chart_data


def decade_list(watchlist):
    decade_dict = watchlist.groupby(['Year']).agg({'Title':"count"}).to_dict()['Title']
    return list(decade_dict.keys())

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


#Get movie titles in each genre
def get_titles(genres_dict, genre, decade, watchlist):
    #All genres and all decades
    title_list = []

    if genre == 'all' and decade == 'all':
        title_list = list(watchlist['Title'])

    #Specific Genre and all decades
    if decade == 'all' and genre != 'all':
        for k1 in genres_dict.keys():
            if str(k1) == genre :
                for k2 in genres_dict[k1]['movies']:
                    title_list.append(k2)

    #All genres and Specific decades
    if decade != 'all' and genre == 'all':
        for k1 in genres_dict.keys():
            for k2 in genres_dict[k1]['movies']:
                if str(genres_dict[k1]['movies'][k2]) == decade:
                    title_list.append(k2)
                    title_list = list(set(title_list))


    #Specific genres and Specific decades
    if decade != 'all' and genre != 'all':
        for k1 in genres_dict.keys():
            if str(k1) == genre :
                for k2 in genres_dict[k1]['movies']:
                    if str(genres_dict[k1]['movies'][k2]) == decade:
                        title_list.append(k2)


    temp_watchlist = pd.DataFrame(columns=list(watchlist.columns))
    for i in range(len(title_list)):
        temp_watchlist = pd.concat([temp_watchlist, watchlist.loc[watchlist['Title']== title_list[i]]])

    movie_list = []
    for _, movie in temp_watchlist.iterrows():
        movie_list.append({
            "title": movie["Title"],
            "IMDB Rating": movie["IMDb Rating"],
            "Rating Count": movie["Num Votes"],
        })

    return movie_list




def top_directors(watchlist):
    top_directors = watchlist.groupby(['Directors']).agg({'Title':"count"}).to_dict()['Title']
    top_directors = {k: top_directors[k] for k in sorted(top_directors, key=top_directors.get, reverse=True)}
    #top_directors = list(top_directors.items())
    top_directors_list = []
    for k in list(top_directors.keys())[:12]:
        temp_director_dict = {'name':k, 'count':top_directors[k],'image_url':add_img_path(k)}
        top_directors_list.append(temp_director_dict)

    return top_directors_list


@home.route('/get-movies/', methods=['POST'])
def get_movies():

    if request.method != "POST":
        return None

    sel_genre = request.form.get('genre')
    sel_decade = request.form.get('decade')

    return json.dumps(get_titles(generate_genres_year(watchlist), str(sel_genre), str(sel_decade), watchlist))




@home.route('/', methods=["GET"])
def index():
    global watchlist
    watchlist = pd.read_csv("datasets/WATCHLIST_mahi.csv",encoding="ISO-8859-1")
    genres = generate_genres(watchlist)

    top_directors(watchlist)

    general = [
        {
            'title': 'Total Movies',
            'number': count_movies(watchlist),
            'icon': 'movie',
        },
        {
            'title': 'Total Directors',
            'number': director_count(watchlist),
            'icon': 'account_circle',
        },
        {
            'title': 'Total Genres',
            'number': len(list(generate_genres_year(watchlist).keys())),
            'icon': 'category',
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
        genres = list(generate_genres_year(watchlist).keys()),
        decades = decade_list(watchlist),
        movieList=json.dumps(get_titles(generate_genres_year(watchlist), 'all', 'all', watchlist)),
        top_directors = top_directors(watchlist)
    )



def allowed_file(filename):

    # We only want files with a . in the filename
    if not "." in filename:
        return False

    # Split the extension from the filename


    # Check if the extension is in ALLOWED_IMAGE_EXTENSIONS
    if ext.upper() in ['csv']:
        return True
    else:
        return False


@home.route('/', methods=["POST"])
def upload_file():

    if request.method == "POST":
        if request.files:

            file = request.files["file"]
            filename = secure_filename(file.filename)
            ext = filename.rsplit(".", 1)[1]

            if ext.lower() == 'csv':

                new_random_name = (''.join(choice(ascii_uppercase) for i in range(20)))
                file.save(os.path.join("datasets/FILE_UPLOADS", new_random_name))
                global watchlist
                watchlist = pd.read_csv("datasets/FILE_UPLOADS/{}".format(new_random_name),encoding="ISO-8859-1")

            else:
                print ("File is not correct")
                watchlist = pd.read_csv("datasets/WATCHLIST_mahi.csv",encoding="ISO-8859-1")

            try:
                genres = generate_genres(watchlist)
            except:
                watchlist = pd.read_csv("datasets/WATCHLIST_mahi.csv",encoding="ISO-8859-1")
                genres = generate_genres(watchlist)

            general = [
                {
                    'title': 'Total Movies',
                    'number': count_movies(watchlist),
                    'icon': 'movie',
                },
                {
                    'title': 'Total Directors',
                    'number': director_count(watchlist),
                    'icon': 'account_circle',
                },
                {
                    'title': 'Total Genres',
                    'number': len(list(generate_genres_year(watchlist).keys())),
                    'icon': 'category',
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
                genres = list(generate_genres_year(watchlist).keys()),
                decades = decade_list(watchlist),
                movieList=json.dumps(get_titles(generate_genres_year(watchlist), 'all', 'all', watchlist)),
                top_directors = top_directors(watchlist)
            )
        return None
    return None