from django.urls import re_path
from . import consumers

"""
 Each queued user receives a positional identifier string which is used to track their matchmaking status
 in the queue. The user client will subscribe to a socket with the corresponding position_id, and this will
 notify the client when a battle has been found. This ensures that the user client can only receive battle connection
 data relating to their own matchmaking stream whilst also enabling the user to remove themselves from the matchmaking
 queue at any point.
"""

websocket_urlpatterns = [
    re_path(r"^ws/matchmaking/(?P<position_id>[^/]+)/$", consumers.MatchmakingConsumer.as_asgi()),
    re_path(r"ws/battle/(?P<battle_id>\w+)/$", consumers.BattleConsumer.as_asgi()),
]