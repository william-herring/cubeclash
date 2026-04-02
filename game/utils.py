import subprocess
from django.conf import settings
from game.constants import BATTLE_FORMATS
from game.models import Battle, Set

def init_set(battle: Battle) -> Set:
    scramble = subprocess.run(f'{settings.TNOODLE_CLI} scramble --puzzle three', shell=True, capture_output=True,text=True).stdout
    set_obj = Set(
        set_type=BATTLE_FORMATS[battle.battle_type]['set_type'],
        scramble_set=scramble,
    )

    return set_obj

def get_scramble() -> str:
    scramble = subprocess.run(f'{settings.TNOODLE_CLI} scramble --puzzle three', shell=True, capture_output=True, text=True).stdout
    return scramble
