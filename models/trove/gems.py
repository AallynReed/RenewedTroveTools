def radiant_level_increments(level: int):
    match level:
        case 1 | 5 | 10 | 15:
            return 0
        case 2 | 3 | 4 | 6 | 7 | 8 | 9 | 11 | 12 | 13 | 14:
            return 3
        case 16 | 17 | 18 | 19 | 21 | 22 | 23:
            return 6
        case 20:
            return 15
        case _:
            return 0


def stellar_level_increments(level: int):
    match level:
        case 1 | 5 | 10 | 15:
            return 0
        case 2 | 3 | 4 | 6 | 7 | 8 | 9 | 11 | 12 | 13 | 14:
            return 5
        case 16 | 17 | 18 | 19 | 21 | 22 | 23 | 24:
            return 10
        case 20 | 25:
            return 25
        case _:
            return 0


def crystal_level_increments(level: int):
    pr = 7
    match level:
        case 1 | 5 | 10 | 15:
            return 0
        case 2 | 3 | 4 | 6 | 7 | 8 | 9 | 11 | 12 | 13 | 14:
            return pr * 1
        case 16 | 17 | 18 | 19 | 21 | 22 | 23 | 24 | 26 | 27 | 28 | 29:
            return pr * 2
        case 20 | 25 | 30:
            return pr * 5
        case _:
            return 0


def mystic_level_increments(level: int):
    pr = 9
    match level:
        case 1 | 5 | 10 | 15:
            return 0
        case 2 | 3 | 4 | 6 | 7 | 8 | 9 | 11 | 12 | 13 | 14:
            return pr * 1
        case 16 | 17 | 18 | 19 | 21 | 22 | 23 | 24 | 26 | 27 | 28 | 29 | 31 | 32 | 33 | 34:
            return pr * 2
        case 20 | 25 | 30 | 35:
            return pr * 5
        case _:
            return 0

level_increments = {
    "radiant": radiant_level_increments,
    "stellar": stellar_level_increments,
    "crystal": crystal_level_increments,
    "mystic": mystic_level_increments,
}


max_levels = {"radiant": 23, "stellar": 25, "crystal": 30, "mystic": 35}


gem_min_max = {
    "radiant": {
        "Physical Damage": {"lesser": [85, 113], "empowered": [113, 150]},
        "Magic Damage": {"lesser": [85, 113], "empowered": [113, 150]},
        "Critical Damage": {"lesser": [85, 113], "empowered": [113, 150]},
        "Critical Hit": {"lesser": [85, 113], "empowered": [113, 150]},
        "Maximum Health %": {"lesser": [85, 113], "empowered": [113, 150]},
        "Maximum Health": {"lesser": [85, 113], "empowered": [113, 150]},
        "Light": {"lesser": [85, 113], "empowered": [113, 150]},
    },
    "stellar": {
        "Physical Damage": {"lesser": [150, 200], "empowered": [200, 266]},
        "Magic Damage": {"lesser": [150, 200], "empowered": [200, 266]},
        "Critical Damage": {"lesser": [150, 200], "empowered": [200, 266]},
        "Critical Hit": {"lesser": [150, 200], "empowered": [200, 266]},
        "Maximum Health %": {"lesser": [150, 200], "empowered": [200, 266]},
        "Maximum Health": {"lesser": [150, 200], "empowered": [200, 266]},
        "Light": {"lesser": [150, 200], "empowered": [200, 266]},
    },
    "crystal": {
        "Physical Damage": {"lesser": [210, 280], "empowered": [245, 350]},
        "Magic Damage": {"lesser": [210, 280], "empowered": [245, 350]},
        "Critical Damage": {
            "lesser": [560 / 3, 770 / 3],
            "empowered": [700 / 3, 910 / 3],
        },
        "Critical Hit": {"lesser": [560 / 3, 770 / 3], "empowered": [700 / 3, 910 / 3]},
        "Maximum Health %": {"lesser": [245, 315], "empowered": [315, 385]},
        "Maximum Health": {"lesser": [245, 315], "empowered": [315, 385]},
        "Light": {"lesser": [280, 385], "empowered": [350, 420]},
    },
    "mystic": {
        "Physical Damage": {"lesser": [270, 360], "empowered": [210, 300]},
        "Magic Damage": {"lesser": [270, 360], "empowered": [210, 300]},
        "Critical Damage": {
            "lesser": [187.2, 297],
            "empowered": [252, 342],
        },
        "Critical Hit": {"lesser": [187.2, 297], "empowered": [252, 342]},
        "Maximum Health %": {"lesser": [315, 405], "empowered": [405, 495]},
        "Maximum Health": {"lesser": [315, 405], "empowered": [405, 495]},
        "Light": {"lesser": [495, 585], "empowered": [495, 630]},
    },
}


lesser_stat_multipliers = {
    "radiant": {
        "Physical Damage": [14, 14],
        "Magic Damage": [14, 14],
        "Critical Damage": [0.2, 0.2],
        "Critical Hit": [0.02, 0.02],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [1, 1],
    },
    "stellar": {
        "Physical Damage": [14, 14],
        "Magic Damage": [14, 14],
        "Critical Damage": [0.2, 0.2],
        "Critical Hit": [0.02, 0.02],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [1, 1],
    },
    "crystal": {
        "Physical Damage": [16, 16],
        "Magic Damage": [16, 16],
        "Critical Damage": [3 / 14, 3 / 14],
        "Critical Hit": [0.3 / 14, 0.3 / 14],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [5 / 7, 5 / 7],
    },
    "mystic": {
        "Physical Damage": [19, 19],
        "Magic Damage": [19, 19],
        "Critical Damage": [2.5 / 9, 2.5 / 9],
        "Critical Hit": [0.25 / 9, 0.25 / 9],
        "Maximum Health %": [5.25 / 9, 5.25 / 9],
        "Maximum Health": [525 / 9, 525 / 9],
        "Light": [5 / 9, 5 / 9],
    }
}

empowered_stat_multipliers = {
    "radiant": {
        "Physical Damage": [14, 14],
        "Magic Damage": [14, 14],
        "Critical Damage": [0.2, 0.2],
        "Critical Hit": [0.02, 0.02],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [1, 1],
    },
    "stellar": {
        "Physical Damage": [14, 14],
        "Magic Damage": [14, 14],
        "Critical Damage": [0.2, 0.2],
        "Critical Hit": [0.02, 0.02],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [1, 1],
    },
    "crystal": {
        "Physical Damage": [16, 16],
        "Magic Damage": [16, 16],
        "Critical Damage": [3 / 14, 3 / 14],
        "Critical Hit": [0.3 / 14, 0.3 / 14],
        "Maximum Health %": [0.5, 0.5],
        "Maximum Health": [50, 50],
        "Light": [5 / 7, 5 / 7],
    },
    "mystic": {
        "Physical Damage": [28, 28],
        "Magic Damage": [28, 28],
        "Critical Damage": [2.5 / 9, 2.5 / 9],
        "Critical Hit": [0.25 / 9, 0.25 / 9],
        "Maximum Health %": [5.25 / 9, 5.25 / 9],
        "Maximum Health": [525 / 9, 525 / 9],
        "Light": [5 / 9, 5 / 9],
    }
}


gem_container_pr = {
    "lesser": {
        "radiant": [85, 113],
        "stellar": [150, 200],
        "crystal": [175, 250],
        "mystic": [200, 260],
    },
    "empowered": {
        "radiant": [113, 150],
        "stellar": [200, 266],
        "crystal": [220, 280],
        "mystic": [240, 300],
    },
}


augment_costs = {
    "rough": {
        "weight": 1,
        "costs": {"bound_brilliance": 1, "heart_of_darkness": 4, "flux": 1200},
    },
    "precise": {
        "weight": 2,
        "costs": {
            "bound_brilliance": 1,
            "fire_gem_dust": 3000,
            "water_gem_dust": 3000,
            "air_gem_dust": 3000,
            "flux": 2000,
        },
    },
    "superior": {
        "weight": 5,
        "costs": {
            "bound_brilliance": 1,
            "diamond_dragonite": 30,
            "titan_soul": 3,
            "flux": 50000,
        },
    },
}
