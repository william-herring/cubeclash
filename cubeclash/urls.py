from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect
import users.views

urlpatterns = [
    path('', lambda request : redirect('/battle') if request.user.is_authenticated else redirect('/login')),
    path('admin/', admin.site.urls),
    path('users/',include('users.urls')),
    path('battle', include('game.urls')),
    path('login', users.views.LoginView.as_view()),
    path('account-redirect', users.views.AuthRedirectView.as_view()),
]
