import json
from channels.consumer import SyncConsumer

class MatchmakingConsumer(SyncConsumer):
    def websocket_connect(self):
        self.accept()

    def websocket_receive(self, event):
        message = event['message']

        self.send(({
            'message': message
        }))