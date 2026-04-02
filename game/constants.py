BATTLE_FORMATS = {
    'bo5': {
        'minimum_sets': 1,
        'minimum_set_scrambles': 3,
        'set_type': 'bo5'
    },
    'bo12': {
        'minimum_sets': 1,
        'minimum_set_scrambles': 7,
        'set_type': 'bo12'
    },
    'bo25': {
        'minimum_sets': 1,
        'minimum_set_scrambles': 13,
        'set_type': 'bo25'
    },
    'bo100': {
        'minimum_sets': 1,
        'minimum_set_scrambles': 51,
        'set_type': 'bo100'
    },
    'bo3ft5': {
        'minimum_sets': 2,
        'minimum_set_scrambles': 5,
        'set_type': 'ft5'
    },
    'bo5ft5': {
        'minimum_sets': 3,
        'minimum_set_scrambles': 5,
        'set_type': 'ft5'
    },
}

SET_WIN_CONDITIONS = {
    'bo5': lambda s1, s2: s1 + s2 == 5,
    'bo12': lambda s1, s2: s1 + s2 == 12,
    'bo25': lambda s1, s2: s1 + s2 == 25,
    'bo100': lambda s1, s2: s1 + s2 == 100,
    'ft5': lambda s1, s2: (s1 == 5 or s2 == 5) and abs(s1 - s2) >= 2,
}

BATTLE_WIN_CONDITIONS = {
    'bo5': lambda s1, s2: s1 + s2 == 1,
    'bo12': lambda s1, s2: s1 + s2 == 1,
    'bo25': lambda s1, s2: s1 + s2 == 1,
    'bo100': lambda s1, s2: s1 + s2 == 1,
    'bo3ft5': lambda s1, s2: s1 + s2 == 3,
    'bo5ft5': lambda s1, s2: s1 + s2 == 5,
}