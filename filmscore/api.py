import json
import time
from markupsafe import re
import requests
import googleapiclient.discovery
import difflib
import string
from datetime import datetime
from imdb import IMDb
from rotten_tomatoes_scraper.rt_scraper import MovieScraper
from django.http import HttpResponseBadRequest, JsonResponse
from soupsieve import closest
from .models import AppReview, Account, Film, RecentlyVisited, SavedFilm, RecentReviews

def change_password(request):
    if request.method == "PUT":
        PUT = json.loads(request.body)
        if PUT['currentpassword'] == request.user.password:
            if PUT['newpass1'] == PUT['newpass2']:
                for user in Account.objects.all():
                    if request.user.username == user.username:
                        user.password = PUT['newpass1']
                        return JsonResponse({})
        return HttpResponseBadRequest

def change_details(request):
    if request.method == "PUT":
        PUT = json.loads(request.body)
        user = None
        for temp in Account.objects.all():
            if temp.username == request.user.username:
                user = temp
                break
        
        if PUT['username'] != "":
            user.username = PUT['username']
        if PUT['email'] != "":
            user.email = PUT['email']
        if PUT['firstname'] != "":
            user.firstName = PUT['firstname']
        if PUT['lastname'] != "":
            user.lastName = PUT['lastname']
        
        return JsonResponse({
            'username': user.username,
            'email': user.email,
            'firstname': user.firstName,
            'lastname': user.lastName
        })

def get_popular_films(request):
    if request.method == "GET":
        ia = IMDb()
        films = ia.get_popular100_movies()
        cleaned = []
        i = 0
        for film in films:
            cleaned.append({
                'rank': film['popular movies 100 rank'],
                'title': film['title']
            })
        return JsonResponse({
            'films': cleaned
        })

def search_movie(request):
    if request.method == "POST":
        ia = IMDb()
        POST = json.loads(request.body)
        name = POST['name']
        existingfilms = []
        matchedname = closest_matched_film(name)

        exist = False
        storedfilm = None
        for film in Film.objects.all():
            if film.name.lower() == matchedname.lower():
                storedfilm = film
                exist = True
                break
        if exist == True:
            film = storedfilm
            info = get_cached_film_info(film)
            set_recently_visited(request, name)
            if request.user.is_authenticated:
                flag = check_if_film_list(request, film.name)
                info['inUserList'] = flag
            else:
                info['inUserList'] = False
            return JsonResponse(info)

        else:
            search = ia.search_movie(name)
            id = search[0].movieID
            filmname = ia.get_movie(id)['title']
            temp = None
            for i in range(len(filmname)):
                if i+1 != None:
                    if filmname[i] in string.punctuation and filmname[i+1] != " ":
                        temp = filmname[:i+1] + " " + filmname[i+1:]
                    
                    if temp == None:
                        temp = filmname

            filmnameNoPunc = temp.translate(str.maketrans('','', string.punctuation))
            film = get_movie(id, filmnameNoPunc)
            stream_avail = get_streaming_availability(filmname)
            reviews = get_user_reviews(filmname.lower())
            trailer = get_trailer(filmnameNoPunc)
            meta = film['meta_reviews']
            meta_user = film['meta_user_reviews']
            film['trailer'] = f"https://www.youtube.com/embed/{trailer['items'][0]['id']['videoId']}"
            film.pop('meta_reviews')
            film.pop('meta_user_reviews')
            save_film(film)
            set_recently_visited(request, filmname)
            recentreviews = get_recent_reviews(filmnameNoPunc, meta, meta_user, film['year'])

            return JsonResponse({
                'film': film,
                'reviews': reviews,
                "recentreviews": recentreviews,
                'streaming': stream_avail,
                'inUserList': False
            })

def closest_matched_film(name):
    if len(Film.objects.all()) != 0:
            existingfilms = []
            for film in Film.objects.all():
                existingfilms.append(film.name)
            closest = difflib.get_close_matches(name, existingfilms, cutoff=0.6)
            if len(closest) > 0:
                return closest[0]
            else:
                return "a"
    else:
        return "a"

def set_recently_visited(request, name):
    temp = None
    for film in Film.objects.all():
        if film.name.lower() == name.lower():
            temp = film
            break
    
    flag = False
    for recent in RecentlyVisited.objects.all():
            if recent.film.name.lower() == temp.name.lower():
                if request.user.is_authenticated:
                    recent.usersVisited.add(Account.objects.get(username=request.user.username))
                recent.recentDate = datetime.now()
                flag = True
                return JsonResponse({
                    'film': recent.film.to_dict(),
                    'usersVisited': recent.get_users(),
                    'recentDate': recent.recentDate
                })
    
    if flag == False:
        recent = RecentlyVisited()
        recent.film = temp
        recent.recentDate = datetime.now()
        recent.save()
        if request.user.is_authenticated:
            recent.usersVisited.add(Account.objects.get(username=request.user.username))
        
        return JsonResponse({
            'film': recent.film.to_dict(),
            'usersSaved': recent.get_users(),
            'recentDate': recent.recentDate
        })
        

def get_trailer(name):
    # API information
    api_service_name = "youtube"
    api_version = "v3"
    # API key
    DEVELOPER_KEY = "AIzaSyA3oAhIdurh3PAl1YHuqIvasrokvELbVRw"

    youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey = DEVELOPER_KEY)

    request = youtube.search().list(
        part = "snippet",
        maxResults = 1,
        q = f"{name} trailer"
    )
    response = request.execute()

    return response


def save_film(film):
    time = datetime.now()
    cached = datetime.strftime(time, '%Y-%m-%d')
    people = {
        'cast': [],
        'directors': []
    }
    for i in range(len(film['cast'])):
        people['cast'].append(film['cast'][i])
    for i in range(len(film['directors'])):
        people['directors'].append(film['directors'][i])
    
    cachefilm = Film()

    cachefilm.name = film['name']
    cachefilm.poster = film['poster']
    cachefilm.avgscore = film['avgScore']
    cachefilm.avgcriticscore = film['avgCriticScore']
    cachefilm.avguserscore = film['avgUserScore']
    cachefilm.metascore = film['scores']['meta_critic']
    cachefilm.metauserscore = film['scores']['meta_user']
    cachefilm.rtcriticscore = film['scores']['rt_critic']
    cachefilm.rtaudiencescore = film['scores']['rt_audience']
    cachefilm.imdbscore = film['scores']['imdb']
    cachefilm.trailer = film['trailer']
    cachefilm.consensus = film['consensus']
    cachefilm.filminfo = film['filminfo']
    cachefilm.year = film['year']
    cachefilm.people = people
    cachefilm.cached = cached

    cachefilm.save()


def get_cached_film_info(tempfilm):
    scores = {
        'meta_critic': tempfilm.metascore,
        'meta_user': tempfilm.metauserscore,
        'rt_critic': tempfilm.rtcriticscore,
        'rt_audience': tempfilm.rtaudiencescore,
        'imdb': tempfilm.imdbscore
    }

    cast = []
    directors = []

    for person in tempfilm.people['cast']:
        cast.append(person)

    for person in tempfilm.people['directors']:
        directors.append(person) 

    film = {
        'name': tempfilm.name,
        'avgScore': tempfilm.avgscore,
        'avgUserScore': tempfilm.avguserscore,
        'avgCriticScore': tempfilm.avgcriticscore,
        'scores': scores,
        'cast': cast,
        'directors': directors,
        'poster': tempfilm.poster,
        'consensus': tempfilm.consensus,
        'filminfo': tempfilm.filminfo,
        'trailer': tempfilm.trailer
    }

    stream_avail = get_streaming_availability(tempfilm.name)
    reviews = get_user_reviews(tempfilm.name.lower())
    recentreviews = get_cached_recent(tempfilm.name)

    return {
        'film': film,
        'reviews': reviews,
        'recentreviews': recentreviews,
        'streaming': stream_avail
    }

def check_if_film_list(request, name):
    temp = None
    for film in SavedFilm.objects.all():
        if film.film.name.lower() == name.lower():
            temp = film
            break

    if temp == None:
        return False
    else:
        users = temp.get_users()
        
        for user in users:
            if user == request.user.username:
                return True
        return False

def get_updated_list(request):
    if request.method == "GET":
        return JsonResponse({
            'inUserList': True
        })

def get_movie(filmid, name):
    ia = IMDb()

    movie = ia.get_movie(filmid)
    year = movie['year']
    cast = []
    directors = []
    genres = []
    scores = {}
    metaapi = get_metacritic_scores(name)

    rtapi = MovieScraper(movie_title=movie['localized title'])
    rtapi.extract_metadata()
    time.sleep(2)

    for actor in movie['cast']:
        cast.append(actor['name'])
    
    for director in movie['directors']:
        directors.append(director['name'])
    
    for genre in movie['genres']:
        genres.append(genre)
    
    age = "N/A"
    for i in range(len(movie['certificates'])):
        if "United Kingdom" in movie['certificates'][i]:
            if "(DVD rating)" in movie['certificates'][i]:
                pass
            else:
                age = movie['certificates'][i].strip('United Kingdom:')
    
    scores['rt_critic'] = rtapi.metadata['Score_Rotten']
    scores['rt_audience'] = rtapi.metadata['Score_Audience']
    scores['imdb'] = movie['rating']
    avgScore = 0
    avgUserScore = 0
    avgCriticScore = 0
    i = 0

    try:
        scores['meta_user'] = metaapi['userScore'] / 10
    except KeyError:
        scores['meta_user'] = 0
             
    try:
        scores['meta_critic'] = metaapi['metaScore'] / 10
    except KeyError:
        scores['meta_critic'] = 0

    if scores['rt_critic'] == '':
        scores['rt_critic'] = 0
    if scores['rt_audience'] == '':
        scores['rt_audience'] = 0

    avgUserScore = int(float(scores['meta_user']*10) + int(scores['rt_audience']) + float(scores['imdb']*10)) / 3
    avgCriticScore = int(int(scores['meta_critic']) + int(scores['rt_critic'])) / 2

    for value in scores.values():
        if isinstance(value, float):
            avgScore += int(float(value)*10)
        else:
            avgScore += int(value)
        i += 1
    
    avgScore = avgScore / i

    if avgUserScore >= 70 and avgCriticScore >= 70:
        consensus = "This film is a hit for both fans and critics alike! You should definitely watch it!"
    elif avgUserScore >= 70 and avgCriticScore < 70:
        consensus = "The fans love it! Can't really say the same for the critics though...."
    elif avgUserScore < 70 and avgCriticScore >= 70:
        consensus = "The critics enjoyed the film! However the views of the general publics don't really match it...."
    elif (avgUserScore >= 50 and avgUserScore < 70) and (avgCriticScore >= 50 and avgCriticScore < 70):
        consensus = "The film had mixed views by both the public and critics, make sure if the film is your type of bread before you watch it...."
    else:
        consensus = "Both the sides don't like this film! Maybe you should think twice about seeing this film....."

    filmdetails = {
        'name': movie['title'],
        'avgScore': round(avgScore),
        'avgUserScore': round(avgUserScore),
        'avgCriticScore': round(avgCriticScore),
        'scores': scores,
        'year': year,
        'cast': cast,
        'directors': directors,
        'poster': movie['full-size cover url'],
        'consensus': consensus,
        'filminfo': {
            'plot': movie['plot'][0],
            'genres': genres,
            'boxoffice': movie['box office']['Cumulative Worldwide Gross'],
            'languages': movie['languages'],
            'firstrelease': movie['original air date'],
            'countriesfilmed': movie['countries'],
            'runtime': movie['runtimes'][0],
            'agerating': age
        },
        'meta_reviews': metaapi['recentReviews'],
        'meta_user_reviews': metaapi['recentUserReviews']
    }

    return filmdetails

def get_user_reviews(name):
    reviews = []
    for review in AppReview.objects.all():
        if review.film.name.lower() == name.lower():
            temp = review.to_dict()
            reviews.append(temp)
    
    return reviews

def get_updated_user_reviews(request):
    if request.method == "POST":
        POST = json.loads(request.body)
        name = POST['film'].lower()
        reviews = get_user_reviews(name)
        return JsonResponse({"reviews": reviews})

def post_review(request):
    if request.method == "POST":
        review = AppReview()
        POST = json.loads(request.body)
        review.title = POST['title']
        review.rating = POST['rating']
        review.description = POST['description']
        review.reviewDate = POST['date']
        review.reviewer = Account.objects.get(username=POST['reviewer'])
        temp = None
        for film in Film.objects.all():
            if film.name.lower() == POST['film'].lower():
                temp = film
        review.film = temp

        review.save()

        return JsonResponse({
            'title': review.title,
            'rating': review.rating,
            'description': review.description,
            'reviewer': review.reviewer.username,
            'reviewDate':review.reviewDate,
            'film': review.film.name
        })

def add_to_saved_films(request):
    if request.method == "POST":
        temp = None
        POST = json.loads(request.body)
        name = POST['name']
        for film in Film.objects.all():
            if film.name.lower() == name.lower():
                temp = film
                break
        
        flag = False
        for film in SavedFilm.objects.all():
            if film.film.name.lower() == temp.name.lower():
                film.userSaved.add(Account.objects.get(username=POST['username']))
                flag = True
                return JsonResponse({
                    'film': film.film.to_dict(),
                    'users': film.get_users()
                })
        
        if flag == False:
            savedfilm = SavedFilm()
            savedfilm.film = temp
            savedfilm.save()
            savedfilm.userSaved.add(Account.objects.get(username=POST['username']))
        
        return JsonResponse({
            'film': savedfilm.film.to_dict(),
            'usersSaved': savedfilm.get_users()
        })

def remove_from_saved_films(request):
    if request.method == "DELETE":
        DELETE = json.loads(request.body)
        name = DELETE['name']
        
        for film in SavedFilm.objects.all():
            if film.film.name.lower() == name.lower():
                film.userSaved.remove(Account.objects.get(username=DELETE['username']))
                return JsonResponse({
                    'film': film.film.to_dict(),
                    'users': film.get_users(),
                    'inUserList': False
                })

def get_recent_reviews(name, meta, metauser, year):
    rtreviews = get_recent_rt_reviews(name, year)

    rt = rtreviews['recentReviews']
    rtuser = rtreviews['recentUserReviews']

    recentrev = RecentReviews()
    recentrev.rtcritic = rt
    recentrev.rtuser = rtuser
    recentrev.metauser = meta
    recentrev.metacritic = metauser

    temp = None
    for film in Film.objects.all():
            if film.name.lower() == name.lower():
                temp = film
                break

    recentrev.film = temp

    recentrev.save()

    return {
        "meta_critic": meta,
        "meta_user": metauser,
        "rt_critic": rt,
        "rt_user": rtuser
    }


def get_streaming_availability(name):
    url = "https://watchmode.p.rapidapi.com/search/"

    querystring = {
        "search_field": "name",
        "search_value":name
    }

    headers = {
        'x-rapidapi-host': "watchmode.p.rapidapi.com",
        'x-rapidapi-key': "80fb906771mshb7adef84037faf5p1c2d1fjsn193b151cfb14"
        }

    response = requests.request("GET", url, headers=headers, params=querystring)

    details = json.loads(response.text)

    film = details["title_results"]

    id = film[0]['id']

    url = f"https://watchmode.p.rapidapi.com/title/{id}/sources/"

    headers = {
        'regions': "GB",
        'x-rapidapi-host': "watchmode.p.rapidapi.com",
        'x-rapidapi-key': "80fb906771mshb7adef84037faf5p1c2d1fjsn193b151cfb14"
        }

    response = requests.request("GET", url, headers=headers)

    service = json.loads(response.text)

    arr = service

    filtered = []

    for i in range(len(arr)):
        if arr[i]['type'] == "sub":
            if "netflix" in arr[i]['web_url']:
                arr[i]['service'] = "Netflix"
                filtered.append(arr[i])
            if "disneyplus" in arr[i]['web_url']:
                arr[i]['service'] = "Disney+"
                filtered.append(arr[i])
            if "amazon" in arr[i]['web_url']:
                arr[i]['service'] = "Prime Video"
                filtered.append(arr[i])
            

    return filtered

def get_metacritic_scores(name):
    namelow = name.lower()
    formatted = namelow.replace(" ", "-")

    url = f"https://metacriticapi.p.rapidapi.com/movies/{formatted}"

    querystring = {"reviews":"true"}

    headers = {
        "X-RapidAPI-Host": "metacriticapi.p.rapidapi.com",
        "X-RapidAPI-Key": "80fb906771mshb7adef84037faf5p1c2d1fjsn193b151cfb14"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    res = json.loads(response.text)

    return res

def get_recent_rt_reviews(name, year):
    namelow = name.lower()
    formatted = namelow.replace(" ", "_")
    id = 0

    result = requests.get(f"https://www.rottentomatoes.com/m/{formatted}/")

    if len(re.findall(r'(?<=rtId":")(.*)(?=","type)',result.text)) == 0:
        time.sleep(2)
        formatted = f"{formatted}_{year}"
        result = requests.get(f"https://www.rottentomatoes.com/m/{formatted}/")
        id = re.findall(r'(?<=rtId":")(.*)(?=","type)',result.text)[0]

    else:
        time.sleep(2)
        id = re.findall(r'(?<=rtId":")(.*)(?=","type)',result.text)[0]

    time.sleep(2)

    r = requests.get(url=f"https://api.flixster.com/android/api/v2/movies/{id}.json")
    r.raise_for_status()

    a = r.json()

    reviews = {
        "recentReviews": [],
        "recentUserReviews": []
    }

    for i in range(6):
        try:
            reviews['recentReviews'].append(a['reviews']['critics'][i])
        except IndexError:
            pass

        try:
            reviews['recentUserReviews'].append(a['reviews']['recent'][i])
        except IndexError:
            pass
        
    if len(reviews['recentReviews']) == 0:
        reviews['recentReviews'].append("N/A")
    if len(reviews['recentUserReviews']) == 0:
        reviews['recentUserReviews'].append("N/A")
    
    return reviews

def get_cached_recent(name):
    temp = None
    for rev in RecentReviews.objects.all():
            if rev.film.name.lower() == name.lower():
                temp = rev
                break
    
    return {
        "meta_critic": temp.metacritic,
        "meta_user": temp.metauser,
        "rt_critic": temp.rtcritic,
        "rt_user": temp.rtuser
    }