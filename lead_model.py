"""Horizontal motion predictor fitted to visible mech tracks in local practice matches."""

import math

# Each row covers flight times of 0.1 to 0.9 seconds. Coefficients weight
# current velocity and the change over the preceding observation.
WEIGHTS = (
    (
        (0.991, -0.005),
        (0.983, 0.004),
        (0.974, 0.025),
        (0.965, 0.045),
        (0.955, 0.054),
        (0.945, 0.061),
        (0.936, 0.063),
        (0.927, 0.06),
        (0.918, 0.054),
    ),
    (
        (0.924, 0.216),
        (0.87, 0.311),
        (0.823, 0.357),
        (0.785, 0.368),
        (0.755, 0.362),
        (0.73, 0.35),
        (0.709, 0.333),
        (0.69, 0.312),
        (0.675, 0.293),
    ),
    (
        (1.002, 0.007),
        (1.016, 0.04),
        (1.037, 0.106),
        (1.058, 0.197),
        (1.082, 0.306),
        (1.104, 0.416),
        (1.126, 0.518),
        (1.143, 0.612),
        (1.153, 0.689),
    ),
    (
        (0.988, 0.172),
        (0.877, 0.388),
        (0.721, 0.492),
        (0.59, 0.531),
        (0.506, 0.531),
        (0.467, 0.51),
        (0.439, 0.475),
        (0.428, 0.439),
        (0.424, 0.396),
    ),
)


def offset(velocity, old_velocity, seconds):
    vx, vy = velocity[:2]
    if old_velocity is None:
        return seconds * vx, seconds * vy
    dx, dy = vx - old_velocity[0], vy - old_velocity[1]
    row = 2 * (math.hypot(vx, vy) < 3) + (math.hypot(dx, dy) > 2.2)
    column = min(8, max(0, round(seconds * 10) - 1))
    speed, turn = WEIGHTS[row][column]
    return seconds * (speed * vx + turn * dx), seconds * (speed * vy + turn * dy)
