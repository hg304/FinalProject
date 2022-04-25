from django.urls import path
from .views import home_view, film_view, selected_film_view, profile_view, top_films_view, login_view, signup_view, log_out
from .api import search_movie, get_updated_user_reviews, post_review, add_to_saved_films, remove_from_saved_films, get_updated_list, get_popular_films, change_password, change_details

urlpatterns = [
    path('', home_view, name="home"),
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('logout/', log_out, name="logout"),
    path('film/', film_view, name="filminfo"),
    path('profile/', profile_view, name="profile"),
    path('selectedfilm/<str:name>/', selected_film_view, name="selected"),
    path('topfilms/', top_films_view, name="topmovies"),
    path('api/changepassword/', change_password, name="changepass"),
    path('api/changeinfo/', change_details, name="changeinfo"),
    path('api/searchfilm/', search_movie, name="getinfo"),
    path('api/getreviewsupdated/', get_updated_user_reviews, name="getreviews"),
    path('api/postfilmreview/', post_review, name="postreview"),
    path('api/addtosavedfilms/', add_to_saved_films, name="addtosaved"),
    path('api/removefromsavedfilms/', remove_from_saved_films, name="removefromsaved"),
    path('api/getnewlist/', get_updated_list, name="getnewlist"),
    path('api/getpopularfilms/', get_popular_films, name="getpopularfilms")
]