import redis
import json
import math
from celery import shared_task
from django.conf import settings
from django.core import serializers

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .models import Battle

r = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

@shared_task
def join_battle_queue(user_id, elo, battle_type):
    elo_catchment = int(math.floor(elo / 1000) * 1000) # ELO catchments increment by 1000

    matchmaking_queue_name = f'{battle_type}_{elo_catchment}_matchmaking_queue'

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

    position_id = f'{battle_type}-{elo_catchment}-{user_id}'

    return {
        'status': 'joined',
        'position_id': position_id,
    }

@shared_task
def find_battles(elo_catchment, battle_type):
    matchmaking_queue_name = f'{battle_type}_{elo_catchment}_matchmaking_queue'
    queue_group_name = f'matchmaking_{battle_type}_{elo_catchment}'
    channel_layer = get_channel_layer()

    if r.get(f'{matchmaking_queue_name}:status') == 'active':
        result = {
            'status': 'loop_already_initiated'
        }
        async_to_sync(channel_layer.group_send)(
            queue_group_name, {'type': 'matchmaking.alert', 'message': json.dumps(result)}
        )
        return result

    if r.llen(matchmaking_queue_name) < 2:
        result = {
            'status': 'queue_empty'
        }
        async_to_sync(channel_layer.group_send)(
            queue_group_name, {'type': 'matchmaking.alert', 'message': json.dumps(result)}
        )
        return result


    battle_list = []
    result = []

    while r.llen(matchmaking_queue_name) >= 2:
        r.set(f'{matchmaking_queue_name}:status', 'active')
        user2 = json.loads(r.rpop(matchmaking_queue_name))['user_id']
        user1 = json.loads(r.rpop(matchmaking_queue_name))['user_id']

        battle = Battle(
            battle_type=battle_type,
            competitor_1_id=user1,
            competitor_2_id=user2,
        )
        battle.save()

        battle_list.append(battle)
        result = serializers.serialize('json', battle_list, fields=['battle_type', 'competitor_1', 'competitor_2'])
        async_to_sync(channel_layer.group_send)(
            queue_group_name, {
                'type': 'matchmaking.alert',
                'message': json.dumps({
                    'status': 'success',
                    'battle_id': str(battle.pk),
                })}
        )

    r.set(f'{matchmaking_queue_name}:status', 'inactive')

    return result
