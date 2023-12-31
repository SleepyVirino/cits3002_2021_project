
from random import randrange

from tile import ALL_TILES, CONNECTION_NEIGHBOURS
from protocol import MessageMoveToken

class Board:
    """Stores the state of the board for a single game, and implements much of the
    game logic as far as token movement, valid tile placement, etc.
    """

    def __init__(self, board_width, board_height):
        self.board_width = board_width
        self.board_height = board_height
        self.width = self.board_width
        self.height = self.board_height
        self.tileids = [None] * (self.board_width * self.board_height)
        self.tilerotations = [None] * (self.board_width * self.board_height)
        self.tileplaceids = [None] * (self.board_width * self.board_height)
        self.tilerects = [None] * (self.board_width * self.board_height)
        self.playerpositions = {}
        self.tile_size_px = 100

    def reset(self):
        """Reset the board to be empty, with no tiles or player tokens."""
        for i in range(len(self.tileids)):
            self.tileids[i] = None
            self.tilerotations[i] = None
            self.tileplaceids[i] = None

        self.playerpositions = {}

    def get_tile(self, x: int, y: int):
        """Get (tile id, rotation, placer id) for location x, y."""
        if x < 0 or x >= self.width:
            raise Exception('invalid x value')
        if y < 0 or y >= self.height:
            raise Exception('invalid y value')

        idx = self.tile_index(x, y)

        return self.tileids[idx], self.tilerotations[idx], self.tileplaceids[idx]

    def set_tile(self, x: int, y: int, tileid: int, rotation: int, idnum: int):
        """Attempt to place the given tile at position x,y.
        rotation: the rotation of the tile.
        idnum: id of the player that is placing the tile.

        If the tile cannot be placed, returns False, otherwise returns True.

        Note that this does not update the token positions.
        """

        if idnum in self.playerpositions:
            playerx, playery, _ = self.playerpositions[idnum]
            if x != playerx or y != playery:
                return False
        elif x != 0 and x != self.width - 1 and y != 0 and y != self.height - 1:
            return False

        idx = self.tile_index(x, y)

        if self.tileids[idx] != None:
            return False

        self.tileids[idx] = tileid
        self.tilerotations[idx] = rotation
        self.tileplaceids[idx] = idnum
        return True

    def have_player_position(self, idnum):
        """Check if the given player (by idnum) has a token on the board."""
        return idnum in self.playerpositions

    def get_player_position(self, idnum):
        """The given player (idnum) must have a token on the board before calling
        this method.

        Returns the player token's location as: x, y, position."""
        return self.playerpositions[idnum]

    def set_player_start_position(self, idnum, x: int, y: int, position: int):
        """Attempt to set the starting position for a player token.

        idnum: the player
        x, y: the square of the board
        position: position on the chosen square (0..7)

        If the player's token is already on the board, or the player did not place
        the tile at the given x,y location, or the chosen position does not touch
        the edge of the game board, then this method will return False and not
        change the state of the game board.

        Otherwise the player's token will be set to the given location, and the
        method will return True.
        """
        if self.have_player_position(idnum):
            return False

        # does the tile exist?
        idx = self.tile_index(x, y)
        if self.tileids[idx] == None:
            return False

        # does the player own the tile?
        if self.tileplaceids[idx] != idnum:
            return False

        # is position in tile valid?
        if (position == 0 or position == 1) and y != self.board_height - 1:
            return False
        if (position == 2 or position == 3) and x != self.board_width - 1:
            return False
        if (position == 4 or position == 5) and y != 0:
            return False
        if (position == 6 or position == 7) and x != 0:
            return False

        self.update_player_position(idnum, x, y, position)

        return True

    def do_player_movement(self, live_idnums):
        """For all of the player ids in the live_idnums list, this method will move
        their player tokens if it is possible for them to move.

        That means that if the token is on a square that has a tile placed on it,
        the token will move across the connector to another edge of the tile, and
        then into the neighbouring square. If the neighbouring square also has a
        tile, the movement will continue in the same fashion. This process stops
        when the player's token reaches an empty square, or the edge of the game
        board.

        A tuple of two lists is returned: positionupdates, eliminated.

        positionupdates contains MessageMoveToken messages describing all of the
        updated token positions.

        eliminated contains a list of player ids that have been eliminated from the
        game by this movement phase (i.e. their token has just been moved to the
        edge of the game board).
        """
        positionupdates = []
        eliminated = []

        for idnum, playerposition in self.playerpositions.items():
            # don't keep moving expired players around
            if not idnum in live_idnums:
                continue

            x, y, position = playerposition
            idx = self.tile_index(x, y)
            moved = False

            while self.tileids[idx] != None:
                moved = True
                tileid = self.tileids[idx]
                rotation = self.tilerotations[idx]
                tile = ALL_TILES[tileid]
                exitposition = tile.getmovement(rotation, position)

                # determine next square to move into from this exit position
                dx, dy, dposition = CONNECTION_NEIGHBOURS[exitposition]
                nx = x + dx
                ny = y + dy

                # if that square would be off the board, we're eliminated
                if nx < 0 or nx >= self.board_width or ny < 0 or ny >= self.board_height:
                    position = exitposition
                    eliminated.append(idnum)
                    break

                # otherwise move into that square and continue the loop (if a tile is in the square)
                x, y, position = nx, ny, dposition
                idx = self.tile_index(x, y)

            if moved:
                self.update_player_position(idnum, x, y, position)
                positionupdates.append(MessageMoveToken(idnum, x, y, position))

        return positionupdates, eliminated

    def tile_index(self, x: int, y: int):
        return x + y * self.width

    def update_player_position(self, idnum, x: int, y: int, position: int):
        self.playerpositions[idnum] = (x, y, position)


def get_random_tileid():
    """Get a random, valid tileid."""
    return randrange(0, len(ALL_TILES))
