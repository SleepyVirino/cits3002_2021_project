import socket
import threading
from tkinter import messagebox

import protocol
from controller import Controller
from board import ALL_TILES
from home import Home
from yamlLoader import YamlLoader


# Configure the setting
settings = YamlLoader().load()
server_ip = settings['server']['ip']
server_port = settings['server']['port']
player_name = settings['player']['name']

# Create the socket and controller
conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
conn.connect((server_ip, server_port))

controller = Controller(conn)


def communication_thread(controller):

    # Socket in controller is constant until the connection is closed
    sock = controller.conn

    # The buffer is used to receive data and process
    buffer = bytearray()
    while True:
        try:
            chunk = sock.recv(4096)
            if chunk:
                # Read a chunk from the socket, and add it to the end of our buffer
                # (in case we had a partial message in the buffer from a previous
                # chunk, and we need the new chunk to complete it)
                buffer.extend(chunk)

                # Unpack as many messages as we can from the buffer.
                while True:
                    msg, consumed = protocol.read_message_from_bytearray(buffer)
                    if consumed:
                        buffer = buffer[consumed:]

                        if isinstance(msg, protocol.MessageWelcome):
                            with controller.lock:
                                controller.idnum = msg.idnum
                                controller.player_name = player_name

                        elif isinstance(msg, protocol.MessageHomeDetails):
                            # Create a home if no home exists
                            home = controller.home
                            if home:
                                pass
                            else:
                                home = Home(msg.id, msg.owner_id, msg.border_width, msg.border_height, msg.hand_size,
                                            msg.max_player)

                            # Controller update home and draw it
                            with controller.lock:
                                controller.home = home

                                # Configure the home and we need change the data type when necessary because all keys in
                                # json are strings.
                                home.player_list = msg.player_list
                                home.player_nums = {int(k): v for k, v in msg.player_nums.items()}
                                home.player_names = {int(k): v for k, v in msg.player_names.items()}
                                home.owner_id = msg.owner_id

                                controller.init_home_menu()
                                controller.draw_home_menu()

                        elif isinstance(msg, protocol.MessageHomeNotFound):
                            messagebox.showerror("Error:", "Sorry, we cannot not find home: %s" % msg.home_id)

                        elif isinstance(msg, protocol.MessageHomeFull):
                            messagebox.showerror("Error:", "Sorry, the home is full: %s" % msg.home_id)

                        elif isinstance(msg, protocol.MessageGameStart):
                            # Every client use this to ensure they are ready to play
                            conn.send(protocol.MessageGameStartOK().pack())
                            # Controller init the game
                            controller.create_game()

                        elif isinstance(msg, protocol.MessageAddTileToHand):
                            tileid = msg.tileid
                            if tileid < 0 or tileid >= len(ALL_TILES):
                                raise RuntimeError('Unknown tile index {}'.format(tileid))
                            controller.game.add_tile_to_hand(tileid)

                        elif isinstance(msg, protocol.MessagePlayerTurn):
                            controller.game.set_player_turn(msg.idnum)

                        elif isinstance(msg, protocol.MessagePlaceTile):
                            controller.game.tile_placed(msg)

                        elif isinstance(msg, protocol.MessageMoveToken):
                            controller.game.token_moved(msg)

                        elif isinstance(msg, protocol.MessagePlayerEliminated):
                            controller.game.set_player_eliminated(msg.idnum)

                        elif isinstance(msg, protocol.MessageGameOver):
                            # The msg.game_state < 0 means it must be a dogfall and otherwise means the id of
                            # someone who win
                            if msg.game_state < 0:
                                messagebox.showinfo("Game Over", "Game Over, Dog fall!")
                            else:
                                messagebox.showinfo("Game Over", "Game Over, Player %d win!" % msg.game_state)
                            # Controller clear the game
                            controller.clear_game()

                        elif isinstance(msg, protocol.MessageCloseConnection):
                            return

                        elif isinstance(msg,protocol.MessagePlayerNotEnough):
                            messagebox.showerror("Error:", "Sorry, the player is not enough!")

                        else:
                            messagebox.showerror("Error:", "Unknown message: {}".format(msg))

                    else:
                        break
            else:
                messagebox.showerror("Error:", "Server closed connection")
                controller.root.quit()
                break
        except Exception as e:
            messagebox.showerror("Error:", "Error: {}".format(e))
            controller.root.quit()
            break


# Define the thread and start
com_thread = threading.Thread(target=communication_thread, args=[controller])
com_thread.start()

# Start the main loop
controller.root.mainloop()

# Wait com_thread stop and then close connection
com_thread.join()
conn.close()
