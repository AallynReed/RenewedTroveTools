from math import ceil


def points_to_mr(points):
    i = 1
    while True:
        if i == 1001:
            break
        i += 1
        if i <= 5:
            increment = 25
        elif 6 <= i <= 10:
            increment = 50
        elif 11 <= i <= 20:
            increment = 75
        elif 21 <= i <= 300:
            increment = 100
        elif i > 300:
            increment = 150 + ceil((i - 300) * 0.5)
        points -= increment
        if points <= 0:
            if points < 0:
                points += increment
                i -= 1
            break
    return i, points, increment


def mr_to_points(level):
    points = 0
    i = 1
    while True:
        i += 1
        if i <= 5:
            increment = 25
        elif 6 <= i <= 10:
            increment = 50
        elif 11 <= i <= 20:
            increment = 75
        elif 21 <= i <= 300:
            increment = 100
        elif i > 300:
            increment = 150 + ceil((i - 300) * 0.5)
        if i == level + 1:
            if i - 1 > 300:
                increment = 150 + ceil((i - 1 - 300) * 0.5)
            break
        points += increment
    return increment, points
