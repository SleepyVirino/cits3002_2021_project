from tkinter import StringVar, Canvas, Listbox
from tkinter.ttk import Frame, Button
import threading

import protocol
from tile import Point, ALL_TILES
from board import Board, PLAYER_COLOURS
from yamlLoader import YamlLoader
from home import Home

settings = YamlLoader.load()


class Game(Frame):
    # Game settings
    TILE_PX = settings['pixel']['tile']
    BORDER_PX = settings['pixel']['border']
    HAND_SPACING_PX = settings['pixel']['hand_space']

    def __init__(self, parent, sock, home: Home, idnum):
        super().__init__(parent)
        self.parent = parent
        self.home = home
        self.pack()

        # Game menu settings
        self.board_width = home.border_width
        self.board_height = home.border_height
        self.hand_size = home.hand_size
        self.board_width_px = Game.TILE_PX * self.board_width
        self.board_height_px = Game.TILE_PX * self.board_height
        self.hand_width_px = Game.TILE_PX * self.hand_size + Game.HAND_SPACING_PX * (self.hand_size - 1)
        self.canvas_width_px = max(self.board_width_px, self.hand_width_px) + 2 * Game.BORDER_PX
        self.canvas_height_px = self.board_height_px + Game.TILE_PX + 3 * Game.BORDER_PX
        self.sock = sock

        self.infolock = threading.Lock()

        # player id
        self.idnum = idnum
        # player id -> name
        self.playernames = dict(home.player_names)

        # hand settings
        self.handlock = threading.Lock()
        self.hand_offset = Point(
            (self.canvas_width_px - self.hand_width_px) / 2,
            2 * Game.BORDER_PX + self.board_height_px)
        self.hand = [None] * self.hand_size
        self.handrotations = [0] * self.hand_size

        # board settings
        self.boardlock = threading.Lock()
        self.board = Board(self.board_width, self.board_height)
        self.board.tile_size_px = Game.TILE_PX
        self.lasttilelocation = None
        self.location = None
        self.playernums = dict(home.player_nums)  # idnum -> player number (turn order)
        self.playerlist = list(home.player_list)
        self.playerlistvar = StringVar(value=[self.playernames[i] for i in self.playerlist])  # // maybe need change
        self.eliminatedlist = []
        self.currentplayerid = None
        self.boardoffset = Point(Game.BORDER_PX, Game.BORDER_PX)

        self.selected_hand = 0
        self.handrects = [None] * self.hand_size

        self.bind('<<ClearBoard>>', lambda ev: self.clear_board())
        self.bind('<<RedrawBoard>>', lambda ev: self.draw_board())
        self.bind('<<RedrawHand>>', lambda ev: self.draw_hand())
        self.bind('<<RedrawTokens>>', lambda ev: self.draw_tokens())
        self.bind('<<RedrawTurn>>', lambda ev: self.draw_turn())
        self.bind('<<CloseConnection>>', lambda ev: self.on_quit())

        self.create_widgets()

    def create_widgets(self):
        # create canvas and so on
        frame = Frame(self, width=self.canvas_width_px + 200, height=self.canvas_height_px)
        frame.grid(column=0, row=0)

        self.canvas = Canvas(frame, width=self.canvas_width_px,
                             height=self.canvas_height_px, bg="white")

        self.board.draw_squares(self.canvas, self.boardoffset, self.play_tile)

        message_x = self.canvas_width_px / 2
        message_y = Game.BORDER_PX / 2

        self.your_turn_text = self.canvas.create_text(message_x, message_y, anchor='center', text='Your turn!',
                                                      fill='black', state='hidden')
        self.eliminated_text = self.canvas.create_text(message_x, message_y, anchor='center',
                                                       text='You were eliminated!', fill='black', state='hidden')
        self.you_won_text = self.canvas.create_text(message_x, message_y, anchor='center', text='You won!',
                                                    fill='black', state='hidden')

        hand_offset = self.hand_offset

        for i in range(len(self.hand)):
            cid = self.canvas.create_rectangle(hand_offset.x + (Game.TILE_PX + Game.HAND_SPACING_PX) * i,
                                               hand_offset.y,
                                               hand_offset.x + (
                                                       Game.TILE_PX + Game.HAND_SPACING_PX) * i + Game.TILE_PX,
                                               hand_offset.y + Game.TILE_PX,
                                               fill='#bbb', outline='#000', width=2,
                                               tags=('hand_rect', 'hand_rect_{}'.format(i)))

            self.handrects[i] = cid

            self.canvas.tag_bind(cid, "<Button-1>", lambda ev, i=i: self.rotate_hand_tile(ev, i))

        self.set_selected_hand(0)

        self.board.draw_tiles(self.canvas, self.boardoffset)

        self.canvas.grid(column=0, row=0, columnspan=1, rowspan=2)

        self.quit = Button(frame, text="QUIT", command=self.on_quit)
        self.quit.grid(column=1, row=0, sticky='n')

        self.playerlistbox = Listbox(frame, listvariable=self.playerlistvar)
        self.playerlistbox.grid(column=1, row=1, sticky='s')

    def set_selected_hand(self, index):
        self.canvas.itemconfigure('hand_rect', fill='#bbb', outline='#000', width=2)

        self.selected_hand = index
        self.canvas.itemconfigure('hand_rect_{}'.format(index), fill='#fff', outline='#bbb', width=4)

    def play_tile(self, x, y):
        if self.lasttilelocation != None and self.location == None:
            return
        if self.currentplayerid != self.idnum:
            return

        if self.sock:
            with self.infolock:
                idnum = self.idnum
                if idnum != None:
                    with self.handlock:
                        tileid = self.hand[self.selected_hand]
                        rotation = self.handrotations[self.selected_hand]
                        if tileid != None:
                            self.sock.send(protocol.MessagePlaceTile(idnum, tileid, rotation, x, y).pack())

    def rotate_hand_tile(self, ev, hand_index):
        if hand_index == self.selected_hand:
            with self.handlock:
                self.handrotations[hand_index] = (self.handrotations[hand_index] + 1) % 4
            self.draw_hand()
        else:
            self.set_selected_hand(hand_index)

    def choose_starting_token(self, position):
        with self.boardlock:
            if self.lasttilelocation and not self.location and self.currentplayerid == self.idnum:
                x, y = self.lasttilelocation
                self.sock.send(protocol.MessageMoveToken(self.idnum, x, y, position).pack())

    def clear_board(self):
        self.canvas.configure(bg='white')
        self.canvas.itemconfigure('board_square', fill="#bbb", activefill="#fff")
        self.canvas.delete('board_tile')
        self.canvas.delete('selection_token')
        self.canvas.delete('token')

    def draw_board(self):
        self.board.draw_tiles(self.canvas, self.boardoffset)

    def draw_hand(self):
        hand_offset = self.hand_offset

        self.canvas.delete('handtile')

        with self.handlock:
            for i in range(len(self.hand)):
                if self.hand[i] != None:
                    drawpoint = Point(hand_offset.x + (Game.TILE_PX + 10) * i, hand_offset.y)
                    tile = ALL_TILES[self.hand[i]]
                    tile.draw(self.canvas, Game.TILE_PX, drawpoint, self.handrotations[i], ('handtile'))

    def draw_tokens(self):
        with self.boardlock:
            if self.lasttilelocation and not self.location:
                x, y = self.lasttilelocation
                self.board.draw_selection_tokens(self.canvas, self.boardoffset, self.playernums, x, y,
                                                 self.choose_starting_token)
            else:
                self.canvas.delete('selection_token')

            self.board.draw_tokens(self.canvas, self.boardoffset, self.playernums, self.eliminatedlist)

    def draw_turn(self):
        self.canvas.itemconfigure(self.you_won_text, state='hidden')
        self.canvas.itemconfigure(self.eliminated_text, state='hidden')
        self.canvas.itemconfigure(self.your_turn_text, state='hidden')

        if self.idnum in self.playernums:
            if self.idnum in self.eliminatedlist:
                self.canvas.itemconfigure(self.eliminated_text, state='normal')
            elif self.eliminatedlist and len(self.playerlist) == 1:
                self.canvas.itemconfigure(self.you_won_text, state='normal')
            elif self.currentplayerid == self.idnum:
                self.canvas.itemconfigure(self.your_turn_text, state='normal')

            playernum = self.playernums[self.idnum]
            playercolour = PLAYER_COLOURS[playernum]
            self.canvas.configure(bg=playercolour)

    def reset_game_state(self):

        with self.handlock:
            for i in range(len(self.hand)):
                self.hand[i] = None
                self.handrotations[i] = 0

        self.event_generate("<<RedrawHand>>")

        with self.boardlock:
            self.board.reset()
            self.lasttilelocation = None
            self.location = None
            self.playernums = {}
            self.playerlist.clear()
            self.eliminatedlist.clear()
            self.currentplayerid = None

        self.event_generate("<<ClearBoard>>")
        self.event_generate("<<RedrawBoard>>")
        self.event_generate("<<RedrawTurn>>")

    def set_player_turn(self, idnum):
        with self.boardlock:
            if not idnum in self.playernums:
                playernum = len(self.playernums)
                self.playernums[idnum] = playernum

                with self.infolock:
                    playername = self.playernames[idnum]
                    self.playerlist.append(idnum)

                self.playerlistvar.set([self.playernames[i] for i in self.playerlist])

            self.currentplayerid = idnum

        self.event_generate("<<RedrawTurn>>")

    def tile_placed(self, msg):

        with self.boardlock:
            idx = self.board.tile_index(msg.x, msg.y)
            self.board.tileids[idx] = msg.tileid
            self.board.tilerotations[idx] = msg.rotation
            self.board.tileplaceids[idx] = msg.idnum

        self.event_generate("<<RedrawBoard>>")

        with self.infolock:
            if self.idnum == msg.idnum:
                with self.handlock:
                    selected = self.selected_hand

                    if self.hand[selected] != msg.tileid:
                        try:
                            selected = self.hand.index(msg.tileid)
                        except ValueError:
                            return

                    self.hand[selected] = None
                    self.handrotations[selected] = 0

                self.event_generate("<<RedrawHand>>")

                redrawtokens = False

                with self.boardlock:
                    self.lasttilelocation = (msg.x, msg.y)
                    if self.location == None:
                        redrawtokens = True

                if redrawtokens:
                    self.event_generate("<<RedrawTokens>>")

    def set_player_eliminated(self, idnum):

        with self.boardlock:
            with self.infolock:
                if idnum in self.playerlist:
                    self.playerlist.remove(idnum)
                else:
                    pass
            self.playerlistvar.set(self.playernames[i] for i in self.playerlist)

            if not idnum in self.eliminatedlist:
                self.eliminatedlist.append(idnum)

        self.event_generate("<<RedrawTokens>>")
        self.event_generate("<<RedrawTurn>>")

    def token_moved(self, msg):
        with self.boardlock:
            if msg.idnum == self.idnum:
                self.location = (msg.x, msg.y, msg.position)
            self.board.update_player_position(msg.idnum, msg.x, msg.y, msg.position)

        self.event_generate("<<RedrawTokens>>")

    def add_tile_to_hand(self, tileid):
        with self.handlock:
            for i in range(len(self.hand)):
                if self.hand[i] == None:
                    self.hand[i] = tileid
                    self.handrotations[i] = 0
                    break
        self.event_generate("<<RedrawHand>>")

    def on_quit(self):
        self.sock.send(protocol.MessageLeaveGame(self.idnum).pack())
        if self.parent:
            self.parent.destroy()
