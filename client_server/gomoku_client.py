import tkinter
import numpy as np
import socket
import threading
from enum import IntEnum


window = tkinter.Tk()

# sockets
soc = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# canvas where everything is drawn
c = tkinter.Canvas(window, bg="white", height=380, width=380)

# label for indicating whose turn it is
# lsuavez = tkinter.Label(window, text='', justify='center').grid(row=2, column=1)

connected = False

# ===================================================================================
class Colors(IntEnum):
    EMPTY = 0
    WHITE = 1
    BLACK = 2
# ======================================================================================

def netloop():

    restart()

    print("connected")
    global connected
    connected = True

    while connected:

        # the client will receive either a numpy matrix in bytes or commands as a string
        rec_bytes = soc.recv(1024)

        rec_str   = rec_bytes.decode()
        rec_split = rec_str.split(', ')

        # the other player can restart the game
        if (rec_str == "restart"):
            restart()        

        elif (rec_split[0] == "coords"):
            coords = list(map(int, rec_split[1].split(' ')))
            draw_line[coords]

        elif (rec_split[0] == "msg"):
            showinfo("Message", rec_split[1])

        else:
            grid = np.frombuffer(rec_bytes, dtype=np.ubyte)
            grid = grid.reshape(15, 15)

            draw_grid(grid)

    soc.close()

def cli_connect(host, port):
 
    soc.connect((host, port)) 

    thread = threading.Thread(target=netloop)
    thread.start()

# =======================================================================================


def onclick(eventorigin):

    x = (eventorigin.x - 5) // 25
    y = (eventorigin.y - 5) // 25
    
    # enviar pro servidor
    if connected:
        tuple_str = ("%d, %d" % (x, y));
        soc.send(tuple_str.encode())

# =======================================================================================

def draw_line(coords):

    # a red line showing where the victory condition was achieved

    for x in range(4):
        coords[x] = 15 + (coords[x] * 25)  # pixel coordinates

    c.create_line(coords, fill="red", width=10, tags="line")


def draw_grid(grid: np.ndarray):

    c.delete("circle")

    fill = '#C4A484'  # brown color for tiles

    x = 5
    y = 5

    for line in grid:
        for elem in line:

            c.create_rectangle(x, y, x + 20, y + 20, fill=fill)

            match elem:
                case Colors.EMPTY:
                    y = y + 25
                    continue
                case Colors.BLACK:
                    color = "black"
                case Colors.WHITE:
                    color = "white"
                
            c.create_oval(x, y, x + 20, y + 20, fill=color, tags="circle")

            y = y + 25
            
        y = 5
        x = x + 25


# =======================================================================================

def restart():

    c.delete("circle")
    c.delete("line")

    if connected:
        soc.send("restart".encode())


def config_window():

    window.title("Gomoku - Client")
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

    bconnect = tkinter.Button(window, text="Connect", command=lambda: cli_connect(ehost.get(), int(eport.get()))).grid(row=5, column=2)
    brestart = tkinter.Button(window, text="Restart", command=lambda: restart()).grid(row=6, column=2)

    # click do mouse no canvas
    c.bind("<Button 1>", onclick)

# ==========================================================================================

def main():
    
    # setar todos elementos da interface
    config_window()

    grid = np.zeros((15, 15), dtype=np.ubyte)

    # desenhar tabuleiro
    draw_grid(grid)

    window.mainloop()

    # fechar sockets
    soc.close()


if __name__ == '__main__':
    main()
