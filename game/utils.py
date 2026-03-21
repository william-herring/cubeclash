import subprocess
from django.conf import settings
from game.constants import BATTLE_FORMATS
from game.models import Battle, Set
from typing import Generator

def init_sets(battle: Battle) -> Generator[Set, None, None]:
    for i in range(BATTLE_FORMATS[battle.battle_type]['minimum_sets']):
        tnoodle_result = subprocess.run(f'{settings.TNOODLE_CLI} scramble --puzzle three --count {BATTLE_FORMATS[battle.battle_type]['minimum_set_scrambles']}', shell=True, capture_output=True, text=True)
        scramble_set = tnoodle_result.stdout.replace('\n', ';')
        set_obj = Set(
            set_type=BATTLE_FORMATS[battle.battle_type]['set_type'],
            scramble_set=scramble_set,
        )

        yield set_obj