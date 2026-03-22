import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
from .tasks import find_battles, submit_time


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
        self.send(text_data=json.dumps({'message': message}))


class BattleConsumer(WebsocketConsumer):
    def connect(self):
        self.battle_id = self.scope['url_route']['kwargs'].get('battle_id')
        self.battle_group_name = f'battle_{self.battle_id}'

        async_to_sync(self.channel_layer.group_add)(self.battle_group_name, self.channel_name)

        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(self.battle_group_name, self.channel_name)

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        event = data['event']
        message = data['message']

        self.handle_event(event, message)

    def handle_event(self, event, message):
        match event:
            case 'battle.join':
                async_to_sync(self.channel_layer.group_send)(self.battle_group_name, {
                    'type': 'battle.message', 'message': json.dumps({
                        'detail': 'competitor_joined',
                        'competitor_number': message['competitor_number'],
                        # Should issue match/set score and all relevant solve details in case of reconnection
                    }),
                })
            case 'battle.submit':
                submission_data = json.loads(message)
                set_id = int(submission_data['set_id'])

                competitor_number = int(submission_data['competitor_number'])
                time = float(submission_data['time'])

                submit_time.delay(self.battle_id, set_id, competitor_number, time)

    def battle_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps({'message': message}))
