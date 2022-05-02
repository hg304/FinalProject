import json
import time
from markupsafe import re
import requests
import googleapiclient.discovery
import difflib
import string

from django.contrib.auth.hashers import check_password, make_password
from django.utils import timezone
from imdb import IMDb
from rotten_tomatoes_scraper.rt_scraper import MovieScraper
from django.http import HttpResponseBadRequest, JsonResponse
from .models import AppReview, Account, Film, OnlineCriticandUserReviews, RecentlyVisited, SavedFilm, OnlineCriticandUserReviews

"""
    Method that changes the password of the currently logged in user
"""
def change_password(request):
    if request.method == "POST":
        PUT = json.loads(request.body)
        if check_password(PUT['currentpass'], request.user.password):
            if PUT['newpass1'] == PUT['newpass2']:
                for user in Account.objects.all():
                    if request.user.username == user.username:
                        user.password = make_password(PUT['newpass1'])
                        user.save()
                        return JsonResponse({})
        return HttpResponseBadRequest

"""
    Method that changes information about the currently logged in user
"""
def change_details(request):
    if request.method == "POST":
        PUT = json.loads(request.body)
        user = None
        for temp in Account.objects.all():
            if temp.username == request.user.username:
                user = temp
                break
        
        if PUT['username'] != None:
            user.username = PUT['username']
        if PUT['email'] != None:
            user.email = PUT['email']
        if PUT['firstname'] != None:
            user.firstName = PUT['firstname']
        if PUT['lastname'] != None:
            user.lastName = PUT['lastname']
        
        user.save()
        
        return JsonResponse({
            'username': user.username,
            'email': user.email,
            'firstname': user.firstName,
            'lastname': user.lastName
        })

"""
    Method that pulls the current top 100 movies online
"""
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

"""
    Method that searches for a film entered by the user and sends the 
    film information back to the user
"""
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
            if request.user.is_authenticated:
                flag = check_if_film_list(request, film.name)
                info['inUserList'] = flag
            else:
                info['inUserList'] = False
            set_recently_visited(request, film.name)
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
            stream_avail = get_streaming_availability(id)
            reviews = get_user_reviews(filmname.lower())
            trailer = get_trailer(filmnameNoPunc)
            meta = film['meta_reviews']
            meta_user = film['meta_user_reviews']
            film['trailer'] = f"https://www.youtube.com/embed/{trailer['items'][0]['id']['videoId']}"
            film.pop('meta_reviews')
            film.pop('meta_user_reviews')
            save_film(film)
            set_recently_visited(request, filmname)
            recentreviews = get_recent_reviews(filmname, filmnameNoPunc, meta, meta_user, film['year'])

            return JsonResponse({
                'film': film,
                'reviews': reviews,
                "recentreviews": recentreviews,
                'streaming': stream_avail,
                'inUserList': False
            })

"""
    Method that takes the inputted word from user and matches the closest
    related film to the name
"""
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

"""
    Method that saves a film as the most recently visited film by a user
"""
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
                recent.recentDate = timezone.now()
                recent.save()
                flag = True
                return JsonResponse({
                    'film': recent.film.to_dict(),
                    'usersVisited': recent.get_users(),
                    'recentDate': recent.recentDate
                })
    
    if flag == False:
        recent = RecentlyVisited()
        recent.film = temp
        recent.recentDate = timezone.now()
        recent.save()
        if request.user.is_authenticated:
            recent.usersVisited.add(Account.objects.get(username=request.user.username))
        
        return JsonResponse({
            'film': recent.film.to_dict(),
            'usersSaved': recent.get_users(),
            'recentDate': recent.recentDate
        })
        
"""
    Method that pulls the trailer of the searched film if being searched 
    for the first time
"""
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

"""
    Method that caches the full information about a film in the database
    when searched the first time so that it can be loaded faster when 
    searched again
"""
def save_film(film):
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
    cachefilm.imdbid = film['imdbid']
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

    cachefilm.save()

"""
    Method that will pull the film info from the database if the searched film
    has been found in the database
"""
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
        'imdbid': tempfilm.imdbid,
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

    stream_avail = get_streaming_availability(tempfilm.imdbid)
    reviews = get_user_reviews(tempfilm.name.lower())
    recentreviews = get_cached_recent(tempfilm.name)

    return {
        'film': film,
        'reviews': reviews,
        'recentreviews': recentreviews,
        'streaming': stream_avail
    }

"""
    Method that checks to see if the film exists in the user's film
    list
"""
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

"""
    Method that returns the updated film list of the user after a film has
    either been added to the list or removed from the list
"""
def get_updated_list(request):
    if request.method == "GET":
        return JsonResponse({
            'inUserList': True
        })

"""
    Method that will pull the information for the film if it is being
    searched for the first time on the application 
"""
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
    try:
        for i in range(len(movie['certificates'])):
            if "United Kingdom" in movie['certificates'][i]:
                if "(DVD rating)" in movie['certificates'][i]:
                    pass
                else:
                    age = movie['certificates'][i].strip('United Kingdom:')
    except KeyError:
        pass
    
    boxoffice = "N/A"
    try:
        boxoffice = movie['box office']['Cumulative Worldwide Gross']
    except KeyError:
        pass

    scores['rt_critic'] = rtapi.metadata['Score_Rotten']
    scores['rt_audience'] = rtapi.metadata['Score_Audience']
    scores['imdb'] = movie['rating']
    avgScore = 0
    avgUserScore = 0
    avgCriticScore = 0
    i = 0

    try:
        scores['meta_user'] = metaapi['userScore'] / 10
    except (KeyError, TypeError) as e:
        scores['meta_user'] = 0
             
    try:
        scores['meta_critic'] = metaapi['metaScore']
    except (KeyError, TypeError) as e:
        scores['meta_critic'] = 0

    if scores['rt_critic'] == '':
        scores['rt_critic'] = 0
    if scores['rt_audience'] == '':
        scores['rt_audience'] = 0

    avgUserScore = int(float(scores['meta_user']*10) + int(scores['rt_audience']) + float(scores['imdb']*10)) / 3
    avgCriticScore = (int(scores['meta_critic']) + int(scores['rt_critic'])) / 2

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

    filmdetails = {}
    try:
        filmdetails = {
            'name': movie['title'],
            'imdbid': filmid,
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
                'boxoffice': boxoffice,
                'languages': movie['languages'],
                'firstrelease': movie['original air date'],
                'countriesfilmed': movie['countries'],
                'runtime': movie['runtimes'][0],
                'agerating': age
            },
            'meta_reviews': metaapi['recentReviews'],
            'meta_user_reviews': metaapi['recentUserReviews']
        }
    except KeyError:
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
            'meta_reviews': [],
            'meta_user_reviews': []
        }

    return filmdetails

"""
    Method that will pull the reviews that were posted by users
    in the application
"""
def get_user_reviews(name):
    reviews = []
    for review in AppReview.objects.all():
        if review.film.name.lower() == name.lower():
            temp = review.to_dict()
            reviews.append(temp)
    
    return reviews

"""
    Method that will return the updated list of user reviews for a 
    film after a review has been posted for it
"""
def get_updated_user_reviews(request):
    if request.method == "POST":
        POST = json.loads(request.body)
        name = POST['film'].lower()
        reviews = get_user_reviews(name)
        return JsonResponse({"reviews": reviews})

"""
    Method that will post the review that has been entered by the user
    in the application to the database for that film
"""
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

"""
    Method to add a chosen film to a user's film list
"""
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

"""
    Method to remove a chosen film from a user's film list
"""
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

"""
    Method that will pull the recent reviews for both critic and audience from 
    different sources for the chosen film
"""
def get_recent_reviews(name, nameNoPunc, meta, metauser, year):
    rtreviews = get_recent_rt_reviews(nameNoPunc, year)

    rt = rtreviews['recentReviews']
    rtuser = rtreviews['recentUserReviews']

    recentrev = OnlineCriticandUserReviews()
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

"""
    Method that will pull the streaming service availability for a chosen
    film
"""
def get_streaming_availability(id):
    url = "https://streaming-availability.p.rapidapi.com/get/basic"

    querystring = {"country":"GB","imdb_id":f"tt{id}","output_language":"EN"}

    headers = {
        "X-RapidAPI-Host": "streaming-availability.p.rapidapi.com",
        "X-RapidAPI-Key": "80fb906771mshb7adef84037faf5p1c2d1fjsn193b151cfb14"
    }

    response = requests.request("GET", url, headers=headers, params=querystring)

    service = json.loads(response.text)

    filtered = []

    for stream in service['streamingInfo']:
        if stream == "disney":
            filtered.append({
                "service": "Disney+",
                "web_url": service['streamingInfo']['disney']['gb']['link']
            })
        elif stream == "netflix":
            filtered.append({
                "service": "Netflix",
                "web_url": service['streamingInfo']['netflix']['gb']['link']
            })
        elif stream == "prime":
            filtered.append({
                "service": "Amazon Prime",
                "web_url": service['streamingInfo']['prime']['gb']['link']
            })

    return filtered

"""
    Method that is focused on pulling the metacritic scores and reviews
    from both critics and audience for a chosen film
"""
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

"""
    Method focused on pulling the rotten tomatoes recent reviews of both
    critics and audience
"""
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

"""
    Method that will pull the cached reviews from other sources for the 
    chosen film
"""
def get_cached_recent(name):
    temp = None
    for rev in OnlineCriticandUserReviews.objects.all():
            if rev.film.name.lower() == name.lower():
                temp = rev
                break
    
    return {
        "meta_critic": temp.metacritic,
        "meta_user": temp.metauser,
        "rt_critic": temp.rtcritic,
        "rt_user": temp.rtuser
    }