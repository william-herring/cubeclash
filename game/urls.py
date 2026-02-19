from django.urls import path
from .views import *

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('join/', JoinBattleView.as_view(), name='join'),
]