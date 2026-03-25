from django.urls import path
from .views import *

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('b/<str:pk>/', BattleView.as_view(), name='battle'),
    path('join/', JoinBattleView.as_view(), name='join'),
    path('create/', CreateBattleView.as_view(), name='create'),
]