from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .forms import SignUpForm
from .models import Account, AppReview, Film, SavedFilm, RecentReviews

class AccountAdmin(UserAdmin):
    form = SignUpForm
    model = Account
    list_display = ['username', 'email', 'firstName', 'lastName']

admin.site.register(Account, AccountAdmin)
admin.site.register(AppReview)
admin.site.register(Film)
admin.site.register(SavedFilm)
admin.site.register(RecentReviews)
