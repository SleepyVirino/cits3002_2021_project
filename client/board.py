from yamlLoader import YamlLoader
from tile import Point, CONNECTION_LOCATIONS, ALL_TILES

settings = YamlLoader.load()

PLAYER_COLOURS = settings['player_color']


class Board:
    """Stores the state of the board for a single game, and implements much of the
    game logic as far as token movement, valid tile placement, etc.
    """

    def __init__(self, board_width, board_height):
        self.board_width = board_width
        self.board_height = board_height
        self.width = self.board_width
        self.height = self.board_height

        # tileids: the id of the tile at each location on the board.
        self.tileids = [None] * (self.board_width * self.board_height)
        # tilerotations: the rotation of the tile at each location on the board.
        # 0 = no rotation, 1 = 90 degrees clockwise, 2 = 180 degrees, 3 = 270 degrees.
        self.tilerotations = [None] * (self.board_width * self.board_height)
        # tileplaceids: the id of the player that placed the tile at each location on the board.
        self.tileplaceids = [None] * (self.board_width * self.board_height)
        # tilerects: the rectangle that the tile at each location on the board is drawn in.
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

    def tile_index(self, x: int, y: int):
        """Return the index of the tile at the given location."""
        return x + y * self.width

    def update_player_position(self, idnum, x: int, y: int, position: int):
        self.playerpositions[idnum] = (x, y, position)

    def draw_squares(self, canvas, offset, onclick):
        # Draw the squares that the tiles will be drawn in.
        for x in range(self.width):
            xpix = offset.x + x * self.tile_size_px
            for y in range(self.height):
                ypix = offset.y + y * self.tile_size_px
                tidx = self.tile_index(x, y)
                if not self.tilerects[tidx]:
                    tid = canvas.create_rectangle(xpix, ypix,
                                                  xpix + self.tile_size_px, ypix + self.tile_size_px, fill="#bbb",
                                                  activefill="#fff",
                                                  tags=('board_square', 'board_square_{}_{}'.format(x, y)))

                    self.tilerects[tidx] = tid

                    canvas.tag_bind(tid, "<Button-1>", lambda ev, x=x, y=y: onclick(x, y))

    def draw_tiles(self, canvas, offset):
        canvas.delete('board_tile')

        for x in range(self.width):
            xpix = offset.x + x * self.tile_size_px
            for y in range(self.height):
                ypix = offset.y + y * self.tile_size_px

                idx = self.tile_index(x, y)
                tileid = self.tileids[idx]

                if tileid != None:
                    tile = ALL_TILES[tileid]
                    rotation = self.tilerotations[idx]

                    tile.draw(canvas, self.tile_size_px, Point(xpix, ypix), rotation,
                              tags=('board_tile', 'board_tile_{}_{}'.format(x, y)))

                    trect = self.tilerects[idx]
                    if trect:
                        canvas.itemconfigure(trect, fill="#bbb", activefill="#bbb")

        canvas.lift('selection_token')

    def draw_tokens(self, canvas, offset, playernums, eliminated):
        canvas.delete('token')

        for idnum, playerposition in self.playerpositions.items():
            x, y, position = playerposition

            xpix = offset.x + x * self.tile_size_px
            ypix = offset.y + y * self.tile_size_px

            playernum = playernums[idnum]
            playercol = PLAYER_COLOURS[playernum]

            if idnum in eliminated:
                playercol = settings['eliminated_color']

            delta = CONNECTION_LOCATIONS[position]

            cx = xpix + int(delta.x * self.tile_size_px)
            cy = ypix + int(delta.y * self.tile_size_px)

            canvas.create_oval(cx - settings["token"]["size"], cy - settings["token"]["size"],
                               cx + settings["token"]["size"], cy + settings["token"]["size"],
                               fill=playercol, outline='black', tags=('token',))

    def draw_selection_token(self, canvas, playernum, xpix: int, ypix: int, connector: int, callback):
        delta = CONNECTION_LOCATIONS[connector]

        cx = xpix + int(delta.x * self.tile_size_px)
        cy = ypix + int(delta.y * self.tile_size_px)

        playercol = PLAYER_COLOURS[playernum]

        tokenid = canvas.create_oval(cx - settings["token"]["size"], cy - settings["token"]["size"],
                                     cx + settings["token"]["size"], cy + settings["token"]["size"],
                                     fill=playercol, activefill="#fff", outline='black',
                                     tags=('selection_token'))

        canvas.tag_bind(tokenid, "<Button-1>", lambda ev: callback(connector))

    def draw_selection_tokens(self, canvas, offset, playernums, x: int, y: int, callback):
        idx = self.tile_index(x, y)
        tileid = self.tileids[idx]
        if tileid == None:
            return

        playerid = self.tileplaceids[idx]
        playernum = playernums[playerid]

        xpix = offset.x + x * self.tile_size_px
        ypix = offset.y + y * self.tile_size_px

        if y == self.height - 1:
            self.draw_selection_token(canvas, playernum, xpix, ypix, 0, callback)
            self.draw_selection_token(canvas, playernum, xpix, ypix, 1, callback)
        if x == self.width - 1:
            self.draw_selection_token(canvas, playernum, xpix, ypix, 2, callback)
            self.draw_selection_token(canvas, playernum, xpix, ypix, 3, callback)
        if y == 0:
            self.draw_selection_token(canvas, playernum, xpix, ypix, 4, callback)
            self.draw_selection_token(canvas, playernum, xpix, ypix, 5, callback)
        if x == 0:
            self.draw_selection_token(canvas, playernum, xpix, ypix, 6, callback)
            self.draw_selection_token(canvas, playernum, xpix, ypix, 7, callback)
