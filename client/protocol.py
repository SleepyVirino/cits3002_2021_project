# CITS3002 2021 Assignment
#
# This module defines essential constants and gameplay logic, which is shared
# by both the client and the server.
#
# This file MUST NOT be modified! The markers may use a different copy of the
# client, which will expect the constants and message definitions to exactly
# match the below.

import struct
from enum import IntEnum
import json


class MessageType(IntEnum):
    """identify the kinds of messages that can be passed between server and
    client. each message will start with a value from this enumeration, so that
    the reader can determine how to interpret the remaining bytes in the message.
    """
    WELCOME = 1
    GAME_START = 2
    ADD_TILE_TO_HAND = 3
    PLAYER_TURN = 4
    PLACE_TILE = 5
    MOVE_TOKEN = 6
    PLAYER_ELIMINATED = 7
    CREATE_HOME = 8
    HOME_DETAILS = 9
    LEAVE_HOME = 10
    JOIN_HOME = 11
    HOME_NOT_FOUND = 12
    HOME_FULL = 13
    MATCH_HOME = 14
    GAME_START_OK = 15
    GAME_OVER = 16
    LEAVE_GAME = 17
    CLOSE_CONNECTION = 18
    PLAYER_NOT_ENOUGH = 19
    PLAYER_NOT_FOUND = 20


class MessageWelcome():
    """Sent by the server to joining clients, to notify them of their idnum."""

    def __init__(self, idnum: int):
        self.idnum = idnum

    def pack(self):
        return struct.pack('!HH', MessageType.WELCOME, self.idnum)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, idnum = struct.unpack_from('!HH', bs, 0)
            return cls(idnum), messagelen

        return None, 0

    def __str__(self):
        return f"Welcome to the game! your ID is {self.idnum}."


class MessageGameStart():
    """Sent by the server to all clients, when a new game has started."""

    def pack(self):
        return struct.pack('!H', MessageType.GAME_START)

    def __str__(self):
        return "Game has started!"


class MessageAddTileToHand():
    """Sent by the server to a single client, to add a new tile to that client's
    hand.
    """

    def __init__(self, tileid):
        self.tileid = tileid

    def pack(self):
        return struct.pack('!HH', MessageType.ADD_TILE_TO_HAND, self.tileid)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, tileid = struct.unpack_from('!HH', bs, 0)
            return MessageAddTileToHand(tileid), messagelen

        return None, 0

    def __str__(self):
        return "Tiles are now added to your hand!"


class MessagePlayerTurn():
    """Sent by the server to all clients to indicate that a new turn has
    started.
    """

    def __init__(self, idnum: int):
        self.idnum = idnum

    def pack(self):
        return struct.pack('!HH', MessageType.PLAYER_TURN, self.idnum)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, idnum = struct.unpack_from('!HH', bs, 0)
            return cls(idnum), messagelen

        return None, 0

    def __str__(self):
        return "A new turn has started!"


class MessagePlaceTile():
    """Sent by the current player to the server to indicate that they want to
    place a tile from their hand in a particular location on the board.

    Sent by the server to all players to indicate that a player placed a tile onto
    the board.
    """

    def __init__(self, idnum: int, tileid: int, rotation: int, x: int, y: int):
        self.idnum = idnum
        self.tileid = tileid
        self.rotation = rotation
        self.x = x
        self.y = y

    def pack(self):
        return struct.pack('!HHHHHH', MessageType.PLACE_TILE, self.idnum,
                           self.tileid, self.rotation, self.x, self.y)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HHHHHH')

        if len(bs) >= messagelen:
            _, idnum, tileid, rotation, x, y = struct.unpack_from('!HHHHHH', bs, 0)
            return MessagePlaceTile(idnum, tileid, rotation, x, y), messagelen

        return None, 0

    def __str__(self):
        return "A player placed his/her tile!"


class MessageMoveToken():
    """Sent by the current player to the server on turn 2, to indicate which
    starting location they choose for their token.

    Sent by the server to all players to indicate the updated location of a
    player's token (either when they select the start location, or when a placed
    tile causes their token to move).
    """

    def __init__(self, idnum: int, x: int, y: int, position: int):
        self.idnum = idnum
        self.x = x
        self.y = y
        self.position = position

    def pack(self):
        return struct.pack('!HHHHH', MessageType.MOVE_TOKEN, self.idnum,
                           self.x, self.y, self.position)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HHHHH')

        if len(bs) >= messagelen:
            _, idnum, x, y, position = struct.unpack_from('!HHHHH', bs, 0)
            return cls(idnum, x, y, position), messagelen

        return None, 0

    def __str__(self):
        return "Player has decided its starting position!"


class MessagePlayerEliminated():
    """Sent by the server to all clients when a player is eliminated from the
    current game (either because their token left the board, or because the
    client disconnected).
    """

    def __init__(self, idnum: int):
        self.idnum = idnum

    def pack(self):
        return struct.pack('!HH', MessageType.PLAYER_ELIMINATED, self.idnum)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, idnum = struct.unpack_from('!HH', bs, 0)
            return cls(idnum), messagelen

        return None, 0

    def __str__(self):
        return "A player has been eliminated!"


class MessageCreateHome():
    def __init__(self, width, height, hand_size, max_players, player_idnum, player_name):
        self.player_idnum = player_idnum
        self.player_name = player_name
        self.width = width
        self.height = height
        self.hand_size = hand_size
        self.max_players = max_players

    def pack(self):
        return struct.pack('!HHHHHHH{}s'.format(len(self.player_name)), MessageType.CREATE_HOME,
                           self.width, self.height, self.hand_size, self.max_players,
                           self.player_idnum, len(self.player_name), self.player_name.encode('utf-8'))

    @classmethod
    def unpack(cls, bs: bytearray):
        headerlen = struct.calcsize('!HHHHHHH')

        if len(bs) >= headerlen:
            _, width, height, hand_size, max_players, player_idnum, name_len = struct.unpack_from('!HHHHHHH', bs, 0)
            if len(bs) >= headerlen + name_len:
                player_name, = struct.unpack_from('!{}s'.format(name_len), bs, headerlen)
                return cls(width, height, hand_size, max_players, player_idnum,
                           player_name.decode('utf-8')), headerlen + name_len

        return None, 0


class MessageHomeDetails():
    def __init__(self, border_width, border_height, hand_size, max_player, id, owner_id, player_names, player_nums,
                 player_list):
        self.border_width = border_width
        self.border_height = border_height
        self.hand_size = hand_size
        self.max_player = max_player
        self.id = id
        self.owner_id = owner_id
        self.player_names = player_names
        self.player_nums = player_nums
        self.player_list = player_list
        self.player_names_str = json.dumps(self.player_names)
        self.player_nums_str = json.dumps(self.player_nums)
        self.player_list_str = json.dumps(self.player_list)

    def pack(self):
        return struct.pack('!HHHHHHHHHH{}s{}s{}s'.format(len(self.player_names_str), len(self.player_nums_str),
                                                         len(self.player_list_str)), MessageType.HOME_DETAILS,
                           self.border_width, self.border_height, self.hand_size, self.max_player,
                           self.id, self.owner_id, len(self.player_names_str), len(self.player_nums_str),
                           len(self.player_list_str),
                           self.player_names_str.encode('utf-8'), self.player_nums_str.encode('utf-8'),
                           self.player_list_str.encode('utf-8'))

    @classmethod
    def unpack(cls, bs: bytearray):
        headerlen = struct.calcsize('!HHHHHHHHHH')

        if len(bs) >= headerlen:
            _, border_width, border_height, hand_size, max_player, id, owner_id, name_len, num_len, list_len = struct.unpack_from(
                '!HHHHHHHHHH', bs, 0)
            if len(bs) >= headerlen + name_len + num_len + list_len:
                player_names, = struct.unpack_from('!{}s'.format(name_len), bs, headerlen)
                player_nums, = struct.unpack_from('!{}s'.format(num_len), bs, headerlen + name_len)
                player_list, = struct.unpack_from('!{}s'.format(list_len), bs, headerlen + name_len + num_len)
                return cls(border_width, border_height, hand_size, max_player, id, owner_id,
                           json.loads(player_names.decode('utf-8')), json.loads(player_nums.decode('utf-8')),
                           json.loads(player_list.decode('utf-8'))), headerlen + name_len + num_len + list_len

        return None, 0


class MessageLeaveHome():
    def __init__(self, player_id):
        self.player_id = player_id

    def pack(self):
        return struct.pack('!HH', MessageType.LEAVE_HOME, self.player_id)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, player_id = struct.unpack_from('!HH', bs, 0)
            return cls(player_id), messagelen

        return None, 0


class MessageJoinHome():
    def __init__(self, home_id, player_id, player_name):
        self.player_id = player_id
        self.home_id = home_id
        self.player_name = player_name

    def pack(self):
        return struct.pack('!HHHH{}s'.format(len(self.player_name)), MessageType.JOIN_HOME, self.home_id,
                           self.player_id,
                           len(self.player_name), self.player_name.encode('utf-8'))

    @classmethod
    def unpack(cls, bs: bytearray):
        headerlen = struct.calcsize('!HHHH')

        if len(bs) >= headerlen:
            _, home_id, player_id, name_len = struct.unpack_from('!HHHH', bs, 0)
            if len(bs) >= headerlen + name_len:
                player_name, = struct.unpack_from('!{}s'.format(name_len), bs, headerlen)
                return cls(home_id, player_id, player_name.decode('utf-8')), headerlen + name_len

        return None, 0


class MessageHomeNotFound():
    def __init__(self, home_id):
        self.home_id = home_id

    def pack(self):
        return struct.pack('!HH', MessageType.HOME_NOT_FOUND, self.home_id)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, home_id = struct.unpack_from('!HH', bs, 0)
            return cls(home_id), messagelen

        return None, 0


class MessageHomeFull():
    def __init__(self, home_id):
        self.home_id = home_id

    def pack(self):
        return struct.pack('!HH', MessageType.HOME_FULL, self.home_id)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, home_id = struct.unpack_from('!HH', bs, 0)
            return cls(home_id), messagelen

        return None, 0


class MessageMatchHome():
    def __init__(self, player_id, player_name):
        self.player_id = player_id
        self.player_name = player_name

    def pack(self):
        return struct.pack('!HHH{}s'.format(len(self.player_name)), MessageType.MATCH_HOME, self.player_id,
                           len(self.player_name), self.player_name.encode('utf-8'))

    @classmethod
    def unpack(cls, bs: bytearray):
        headerlen = struct.calcsize('!HHH')

        if len(bs) >= headerlen:
            _, player_id, name_len = struct.unpack_from('!HHH', bs, 0)
            if len(bs) >= headerlen + name_len:
                player_name, = struct.unpack_from('!{}s'.format(name_len), bs, headerlen)
                return cls(player_id, player_name.decode('utf-8')), headerlen + name_len

        return None, 0


class MessageGameStartOK():
    def __init__(self):
        pass

    def pack(self):
        return struct.pack('!H', MessageType.GAME_START_OK)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!H')

        if len(bs) >= messagelen:
            return cls(), messagelen

        return None, 0


class MessageGameOver():
    def __init__(self, game_state):
        self.game_state = game_state

    def pack(self):
        return struct.pack('!Hi', MessageType.GAME_OVER, self.game_state)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!Hi')

        if len(bs) >= messagelen:
            _, game_state = struct.unpack_from('!Hi', bs, 0)
            return cls(game_state), messagelen

        return None, 0


class MessageLeaveGame():
    def __init__(self, player_id):
        self.player_id = player_id

    def pack(self):
        return struct.pack('!HH', MessageType.LEAVE_GAME, self.player_id)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, player_id = struct.unpack_from('!HH', bs, 0)
            return cls(player_id), messagelen

        return None, 0


class MessageCloseConnection():
    def __init__(self, player_id):
        self.player_id = player_id

    def pack(self):
        return struct.pack('!HH', MessageType.CLOSE_CONNECTION, self.player_id)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!HH')

        if len(bs) >= messagelen:
            _, player_id = struct.unpack_from('!HH', bs, 0)
            return cls(player_id), messagelen

        return None, 0


class MessagePlayerNotEnough():
    def __init__(self):
        pass

    def pack(self):
        return struct.pack('!H', MessageType.PLAYER_NOT_ENOUGH)

    @classmethod
    def unpack(cls, bs: bytearray):
        messagelen = struct.calcsize('!H')

        if len(bs) >= messagelen:
            return cls(), messagelen

        return None, 0


def read_message_from_bytearray(bs: bytearray):
    """Attempts to read and unpack a single message from the beginning of the
    provided bytearray. If successful, it returns (msg, number_of_bytes_consumed).
    If unable to read a message (because there are insufficient bytes), it returns
    (None, 0).
    """

    msg = None
    consumed = 0

    typesize = struct.calcsize('!H')

    if len(bs) >= typesize:
        typeint, = struct.unpack_from('!H', bs, 0)

        if typeint == MessageType.WELCOME:
            msg, consumed = MessageWelcome.unpack(bs)
        elif typeint == MessageType.GAME_START:
            msg, consumed = MessageGameStart(), typesize
        elif typeint == MessageType.ADD_TILE_TO_HAND:
            msg, consumed = MessageAddTileToHand.unpack(bs)
        elif typeint == MessageType.PLAYER_TURN:
            msg, consumed = MessagePlayerTurn.unpack(bs)
        elif typeint == MessageType.PLACE_TILE:
            msg, consumed = MessagePlaceTile.unpack(bs)
        elif typeint == MessageType.MOVE_TOKEN:
            msg, consumed = MessageMoveToken.unpack(bs)
        elif typeint == MessageType.PLAYER_ELIMINATED:
            msg, consumed = MessagePlayerEliminated.unpack(bs)
        elif typeint == MessageType.CREATE_HOME:
            msg, consumed = MessageCreateHome.unpack(bs)
        elif typeint == MessageType.HOME_DETAILS:
            msg, consumed = MessageHomeDetails.unpack(bs)
        elif typeint == MessageType.LEAVE_HOME:
            msg, consumed = MessageLeaveHome.unpack(bs)
        elif typeint == MessageType.JOIN_HOME:
            msg, consumed = MessageJoinHome.unpack(bs)
        elif typeint == MessageType.HOME_NOT_FOUND:
            msg, consumed = MessageHomeNotFound.unpack(bs)
        elif typeint == MessageType.HOME_FULL:
            msg, consumed = MessageHomeFull.unpack(bs)
        elif typeint == MessageType.MATCH_HOME:
            msg, consumed = MessageMatchHome.unpack(bs)
        elif typeint == MessageType.GAME_START_OK:
            msg, consumed = MessageGameStartOK.unpack(bs)
        elif typeint == MessageType.GAME_OVER:
            msg, consumed = MessageGameOver.unpack(bs)
        elif typeint == MessageType.LEAVE_GAME:
            msg, consumed = MessageLeaveGame.unpack(bs)
        elif typeint == MessageType.CLOSE_CONNECTION:
            msg, consumed = MessageCloseConnection.unpack(bs)
        elif typeint == MessageType.PLAYER_NOT_ENOUGH:
            msg, consumed = MessagePlayerNotEnough.unpack(bs)

    return msg, consumed
