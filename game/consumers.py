import json
from django.core import serializers
from asgiref.sync import async_to_sync
from channels.consumer import SyncConsumer
from channels.generic.websocket import WebsocketConsumer
from .tasks import find_battles


class MatchmakingConsumer(WebsocketConsumer):
    def connect(self):
        position_id = self.scope['url_route']['kwargs'].get('position_id')

        self.position_id = position_id
        self.battle_type = position_id.split('-')[0]
        self.elo_catchment = position_id.split('-')[1]
        self.user_id = position_id.split('-')[2]

        self.queue_group_name = f'matchmaking_{self.battle_type}_{self.elo_catchment}'

        async_to_sync(self.channel_layer.group_add)(self.queue_group_name, self.channel_name)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event = data['event']

        self.handle_event(event)

    def handle_event(self, event):
        if event == 'matchmaking.ready':
            find_battles.delay(self.elo_catchment, self.battle_type)

        elif event == 'matchmaking.exit_queue':
            pass #TODO exit queue

    def matchmaking_alert(self, event):
        message = event['message']
        print(message)
        self.send(text_data=json.dumps({'message': message}))


class BattleConsumer(SyncConsumer):
    def websocket_connect(self):
        pass

    def websocket_receive(self, event):
        pass
