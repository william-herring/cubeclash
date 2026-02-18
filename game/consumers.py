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

        # EXAMPLE POSITIONAL ID "bo5-1000-4" where user 4 is queuing for a bo5 match within the 1000-2000 ELO catchment

        async_to_sync(self.channel_layer.group_add)(self.position_id, self.channel_name)

        self.accept()

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event = data['event']

        self.handle_event(event)

    def handle_event(self, event):
        if event == 'matchmaking.ready':
            matchmaking_result = find_battles.delay(self.elo_catchment, self.battle_type).get()

            if type(matchmaking_result) == dict:
                async_to_sync(self.channel_layer.group_send)(
                    self.position_id, {'type': 'matchmaking.alert', 'message': json.dumps(matchmaking_result)}
                )
            else:
                deserialized_result = serializers.deserialize('json', matchmaking_result)
                for deserialized_battle in deserialized_result:
                    battle = deserialized_battle.object

                    async_to_sync(self.channel_layer.group_send)(
                        f'{battle.battle_type}-{battle.competitor_1}', {
                            'type': 'matchmaking.alert',
                            'message': json.dumps({
                                'status': 'success',
                                'battle_id': str(battle.pk),
                        })}
                    )

                    async_to_sync(self.channel_layer.group_send)(
                        f'{battle.battle_type}-{battle.competitor_2}', {
                            'type': 'matchmaking.alert',
                            'message': json.dumps({
                                'status': 'success',
                                'battle_id': str(battle.pk),
                        })}
                    )

                    self.close()

        elif event == 'matchmaking.exit_queue':
            pass #TODO exit queue

    def matchmaking_alert(self, event):
        message = event['message']
        self.send(text_data=json.dumps({'message': message}))


class BattleConsumer(SyncConsumer):
    def websocket_connect(self):
        pass

    def websocket_receive(self, event):
        pass
