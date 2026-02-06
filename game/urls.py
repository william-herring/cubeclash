from django.urls import path
from .views import *

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('matchmaking/', MatchmakingView.as_view(), name='matchmaking'),
]