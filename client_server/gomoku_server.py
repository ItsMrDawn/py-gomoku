import tkinter
import numpy as np
import socket
import threading
from enum import IntEnum


PORT = 42069

# sockets
soc1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
soc2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# a 15x15 matrix representing the board state
grid = np.zeros((15, 15), dtype=np.ubyte)

# turn counter
turn = 0

connected = False
is_over   = False

# ===================================================================================
class Colors(IntEnum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2

class Directions(IntEnum):
    HORIZONTAL = 0
    VERTICAL = 1
    DIAGUP = 2
    DIAGDOWN = 3
# ======================================================================================

def netloop(insoc, inend):

    restart()
 
    print('player connected - address ' + inend[0] + ':' + str(inend[1]))
    
    global connected

    while connected:

        # the server will receive the x y coordinates of the play

        rec_str = insoc.recv(256).decode()

        # a player can call to restart the game
        if (rec_str == "restart"):

            if turn != 0:
                restart()

            continue

        x, y = tuple(map(int, rec_str.split(', ')))

        place_piece(x, y)
        check_victory(x, y)

    insoc.close()


def server_connect(port):

    serv.bind(('', port))
    serv.listen()

    global soc1, soc2, connected

    '''
    numcon = 0
    t = []
    while numcon < 2:
        soc, endcli = serv.accept()
        thread = threading.Thread(target=netloop, args=(soc, ))
        thread.start()
        t.append(thread)
        print('player connected - address ' + endcli[0] + ':' + str(endcli[1]))

        numcon = numcon + 1
    '''

    print('listening for connections on port ' + str(port))

    soc1, endcli1 = serv.accept()
    thread = threading.Thread(target=netloop, args=(soc1, endcli1))
    thread.start()

    connected = True

    soc2, endcli2 = serv.accept()
    thread2 = threading.Thread(target=netloop, args=(soc2, endcli2))
    thread2.start()

    while connected:
        continue

    # close sockets
    serv.close()


# =======================================================================================

def place_piece(inx, iny: int):

    # already has a piece
    if grid[inx, iny] != 0:
        return

    global turn

    if (turn % 2) == 0:
        grid[inx, iny] = Colors.BLACK
    else:
        grid[inx, iny] = Colors.WHITE

    turn = turn + 1

    # send the newly modified grid to both players
    soc1.send(grid.tobytes())
    soc2.send(grid.tobytes())


# return x1, y1, x2, y2 for drawing a line
def check_victory(inx, iny: int):

    # the idea here is to count how many consecutive pieces of a color there are in the 
    # line, column and diagonal of the piece that just got placed, to see if it
    # has achieved a victory condition

    coords = [0, 0, 0, 0]

    global turn
    if ((turn - 1) % 2) == 0:
        color = Colors.BLACK
    else:
        color = Colors.WHITE

    num_diag = 14 - (inx + iny)

    seqs = []
    seqs.append((Directions.VERTICAL,   grid[inx,:]))                           # column
    seqs.append((Directions.HORIZONTAL, grid[:,iny]))                           # line
    seqs.append((Directions.DIAGDOWN,   np.diagonal(grid, iny-inx, 0)))         # diagonal going down like \
    seqs.append((Directions.DIAGUP,     np.fliplr(grid).diagonal(num_diag, 0))) # diagonal going up like /

    for seq in seqs:

        consecutive = 0
        position    = -1
        direction   = seq[0]
        line        = seq[1]

        for x in line:

            position = position + 1

            if x == color:
                consecutive = consecutive + 1
            else:
                consecutive = 0   # combo breaker      
                continue

            # found 5 consecutive pieces of the same color
            if consecutive == 5:
                match direction:
                    case Directions.VERTICAL:   
                        coords = [inx, position - 4, inx, position]

                    case Directions.HORIZONTAL: 
                        coords = [position - 4, iny, position, iny]

                    case Directions.DIAGDOWN:
                        # upper portion, pos = y
                        if (inx - iny) > 0:
                            coords = [(inx - iny) + position - 4, position - 4, (inx - iny) + position, position]
                        else:  # lower portion, pos = x
                            coords = [position - 4, (iny - inx) + position - 4, position, (iny - inx) + position]   

                    case Directions.DIAGUP:
                        # upper portion, pos = x
                        if (num_diag) > 0:
                            coords = [position - 4, (14 - num_diag) - (position - 4), position, (14 - num_diag) - position]
                        else:  # lower portion, pos = y
                            coords = [abs(num_diag) + (position - 4), 14 - (position - 4), abs(num_diag) + position, 14 - position]

                break

        # if found a match, draw it and stop the game
        if coords != [0, 0, 0, 0]:

            coords_str = [str(int) for int in coords]
            coords_str = " ".join(coords_str)
            coords_str = "coords, " + coords_str
    
            soc1.send(coords_str.encode())
            soc2.send(coords_str.encode())

            if (turn % 2) == 0:
                soc1.send("msg, You won!".encode())
                soc2.send("msg, You lost :(".encode())
            else:
                soc1.send("msg, You lost :(".encode())
                soc2.send("msg, You won!".encode())

            return 1

    return 0


# =======================================================================================

def restart():
    global grid
    grid = np.zeros((15, 15), dtype=np.ubyte)

    global turn
    turn = 0

    global is_over
    is_over = False

#    if connected:
#        soc1.send("restart".encode())
#        soc2.send("restart".encode())

# ==========================================================================================

def main():

    server_connect(PORT)


if __name__ == '__main__':
    main()
