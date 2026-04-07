import redis
import json
import math
from celery import shared_task
from django.conf import settings
from django.core import serializers

from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from .constants import SET_WIN_CONDITIONS, BATTLE_WIN_CONDITIONS
from .elo import update_rating
from .models import Battle, Set
from .utils import init_set, get_scramble

r = redis.StrictRedis.from_url(settings.CELERY_BROKER_URL)

@shared_task
def join_battle_queue(user_id, elo, battle_type):
    elo_catchment = int(math.floor(elo / 1000) * 1000) # ELO catchments increment by 1000

    matchmaking_queue_name = f'{battle_type}_{elo_catchment}_matchmaking_queue'
    currently_queued_users = r.lrange('queued_users', 0, -1)

    if bytes(str(user_id), 'ascii') in currently_queued_users:
        return {
            'status': 'already_queued',
        }

    user = json.dumps({
        'user_id': user_id,
        'elo': elo,
    })

    r.rpush('queued_users', user_id)
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
        'status': 'joined_queue',
        'position_id': position_id,
    }

@shared_task
def leave_battle_queue(user_id, elo, battle_type):
    elo_catchment = int(math.floor(elo / 1000) * 1000)

    matchmaking_queue_name = f'{battle_type}_{elo_catchment}_matchmaking_queue'
    user = json.dumps({
        'user_id': user_id,
        'elo': elo,
    })

    r.lrem('queued_users', 0, user_id)
    r.lrem(matchmaking_queue_name, 0, user)

    return {
        'status': 'left_queue'
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

        set_obj = init_set(battle)
        set_obj.battle = battle
        set_obj.save()

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

        r.rpop('queued_users', user1)
        r.rpop('queued_users', user2)

    r.set(f'{matchmaking_queue_name}:status', 'inactive')

    return result

@shared_task
def submit_time(battle_id, competitor_number: int, time: float):
    battle = Battle.objects.get(pk=battle_id)
    set_obj = battle.sets.all().last()
    competitor_1_results = set_obj.competitor_1_results
    competitor_2_results = set_obj.competitor_2_results
    channel_layer = get_channel_layer()
    battle_group_name = f'battle_{battle_id}'

    if competitor_number == 1:
        competitor_1_results += ';' + str(time)
        set_obj.competitor_1_results = competitor_1_results
    elif competitor_number == 2:
        competitor_2_results += ';' + str(time)
        set_obj.competitor_2_results = competitor_2_results
    set_obj.save()

    competitor_1_results_list = competitor_1_results.split(';')
    competitor_2_results_list = competitor_2_results.split(';')
    if len(competitor_1_results_list) == len(competitor_2_results_list):
        if abs(float(competitor_1_results_list[-1])) == abs(float(competitor_2_results_list[-1])):
            pass
        elif float(competitor_1_results_list[-1]) != -1 and (abs(float(competitor_1_results_list[-1])) < abs(float(competitor_2_results_list[-1])) or float(competitor_2_results_list[-1]) == -1):
            set_obj.competitor_1_score = set_obj.competitor_1_score + 1
        else:
            set_obj.competitor_2_score = set_obj.competitor_2_score + 1

        async_to_sync(channel_layer.group_send)(
            battle_group_name, {'type': 'battle.message', 'message': json.dumps({
                'detail': 'score_update',
                'competitor_1_latest_result': float(competitor_1_results_list[-1]),
                'competitor_2_latest_result': float(competitor_2_results_list[-1]),
                'competitor_1_score': set_obj.competitor_1_score,
                'competitor_2_score': set_obj.competitor_2_score,
            })}
        )

        set_has_been_won = SET_WIN_CONDITIONS[set_obj.set_type](set_obj.competitor_1_score, set_obj.competitor_2_score)
        if set_has_been_won:
            if set_obj.competitor_1_score > set_obj.competitor_2_score:
                battle.competitor_1_sets += 1
            else:
                battle.competitor_2_sets += 1

            winner = None
            battle_has_been_won = BATTLE_WIN_CONDITIONS[battle.battle_type](battle.competitor_1_sets, battle.competitor_2_sets)
            if battle_has_been_won:
                if battle.competitor_1_sets > battle.competitor_2_sets:
                    winner = 'competitor_1'
                    battle.winner = battle.competitor_1

                    battle.competitor_1.previous_elo = battle.competitor_1.elo
                    battle.competitor_1.elo = update_rating(battle.competitor_1.elo, battle.competitor_2.elo, 1)
                    battle.competitor_2.previous_elo = battle.competitor_2.elo
                    battle.competitor_2.elo = update_rating(battle.competitor_2.elo, battle.competitor_1.elo, 0)
                    battle.competitor_1.save()
                    battle.competitor_2.save()
                else:
                    winner = 'competitor_2'
                    battle.winner = battle.competitor_2

                    battle.competitor_1.previous_elo = battle.competitor_1.elo
                    battle.competitor_1.elo = update_rating(battle.competitor_1.elo, battle.competitor_2.elo, 0)
                    battle.competitor_2.previous_elo = battle.competitor_2.elo
                    battle.competitor_2.elo = update_rating(battle.competitor_2.elo, battle.competitor_1.elo, 1)
                    battle.competitor_1.save()
                    battle.competitor_2.save()
            else:
                set_obj = init_set(battle)
                set_obj.battle = battle
                set_obj.save()
            battle.save()

            async_to_sync(channel_layer.group_send)(
                battle_group_name, {'type': 'battle.message', 'message': json.dumps({
                    'detail': 'set_finished',
                    'battle_winner': winner,
                    'competitor_1_sets': battle.competitor_1_sets,
                    'competitor_2_sets': battle.competitor_2_sets,
                })}
            )

            if winner:
                return

        new_scramble = get_scramble()
        scramble_set = set_obj.scramble_set
        scramble_set += ';' + new_scramble
        set_obj.scramble_set = scramble_set
        async_to_sync(channel_layer.group_send)(
            battle_group_name, {'type': 'battle.message', 'message': json.dumps({
                'detail': 'scramble',
                'scramble': new_scramble,
            })}
        )

    set_obj.save()
