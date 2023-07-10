from tkinter import Tk, Scale, Label, Button, Toplevel, Entry
from tkinter import messagebox
from tkinter.ttk import Frame, Button
from socket import *
import threading

from protocol import *
from game import Game
from yamlLoader import YamlLoader

settings = YamlLoader().load()


class Controller():
    # The number of rows and columns of the all menus
    MENU_ROWS = 9
    MENU_COLUMNS = 3
    HOME_SETTING_MENU_ROWS = 6
    HOME_SETTING_MENU_COLUMNS = 4
    JOIN_HOME_ROWS = 3
    JOIN_HOME_COLUMNS = 3
    HOME_ROWS = 10
    HOME_COLUMNS = 5

    def __init__(self, conn: socket, game=None, home=None):
        self.conn = conn
        self.game = game
        self.home = home
        self.lock = threading.Lock()

        self.idnum = None
        self.player_name = None

        self.root = Tk()
        self.root.protocol("WM_DELETE_WINDOW", self.on_quit)

        # Configure the root window settings
        width = settings['root']['width']
        height = settings['root']['height']
        resize = settings['root']['resize']
        self.root.geometry(f"{width}x{height}")
        self.root.resizable(width=resize, height=resize)
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # The four menus
        self.menu = None
        self.join_home_menu = None
        self.home_setting_menu = None
        self.home_menu = None

        self.current_menu = None

        self.init_menu()
        self.init_home_setting_menu()
        self.init_join_home_menu()

    def init_menu(self):
        # Create main menu
        self.menu = Frame(self.root)
        for row in range(Controller.MENU_ROWS):
            self.menu.rowconfigure(row, weight=1)
        for column in range(Controller.MENU_COLUMNS):
            self.menu.columnconfigure(column, weight=1)

        # Three buttons
        Button(self.menu, text="Start Match", command=self.start_match).grid(column=1, row=2, sticky='nsew')
        Button(self.menu, text="Create Home", command=self.create_home).grid(column=1, row=4, sticky='nsew')
        Button(self.menu, text="Join Home", command=self.join_home).grid(column=1, row=6, sticky='nsew')

        # The first menu is main menu
        self.current_menu = self.menu
        self.current_menu.grid(column=0, row=0, sticky='nsew')

    def init_home_setting_menu(self):
        # Create the home setting menu
        self.home_setting_menu = Frame(self.root)
        for row in range(Controller.HOME_SETTING_MENU_ROWS):
            self.home_setting_menu.rowconfigure(row, weight=1)
        for column in range(Controller.HOME_SETTING_MENU_COLUMNS):
            self.home_setting_menu.columnconfigure(column, weight=1)

        # All setting scales
        self.board_width_scale = Scale(self.home_setting_menu, from_=4, to=10, orient="horizontal")
        self.board_width_scale.grid(column=2, row=1)
        self.board_height_scale = Scale(self.home_setting_menu, from_=4, to=10, orient="horizontal")
        self.board_height_scale.grid(column=2, row=2)
        self.hand_size_scale = Scale(self.home_setting_menu, from_=4, to=6, orient="horizontal")
        self.hand_size_scale.grid(column=2, row=3)
        self.max_player_num_scale = Scale(self.home_setting_menu, from_=2, to=8, orient='horizontal')
        self.max_player_num_scale.grid(column=2, row=4)

        # All setting labels
        self.board_width_label = Label(self.home_setting_menu, text="Board Width")
        self.board_width_label.grid(column=1, row=1, sticky='ew')
        self.board_height_label = Label(self.home_setting_menu, text="Board Height")
        self.board_height_label.grid(column=1, row=2, sticky='ew')
        self.hand_size_label = Label(self.home_setting_menu, text="Hand Size")
        self.hand_size_label.grid(column=1, row=3, sticky='ew')
        self.max_player_num_label = Label(self.home_setting_menu, text="Max Player")
        self.max_player_num_label.grid(column=1, row=4, sticky='ew')

        # Two buttons
        Button(self.home_setting_menu, text="Create", command=self.create).grid(column=3, row=5, sticky='nsew')
        Button(self.home_setting_menu, text="Back", command=self.create_back).grid(column=0, row=5, sticky='nsew')

    def init_join_home_menu(self):
        # Create join home menu
        self.join_home_menu = Frame(self.root)
        for row in range(Controller.JOIN_HOME_ROWS):
            self.join_home_menu.rowconfigure(row, weight=1)
        for column in range(Controller.JOIN_HOME_COLUMNS):
            self.join_home_menu.columnconfigure(column, weight=1)

        # One label, one entry and two buttons
        self.home_id_label = Label(self.join_home_menu, text='Home ID')
        self.home_id_label.grid(column=0, row=1, sticky='ew')
        self.home_id_entry = Entry(self.join_home_menu)
        self.home_id_entry.grid(column=1, row=1, columnspan=2, sticky='ew')
        Button(self.join_home_menu, text="Join", command=self.join).grid(column=2, row=2, sticky='nsew')
        Button(self.join_home_menu, text="Back", command=self.join_back).grid(column=0, row=2, sticky='nsew')

    def init_home_menu(self):
        # Create home menu
        self.home_menu = Frame(self.root)
        for row in range(Controller.HOME_ROWS):
            self.home_menu.rowconfigure(row, weight=1)
        for column in range(Controller.HOME_COLUMNS):
            self.home_menu.columnconfigure(column, weight=1)

        # All labels
        self.home_id_label = Label(self.home_menu, text=str(self.home.id))
        self.home_id_label.grid(column=1, row=8, rowspan=2, columnspan=3, sticky='ew')
        self.player_labels = {}
        for i, idnum in enumerate(self.home.player_list):
            id_label = Label(self.home_menu, text=str(idnum))
            id_label.grid(column=0, row=i, sticky='ew')
            name_label = Label(self.home_menu, text=self.home.player_names[idnum])
            name_label.grid(column=1, row=i, columnspan=3, sticky='ew')
            state_label = Label(self.home_menu, text=self.get_role_str(idnum))
            state_label.grid(column=4, row=i, sticky='ew')
            self.player_labels[idnum] = (id_label, name_label, state_label)

        # Two buttons
        Button(self.home_menu, text="Start", command=self.start).grid(column=4, row=8, rowspan=2, sticky='nsew')
        Button(self.home_menu, text="Back", command=self.home_back).grid(column=0, row=8, rowspan=2, sticky='nsew')

    def start(self):
        # The home owner can start the game
        if self.home.owner_id != self.idnum:
            messagebox.showerror("Error", "You are not the owner of this home")
        else:
            self.conn.send(MessageGameStart().pack())

    def clear_home(self):
        # Clear the home menu when leaving the home
        self.home_menu.destroy()
        self.home = None
        self.player_labels = {}

    def get_role_str(self, idnum):
        # Return every player's role in the home
        # I: this player
        # O: the owner of the home
        # X: other players
        result = ""
        if idnum == self.idnum:
            result += " I "
        if idnum == self.home.owner_id:
            result += " O "
        else:
            result += " X "
        return result

    def update_home(self):
        # Update the home menu and only player_labels need update
        for idnum in self.home.player_list:
            self.player_labels[idnum][1]['text'] = str(idnum)
            self.player_labels[idnum][1]['text'] = self.home.player_names[idnum]
            self.player_labels[idnum][2]['text'] = self.get_role_str(idnum)

    def draw_home_menu(self):
        self.current_menu.grid_remove()
        self.current_menu = self.home_menu
        self.update_home()
        self.current_menu.grid(column=0, row=0, sticky='nesw')

    def home_back(self):
        self.current_menu.grid_remove()
        self.current_menu = self.menu
        self.current_menu.grid(column=0, row=0, sticky='nesw')

        if self.game:
            self.clear_game()

        self.conn.send(MessageLeaveHome(self.idnum).pack())
        self.clear_home()

    def start_match(self):
        self.conn.send(MessageMatchHome(self.idnum, self.player_name).pack())

    def create_home(self):
        self.current_menu.grid_remove()
        self.current_menu = self.home_setting_menu
        self.current_menu.grid(column=0, row=0, sticky='nesw')

    def join_home(self):
        self.current_menu.grid_remove()
        self.current_menu = self.join_home_menu
        self.current_menu.grid(column=0, row=0, sticky='nsew')

    def create(self):
        # According to the scales, create a home
        board_width = self.board_width_scale.get()
        board_height = self.board_height_scale.get()
        hand_size = self.hand_size_scale.get()
        max_player_num = self.max_player_num_scale.get()
        self.conn.send(MessageCreateHome(board_width, board_height, hand_size, max_player_num, self.idnum,
                                         self.player_name).pack())

    def create_back(self):
        self.current_menu.grid_remove()
        self.current_menu = self.menu
        self.current_menu.grid(column=0, row=0, sticky='nsew')

    def join(self):
        home_id = self.home_id_entry.get()
        if not home_id.isnumeric():
            messagebox.showerror("Error", "Home ID must be alphanumeric")
            return None
        home_id = int(home_id)
        self.conn.send(MessageJoinHome(home_id, self.idnum, self.player_name).pack())

    def join_back(self):
        self.current_menu.grid_remove()
        self.current_menu = self.menu
        self.current_menu.grid(column=0, row=0, sticky='nsew')

    def create_game(self):
        # Create a new window for the game
        self.game_window = Toplevel(self.root, name="game_window")
        self.game_window.title("Game")
        self.game_window.protocol("WM_DELETE_WINDOW", self.game_window_on_quit)

        self.game = Game(self.game_window, self.conn, self.home, self.idnum)

    def on_quit(self):
        # When the main window closes, send a "close connection" message to the server and destroy the window
        self.conn.send(MessageCloseConnection(self.idnum).pack())
        self.root.destroy()

    def game_window_on_quit(self):
        # When the game window closes, send a "leave game" message to the server and clear the game
        self.conn.send(MessageLeaveGame(self.idnum).pack())
        self.clear_game()

    def clear_game(self):
        if self.game:
            self.game.destroy()
        if self.game_window:
            self.game_window.destroy()
        self.game = None
        self.game_window = None
