import subprocess
from django.conf import settings
from game.constants import BATTLE_FORMATS
from game.models import Battle, Set
from typing import Generator

def init_sets(battle: Battle) -> Generator[Set, None, None]:
    for i in range(BATTLE_FORMATS[battle.battle_type]['minimum_sets']):
        scramble = subprocess.run(f'{settings.TNOODLE_CLI} scramble --puzzle three', shell=True, capture_output=True,text=True).stdout
        set_obj = Set(
            set_type=BATTLE_FORMATS[battle.battle_type]['set_type'],
            scramble_set=scramble,
        )

        yield set_obj

def get_scramble() -> str:
    scramble = subprocess.run(f'{settings.TNOODLE_CLI} scramble --puzzle three', shell=True, capture_output=True, text=True).stdout
    return scramble
