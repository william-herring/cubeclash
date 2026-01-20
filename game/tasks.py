import redis
import json
from celery import shared_task
from django.conf import settings

from .models import Battle

r = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

@shared_task
def join_battle_queue(user_id, elo, battle_type):
    matchmaking_queue_name = f'{battle_type}_matchmaking_queue'

    user = json.dumps({
        'user_id': user_id,
        'elo': elo,
    })

    r.rpush(matchmaking_queue_name, user)

    if r.llen(matchmaking_queue_name) >= 2:
        matchmaking_queue = r.lrange(matchmaking_queue_name, 0, -1)
        deserialized_matchmaking_queue = [json.loads(user) for user in matchmaking_queue]
        sorted_matchmaking_queue = sorted(deserialized_matchmaking_queue, key=lambda k: k['elo'])
        matchmaking_queue = [json.dumps(user) for user in sorted_matchmaking_queue]

        with r.pipeline() as pipe:
            pipe.delete(matchmaking_queue_name)
            pipe.rpush(matchmaking_queue_name, *matchmaking_queue)
            pipe.execute()

@shared_task
def find_battles(battle_type):
    matchmaking_queue_name = f'{battle_type}_matchmaking_queue'

    while r.llen('matchmaking_queue') >= 2:
        user1 = json.loads(r.rpop(matchmaking_queue_name))['user_id']
        user2 = json.loads(r.rpop(matchmaking_queue_name))['user_id']

        battle = Battle(
            type=battle_type,
            user1=user1,
            user2=user2,
        )
        battle.save()

        return battle
    return None
