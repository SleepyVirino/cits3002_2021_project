import socket
import threading

import protocol
from tile import get_random_tileid
from home import Home


def client_handler(connection, address, idnum):
    # Send welcome message to client and allocate id
    connection.send(protocol.MessageWelcome(idnum).pack())

    home = None
    home_id = None

    buffer = bytearray()

    while True:
        chunk = connection.recv(4096)
        if not chunk:
            print('client {} disconnected'.format(address))
            return

        buffer.extend(chunk)

        while True:
            msg, consumed = protocol.read_message_from_bytearray(buffer)
            if not consumed:
                break

            buffer = buffer[consumed:]

            print('received message {}'.format(msg))

            # sent by the player to put a tile onto the board (in all turns except
            # their second)
            if isinstance(msg, protocol.MessageCreateHome):
                # Create home, configure it, add home to all homes and send the creator the home details
                with all_homes_lock:
                    global create_home_id
                    home_id = create_home_id
                    create_home_id += 1
                    home = Home(home_id, msg.player_idnum, msg.width, msg.height, msg.hand_size, msg.max_players)
                    home.append_player(msg.player_idnum, msg.player_name, connection)

                    all_homes[home_id] = home

                    connection.send(protocol.MessageHomeDetails(home.border_width, home.border_height, home.hand_size,
                                                                home.max_player, home.id, home.owner_id,
                                                                home.player_names,
                                                                home.player_nums, home.player_list).pack())

            elif isinstance(msg, protocol.MessageCloseConnection):
                # Close connection and delete player from home, but we need maintain the home and the game
                with all_homes_lock:
                    if home:
                        home.delete_player(msg.player_id)
                        if home.is_empty():
                            pass
                        else:
                            if msg.player_id == home.owner_id:
                                home.owner_id = home.player_list[0]
                            for idnum in home.conns:
                                home.conns[idnum].send(
                                    protocol.MessageHomeDetails(home.border_width, home.border_height, home.hand_size,
                                                                home.max_player, home.id, home.owner_id,
                                                                home.player_names,
                                                                home.player_nums, home.player_list).pack())
                            if home.running:
                                home.update_on_game_list([msg.player_id])
                                home.update_left_player([msg.player_id])
                                game_state = home.game_state()
                                if game_state == protocol.GameState.RUNNING:

                                    if msg.player_id == home.current_player:
                                        home.update_order()
                                        for idnum in home.player_list_on_game:
                                            home.conns[idnum].send(
                                                protocol.MessagePlayerTurn(home.current_player).pack())
                                else:

                                    for idnum in home.conns:
                                        home.conns[idnum].send(protocol.MessageGameOver(game_state).pack())
                                    home.clear_game_state()
                        if home.is_empty():
                            del all_homes[home_id]
                        home = None
                connection.send(protocol.MessageCloseConnection(msg.player_id).pack())
                connection.close()
                print("client {} disconnected".format(address))
                return

            elif isinstance(msg, protocol.MessageLeaveHome):
                # Delete player from home, but we need maintain the home and the game
                with all_homes_lock:
                    home.delete_player(msg.player_id)
                    if home.is_empty():
                        pass
                    else:
                        if msg.player_id == home.owner_id:
                            home.owner_id = home.player_list[0]
                        for idnum in home.conns:
                            home.conns[idnum].send(
                                protocol.MessageHomeDetails(home.border_width, home.border_height, home.hand_size,
                                                            home.max_player, home.id, home.owner_id, home.player_names,
                                                            home.player_nums, home.player_list).pack())
                        if home.running:
                            home.update_on_game_list([msg.player_id])
                            home.update_left_player([msg.player_id])
                            game_state = home.game_state()
                            if game_state == protocol.GameState.RUNNING:

                                if msg.player_id == home.current_player:
                                    home.update_order()
                                    for idnum in home.player_list_on_game:
                                        home.conns[idnum].send(protocol.MessagePlayerTurn(home.current_player).pack())
                            else:

                                for idnum in home.conns:
                                    home.conns[idnum].send(protocol.MessageGameOver(game_state).pack())
                                home.clear_game_state()

                    if home.is_empty():
                        del all_homes[home_id]
                    home = None

            elif isinstance(msg, protocol.MessageJoinHome):
                # Send home details to all players after someone joined, or send home full message or home not found
                with all_homes_lock:
                    home = all_homes.get(msg.home_id, None)
                    if not home:
                        connection.send(protocol.MessageHomeNotFound(msg.home_id).pack())
                        continue
                    if home.is_full():
                        connection.send(protocol.MessageHomeFull(msg.home_id).pack())
                        continue
                    home.append_player(msg.player_id, msg.player_name, connection)
                    for idnum in home.conns:
                        home.conns[idnum].send(
                            protocol.MessageHomeDetails(home.border_width, home.border_height, home.hand_size,
                                                        home.max_player, home.id, home.owner_id, home.player_names,
                                                        home.player_nums, home.player_list).pack())

            elif isinstance(msg, protocol.MessageMatchHome):
                # Send home details to all players after someone matched, or send home not found
                with all_homes_lock:
                    for home_id, home_ in all_homes.items():
                        if not home_.is_full():
                            home = home_
                            home.append_player(msg.player_id, msg.player_name, connection)
                            for idnum in home.conns:
                                home.conns[idnum].send(
                                    protocol.MessageHomeDetails(home.border_width, home.border_height, home.hand_size,
                                                                home.max_player, home.id, home.owner_id,
                                                                home.player_names,
                                                                home.player_nums, home.player_list).pack())
                            break
                    else:
                        connection.send(protocol.MessageHomeNotFound(0).pack())

            elif isinstance(msg, protocol.MessageGameStart):
                # Send game start message to all players in the home when the number of players is enough
                with all_homes_lock:
                    if len(home.player_list) < 2:
                        connection.send(protocol.MessagePlayerNotEnough().pack())
                        continue

                    for idnum in home.conns:
                        home.conns[idnum].send(protocol.MessageGameStart().pack())
                    home.init_game_state()

            elif isinstance(msg, protocol.MessageGameStartOK):
                with all_homes_lock:
                    for _ in range(home.hand_size):
                        tileid = get_random_tileid()
                        connection.send(protocol.MessageAddTileToHand(tileid).pack())
                    connection.send(protocol.MessagePlayerTurn(home.current_player).pack())

            elif isinstance(msg, protocol.MessageLeaveGame):
                with all_homes_lock:
                    home.update_on_game_list([msg.player_id])
                    home.update_left_player([msg.player_id])
                    if not home.running:
                        continue
                    game_state = home.game_state()
                    if game_state == protocol.GameState.RUNNING:
                        if msg.player_id == home.current_player:
                            home.update_order()
                            for idnum in home.player_list_on_game:
                                home.conns[idnum].send(protocol.MessagePlayerTurn(home.current_player).pack())
                    else:
                        for idnum in home.player_list_on_game:
                            home.conns[idnum].send(protocol.MessageGameOver(game_state).pack())
                        home.clear_game_state()

            elif isinstance(msg, protocol.MessagePlaceTile):
                with all_homes_lock:
                    if home.board.set_tile(msg.x, msg.y, msg.tileid, msg.rotation, msg.idnum):
                        # notify all clients that placement was successful
                        for idnum in home.player_list_on_game:
                            home.conns[idnum].send(msg.pack())

                        # check for token movement
                        positionupdates, eliminated = home.board.do_player_movement(home.left_player_list)
                        home.update_left_player(eliminated)
                        home.update_order()
                        for msg in positionupdates:
                            for idnum in home.player_list_on_game:
                                home.conns[idnum].send(msg.pack())

                        for idnum in eliminated:
                            for idnum_ in home.player_list_on_game:
                                home.conns[idnum_].send(protocol.MessagePlayerEliminated(idnum).pack())

                        game_state = home.game_state()
                        if game_state == protocol.GameState.RUNNING:
                            pass
                        else:
                            for idnum in home.player_list_on_game:
                                home.conns[idnum].send(protocol.MessageGameOver(game_state).pack())
                            home.clear_game_state()
                            continue

                        if idnum not in eliminated:
                            # pickup a new tile
                            tileid = get_random_tileid()
                            connection.send(protocol.MessageAddTileToHand(tileid).pack())

                        # start next turn
                        for idnum in home.player_list_on_game:
                            home.conns[idnum].send(protocol.MessagePlayerTurn(home.current_player).pack())

            elif isinstance(msg, protocol.MessageMoveToken):
                # sent by the player in the second turn, to choose their token's starting path
                with all_homes_lock:
                    if not home.board.have_player_position(msg.idnum):
                        if home.board.set_player_start_position(msg.idnum, msg.x, msg.y, msg.position):
                            # check for token movement
                            positionupdates, eliminated = home.board.do_player_movement(home.left_player_list)

                            home.update_left_player(eliminated)
                            home.update_order()
                            for msg in positionupdates:
                                for idnum in home.player_list_on_game:
                                    home.conns[idnum].send(msg.pack())

                            for idnum in eliminated:
                                for idnum_ in home.player_list_on_game:
                                    home.conns[idnum_].send(protocol.MessagePlayerEliminated(idnum).pack())
                            game_state = home.game_state()
                            if game_state == protocol.GameState.RUNNING:
                                pass
                            else:
                                for idnum in home.player_list_on_game:
                                    home.conns[idnum].send(protocol.MessageGameOver(game_state).pack())
                                home.clear_game_state()
                                continue
                            # start next turn
                            for idnum in home.player_list_on_game:
                                home.conns[idnum].send(protocol.MessagePlayerTurn(home.current_player).pack())


# create a TCP/IP socket
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# listen on all network interfaces
server_address = ('', 30020)
sock.bind(server_address)

print('listening on {}'.format(sock.getsockname()))

sock.listen(5)
# Global variables
idnum = 0
all_homes = {}
create_home_id = 0
all_homes_lock = threading.Lock()

while True:
    # handle each new connection independently
    connection, client_address = sock.accept()
    print('received connection from {}'.format(client_address))
    tr = threading.Thread(target=client_handler, args=(connection, client_address, idnum))
    tr.start()
    idnum += 1
