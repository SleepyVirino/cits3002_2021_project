from random import randrange


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Tile:
    def __init__(self, connections):
        if len(connections) != 4:
            raise RuntimeError("Tile must have exactly 8 connections")

        self.nextpoint = [None] * 8

        for i in range(4):
            a, b = connections[i]
            if a == b:
                raise RuntimeError("Connection must not loop back to itself")
            if a < 0 or a >= 8 or b < 0 or b >= 8:
                raise RuntimeError("Invalid connection ports {}, {}".format(a, b))
            if self.nextpoint[a] != None:
                raise RuntimeError("Connection port {} set multiple times".format(a))
            if self.nextpoint[b] != None:
                raise RuntimeError("Connection port {} set multiple times".format(b))
            self.nextpoint[a] = b
            self.nextpoint[b] = a

        self.connections = connections

    def getmovement(self, rotation, fromposition):
        unrotated = ((fromposition - 2 * rotation) + 8) % 8
        nextposition = self.nextpoint[unrotated]
        nextposition = (nextposition + 2 * rotation) % 8
        return nextposition

    def draw(self, canvas, size_px, basepoint, rotation, tags):
        for i in range(4):
            a, b = self.connections[i]

            apos = CONNECTION_LOCATIONS[(a + 2 * rotation) % 8]
            bpos = CONNECTION_LOCATIONS[(b + 2 * rotation) % 8]

            ax = basepoint.x + int(apos.x * size_px)
            ay = basepoint.y + int(apos.y * size_px)

            bx = basepoint.x + int(bpos.x * size_px)
            by = basepoint.y + int(bpos.y * size_px)

            canvas.create_line(ax, ay, bx, by, width=3,
                               fill="#000000", activefill="#66ccee", tags=tags)

CONNECTION_LOCATIONS = [
    Point(0.25, 1.0),
    Point(0.75, 1.0),
    Point(1.0, 0.75),
    Point(1.0, 0.25),
    Point(0.75, 0.0),
    Point(0.25, 0.0),
    Point(0.0, 0.25),
    Point(0.0, 0.75)
]
ALL_TILES = [Tile(x) for x in [
    [(0, 5), (1, 2), (3, 6), (4, 7)],
    [(0, 5), (1, 4), (2, 6), (3, 7)],
    [(0, 7), (1, 2), (3, 4), (5, 6)],
    [(0, 5), (1, 4), (2, 7), (3, 6)],

    [(0, 7), (1, 6), (2, 5), (3, 4)],
    [(0, 2), (1, 3), (4, 6), (5, 7)],
    [(0, 4), (1, 5), (2, 6), (3, 7)],
    [(0, 7), (1, 2), (3, 5), (4, 6)],

    [(0, 5), (1, 7), (2, 4), (3, 6)],
    [(0, 4), (1, 2), (3, 6), (5, 7)],
    [(0, 2), (1, 5), (3, 6), (4, 7)]
]]

CONNECTION_NEIGHBOURS = [
    # dx, dy, position
    (0, 1, 5),
    (0, 1, 4),
    (1, 0, 7),
    (1, 0, 6),
    (0, -1, 1),
    (0, -1, 0),
    (-1, 0, 3),
    (-1, 0, 2)
]

def get_random_tileid():
    """Get a random, valid tileid."""
    return randrange(0, len(ALL_TILES))






