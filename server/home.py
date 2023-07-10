import random

from board import Board
from protocol import GameState


class Home():
    def __init__(self, id, owner_id, border_width=5, border_height=5, hand_size=4, max_player=4):
        self.owner_id = owner_id
        self.border_width = border_width
        self.border_height = border_height
        self.hand_size = hand_size
        self.max_player = max_player
        self.conns = {}
        self.id = id
        self.player_names = {}
        self.player_nums = {}
        self.player_list = []

        self.turn_round = {}
        self.left_player_list = []
        self.eliminated_player_list = []
        self.player_list_on_game = []
        self.current_player = None
        self.board = None
        self.running = False

    def update_on_game_list(self, leave_game_list):
        for leave_game_player in leave_game_list:
            if leave_game_player in self.player_list_on_game:
                self.player_list_on_game.remove(leave_game_player)

    def update_left_player(self, eliminated_player_list):

        for eliminated_player in eliminated_player_list:
            if eliminated_player not in self.eliminated_player_list:
                self.eliminated_player_list.append(eliminated_player)
            if eliminated_player in self.left_player_list:
                self.left_player_list.remove(eliminated_player)

    def update_order(self):
        if len(self.left_player_list) == 0:
            self.turn_round = {}
            self.current_player = None
        else:
            next_player = self.turn_round[self.current_player]
            while next_player in self.eliminated_player_list:
                next_player = self.turn_round[next_player]
            self.current_player = next_player
            for left_player in self.left_player_list:
                next_player = self.turn_round[left_player]
                while next_player in self.eliminated_player_list:
                    next_player = self.turn_round[next_player]
                self.turn_round[left_player] = next_player

    def init_game_state(self):
        self.running = True
        board = Board(self.border_width, self.border_height)
        self.board = board
        random.shuffle(self.player_list)
        for i in range(len(self.player_list) - 1):
            self.turn_round[self.player_list[i]] = self.player_list[i + 1]
        else:
            self.turn_round[self.player_list[-1]] = self.player_list[0]
        self.current_player = self.player_list[0]
        self.left_player_list = list(self.player_list)
        self.eliminated_player_list = []
        self.player_list_on_game = list(self.player_list)

    def clear_game_state(self):
        self.running = False
        self.board = None
        self.turn_round = {}
        self.current_player = None
        self.left_player_list = []
        self.eliminated_player_list = []
        self.player_list_on_game = []

    def append_player(self, player_idnum, player_name, conn=None):
        self.player_names[player_idnum] = player_name
        self.player_list.append(player_idnum)
        for i in range(self.max_player):
            if i not in self.player_nums.values():
                self.player_nums[player_idnum] = i
                break
        self.conns[player_idnum] = conn

    def delete_player(self, player_idnum):
        del self.player_names[player_idnum]
        self.player_list.remove(player_idnum)
        del self.player_nums[player_idnum]
        del self.conns[player_idnum]

    def is_empty(self):
        return len(self.player_list) == 0

    def is_full(self):
        return len(self.player_list) == self.max_player

    def game_state(self):
        if len(self.left_player_list) == 1:
            return self.left_player_list[0]
        elif len(self.left_player_list) == 0:
            return GameState.DOG_FALL
        else:
            return GameState.RUNNING
