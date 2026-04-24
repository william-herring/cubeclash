from django.urls import path
from .views import *

urlpatterns = [
    path('', DashboardView.as_view(), name='dashboard'),
    path('b/<str:pk>/', BattleView.as_view(), name='battle'),
    path('b/<str:pk>/details/', BattleOverviewView.as_view(), name='battle-details'),
    path('join/', JoinBattleView.as_view(), name='join'),
    path('cancel-matchmaking/', CancelMatchmakingView.as_view(), name='cancel-matchmaking'),
    path('create/', CreateBattleView.as_view(), name='create'),
]