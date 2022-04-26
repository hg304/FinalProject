from django.db import models
from django.contrib.auth.models import AbstractUser

class Account(AbstractUser):
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=50)
    lastName = models.CharField(max_length=50)

    def __str__(self):
        return self.username

class Film(models.Model):
    id = models.IntegerField(null=True)
    name = models.CharField(max_length=200, primary_key=True)
    poster = models.CharField(max_length=1000)
    avgscore = models.IntegerField()
    avguserscore = models.IntegerField()
    avgcriticscore = models.IntegerField()
    metascore = models.IntegerField()
    metauserscore = models.IntegerField()
    rtcriticscore = models.IntegerField()
    rtaudiencescore = models.IntegerField()
    imdbscore = models.IntegerField()
    consensus = models.TextField()
    plot = models.CharField(max_length=2000)
    trailer = models.CharField(max_length=2000)
    people = models.JSONField()
    cached = models.DateField()

    def to_dict(self):
        return {
            'name': self.name,
            'poster': self.poster,
            'avgscore': self.avgscore,
            'metascore': self.metascore,
            'metauser': self.metauserscore,
            'rtcriticscore': self.rtcriticscore,
            'rtaudiencescore': self.rtaudiencescore,
            'imdbscore': self.imdbscore,
            'consensus': self.consensus,
            'plot': self.plot,
            'trailer': self.trailer,
            'people': self.people,
            'cached': self.cached
        }

class RecentReviews(models.Model):
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


class AppReview(models.Model):
    title = models.CharField(max_length=200)
    rating = models.IntegerField()
    description = models.TextField()
    reviewDate = models.DateField()
    reviewer = models.ForeignKey(Account, to_field='username', on_delete=models.CASCADE)
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

