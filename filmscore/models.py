from django.db import models
from django.contrib.auth.models import AbstractUser

"""
    Model representation of user accounts for the
    application
"""

class Account(AbstractUser):
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)

    def __str__(self):
        return self.username

    def to_dict(self):
        return {
            "username": self.username,
            "email": self.email,
            "firstName": self.firstName,
            "lastName": self.lastName
        }

"""
    Model representation of films that are cached in the system after
    being searched the first time
"""
class Film(models.Model):
    name = models.CharField(max_length=200, primary_key=True)
    imdbid = models.CharField(max_length=100)
    poster = models.CharField(max_length=1000)
    year = models.IntegerField()
    avgscore = models.IntegerField()
    avguserscore = models.IntegerField()
    avgcriticscore = models.IntegerField()
    metascore = models.IntegerField()
    metauserscore = models.FloatField()
    rtcriticscore = models.IntegerField()
    rtaudiencescore = models.IntegerField()
    imdbscore = models.FloatField()
    filminfo = models.JSONField()
    consensus = models.TextField()
    trailer = models.CharField(max_length=2000)
    people = models.JSONField()

    def to_dict(self):
        return {
            'name': self.name,
            'imdbid': self.imdbid,
            'poster': self.poster,
            'avgscore': self.avgscore,
            'metascore': self.metascore,
            'metauser': self.metauserscore,
            'year': self.year,
            'rtcriticscore': self.rtcriticscore,
            'rtaudiencescore': self.rtaudiencescore,
            'imdbscore': self.imdbscore,
            'consensus': self.consensus,
            'filminfo': self.filminfo,
            'trailer': self.trailer,
            'people': self.people
        }

"""
    Model representation of recent critic reviews from other sources that are cached
    for a given film when searched the first time
"""
class OnlineCriticandUserReviews(models.Model):
    rtcritic = models.JSONField()
    rtuser = models.JSONField()
    metauser = models.JSONField()
    metacritic = models.JSONField()
    film = models.ForeignKey(Film, to_field='name', on_delete=models.CASCADE)

    def to_dict(self):
        return {
            "recentrtcritic": self.rtcritic,
            "recentrtuser": self.rtuser,
            "recentmetacritic": self.metacritic,
            "recentmetauser": self.metauser,
            "film": self.film
        }

"""
    Model representation of reviews for a film that are posted on the application
"""
class AppReview(models.Model):
    title = models.CharField(max_length=200)
    rating = models.IntegerField()
    description = models.TextField()
    reviewDate = models.DateTimeField()
    reviewer = models.ForeignKey(Account, to_field='id', on_delete=models.CASCADE)
    film = models.ForeignKey(Film, to_field='name', on_delete=models.CASCADE)

    def __str__(self):
        return self.title

    def to_dict(self):
        return {
            'title': self.title,
            'rating': self.rating,
            'description': self.description,
            'date': self.reviewDate,
            'reviewer': self.reviewer.username,
            'film': self.film.name
        }


"""
    Model representation of a film that has been saved to a user's film list
"""
class SavedFilm(models.Model):
    film = models.ForeignKey(Film, to_field='name', on_delete=models.CASCADE)
    userSaved = models.ManyToManyField(Account)

    def get_users(self):
        if self.userSaved.all() == None:
            return []
        return [user.username for user in self.userSaved.all()]
    
    def to_dict(self):
        return {
            'film': self.film.name,
            'poster': self.film.poster,
            'score': self.film.avgscore,
            'userSaved': self.get_users()
        }

"""
    Model representation of the films that have been recently visited by the user
    for the first time
"""
class RecentlyVisited(models.Model):
    film = models.ForeignKey(Film, to_field="name", on_delete=models.CASCADE)
    usersVisited = models.ManyToManyField(Account)
    recentDate = models.DateTimeField()

    def get_users(self):
        if self.usersVisited.all() == None:
            return []
        return [user.username for user in self.usersVisited.all()]

    def to_dict(self):
        return {
            'film': self.film.name,
            'poster': self.film.poster,
            'score': self.film.avgscore,
            'usersVisited': self.get_users(),
            'recentDate': self.recentDate
        }

