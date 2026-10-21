import math

START = (0.0, -12.0, 90.0)   # x, y, heading (deg, 0 = East, CCW+)
EXIT = (8.0, 12.0)

WALLS = [
    ((-1.5, -13.5), (1.5, -13.5)),   # start cap
    ((-1.5, -13.5), (-1.5, 1.5)),    # corridor 1, left
    ((1.5, -13.5), (1.5, -1.5)),     # corridor 1, right
    ((-1.5, 1.5), (6.5, 1.5)),       # corridor 2, top
    ((1.5, -1.5), (9.5, -1.5)),      # corridor 2, bottom
    ((9.5, -1.5), (9.5, 13.5)),      # corridor 3, right
    ((6.5, 1.5), (6.5, 13.5)),       # corridor 3, left
]


def dist_point_segment(px, py, seg):
    (x1, y1), (x2, y2) = seg
    dx, dy = x2 - x1, y2 - y1
    t = ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)
    t = max(0.0, min(1.0, t))
    return math.hypot(px - (x1 + t * dx), py - (y1 + t * dy))
