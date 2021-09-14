# https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/intro.html

import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
# import old_peer

def set_peer_port(*args):
    print('Port:', p_port_entry.get())

def starting_window():
    global p_port_entry

    p_port_frame = ttk.Frame(wind)
    p_port_frame.pack(pady=10)

    welcome_msg = ttk.Label(p_port_frame, text='Welcome in world of Harshit', font=('', 20))
    welcome_msg.grid(row=0, column=0, padx=5, pady=5, columnspan=2)

    p_port_label = ttk.Label(p_port_frame, text='Enter your port')
    p_port_label.grid(row=1, column=0, padx=5, pady=5, sticky=tk.E)

    p_port_entry = ttk.Entry(p_port_frame)
    p_port_entry.grid(row=1, column=1, padx=5, pady=5, sticky=tk.W)

    p_port_button = ttk.Button(p_port_frame, text='Start', command=set_peer_port)
    p_port_button.grid(row=2, column=0, padx=5, pady=5, columnspan=2)

wind = tk.Tk()
wind.geometry('500x300')
wind.resizable(0, 0)

style = ttk.Style()
# style.theme_use('alt')
# theme_names = ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')

starting_window()

p_port_entry.focus()
wind.bind('<Return>', set_peer_port)

wind.mainloop()
