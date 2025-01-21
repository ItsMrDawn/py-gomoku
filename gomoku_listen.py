import tkinter
from tkinter.messagebox import showinfo
import numpy as np
import socket
import threading
from enum import IntEnum


window = tkinter.Tk()

# sockets
soc  = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# canvas where everything is drawn
c = tkinter.Canvas(window, bg="white", height=380, width=380)

# label for indicating whose turn it is
# lyourturn = tkinter.Label(window, text='', justify='center').grid(row=2, column=1)

# a 15x15 matrix representing the board state
grid = np.zeros((15, 15), dtype=np.ubyte)

# turn counter
turn = 0

connected = False
is_over   = False
is_server = False

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

def netloop():

    restart()

    print("connected")
    global connected
    connected = True

    while connected:
        rec_str = soc.recv(256).decode()

        # the other player can restart the game
        if (rec_str == "restart"):

            if turn != 0:
                restart()

            continue

        x, y = tuple(map(int, rec_str.split(', ')))

        draw_circle(x, y)
        check_victory(x, y)

    soc.close()

def cli_connect(host, port):

    soc.connect((host, port)) 

    window.title("Gomoku - Client (Black)")

    thread = threading.Thread(target=netloop)
    thread.start()

def server_connect(port):

    serv.bind(('', port))
    serv.listen()

    global soc, is_server

    soc, endcli = serv.accept()

    window.title("Gomoku - Host (White)")
    is_server = True

    thread = threading.Thread(target=netloop)
    thread.start()


# =======================================================================================


def onclick(eventorigin):

    if is_over:
        return

    x = (eventorigin.x - 5) // 25
    y = (eventorigin.y - 5) // 25

    # send click location to the other application
    if connected:
        if (((turn % 2) == 0) and is_server) or (((turn % 2) != 0) and not is_server):
            return

        tuple_str = ("%d, %d" % (x, y));
        soc.send(tuple_str.encode())

    draw_circle(x, y)
    check_victory(x, y)

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
        position = -1
        direction = seq[0]
        line = seq[1]

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
            draw_line(coords)
            return 1

    return 0


# =======================================================================================

def draw_line(coords):

    # a red line showing where the victory condition was achieved

    for x in range(4):
        coords[x] = 15 + (coords[x] * 25)  # pixel coordinates

    c.create_line(coords, fill="red", width=10, tags="line")

    global turn, is_server

    if (((turn % 2) == 0) and is_server) or (((turn % 2) != 0) and not is_server):
        showinfo("End", "You won!")
    else:
        showinfo("End", "You lost :(")


def draw_circle(inx, iny: int):

    # the piece placed by a player

    if grid[inx, iny] != 0:
        return

    global turn

    if (turn % 2) == 0:
        fill = "black"
        grid[inx, iny] = Colors.BLACK
    else:
        fill = "white"
        grid[inx, iny] = Colors.WHITE

    turn = turn + 1

    x = 5 + (inx * 25)
    y = 5 + (iny * 25)

    c.create_oval(x, y, x + 20, y + 20, fill=fill, tags="circle")


def draw_grid():
  
    # the board

    fill = '#C4A484'  # brown color for tiles

    x = 5
    y = 5

    for line in grid:
        for col in line:

            c.create_rectangle(x, y, x + 20, y + 20, fill=fill)

            y = y + 25

        y = 5
        x = x + 25


# =======================================================================================

def restart():
    global grid
    grid = np.zeros((15, 15), dtype=np.ubyte)

    global turn
    turn = 0

    global is_over
    is_over = False

    c.delete("circle")
    c.delete("line")

    if connected:
        soc.send("restart".encode())


def config_window():

    window.title("Gomoku")
    window.geometry('390x480')

    c.grid(row=0, columnspan=3)

    tkinter.Label(window, text='Address:', justify='right').grid(row=5, column=0)
    tkinter.Label(window, text='Port:', justify='right').grid(row=6, column=0)

    ehost = tkinter.Entry(window)
    ehost.grid(row=5, column=1)
    ehost.insert(tkinter.END, '127.0.0.1')

    eport = tkinter.Entry(window)
    eport.grid(row=6, column=1)
    eport.insert(tkinter.END, '42069')

    bconnect  = tkinter.Button(window, text="Connect", command=lambda: cli_connect(ehost.get(), int(eport.get()))).grid(row=5, column=2)
    blisten    = tkinter.Button(window, text="Listen", command=lambda: server_connect(int(eport.get()))).grid(row=6, column=2)
    brestart = tkinter.Button(window, text="Restart",  command=lambda: restart()).grid(row=7, column=1)

    # mouse click event on the canvas
    c.bind("<Button 1>", onclick)

# ==========================================================================================

def main():
    
    # configure all the UI elements
    config_window()

    # draw the board
    draw_grid()

    window.mainloop()

    # close the sockets
    soc.close()
    serv.close()


if __name__ == '__main__':
    main()
