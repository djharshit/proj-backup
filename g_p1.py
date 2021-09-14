import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from queue import Queue
import threading
import pickle
import json
# import a

# ====== GUI ======
wind = tk.Tk()
wind.title('Peer program')
wind.geometry('600x400')
wind.resizable(0, 0)

# wind.rowconfigure(0, weight=1)
# wind.columnconfigure(0, weight=1)

# ====== Variables ======
details = None
peers = {}
trck_color = 'red'
peer_color = 'blue'
uid = tk.StringVar()
name = tk.StringVar()
pwd = tk.StringVar()
t_port = tk.StringVar()
s_port = tk.StringVar()
i = tk.IntVar()
q = Queue()


def change_frame(frame):
    frame.tkraise()


def check_state():
    if i.get():
        change_frame(peer_frame)
    else:
        change_frame(trck_frame)


def start_mys(port_var):
    try:
        port = int(port_var.get())
    except ValueError:
        messagebox.showerror('Invalid', 'Wrong port number')

    else:
        # wind.bind('<Return>', lambda x: ...)

        mys = a.MyServer(port)

        srvr_thrd = threading.Thread(target=mys.accept_conn)
        srvr_thrd.start()

        q.put(port)
        change_frame(sec_frame)
        p_port_label['text'] = f'Peer Port\n{port}'

        # t = threading.Thread(target=server_start)
        # t.start()
        # t.join()

    # try:
    #     x = 5
    # except ConnectionRefusedError:
    #     messagebox.showwarning('Sleeping', f'Port {port} is sleeping')

def check_trck_port(port_var):
    global trck_clnt

    try:
        port = int(port_var.get())
    except ValueError:
        messagebox.showerror('Invalid', 'Wrong port number')

    else:
        trck_clnt = a.MyClient(port)

        if trck_clnt.server_connect():
            q.put(port)
            change_frame(trck_frame_2)

            print('[+] Connected to', port)
            trck_clnt.send_msg(str(s_port.get()).encode())

        else:
            messagebox.showwarning('Sleeping', f'Tracker {port} is sleeping')


def login(*args):
    global trck_clnt

    user = uid.get() + ' ' + pwd.get()
    trck_clnt.send_msg(b'login')
    trck_clnt.send_msg(user.encode())

    data = trck_clnt.receive_msg()

    trck_msg, *details = pickle.loads(data)
    print(trck_msg)

    if trck_msg in ['Wrong password', 'Uid not found']:
        messagebox.showwarning('Invalid', trck_msg)

    else:
        change_frame(trck_frame_5)

def register(*args):
    ...


# def

# style = ttk.Style()
# style.theme_use('alt')
# theme_names = ('winnative', 'clam', 'alt', 'default', 'classic', 'vista', 'xpnative')

start_frame = tk.Frame(wind)
sec_frame = tk.Frame(wind)
start_frame.grid(row=0, column=0, sticky='nsew')
sec_frame.grid(row=0, column=0, sticky='nsew')

# ====== Starting Frame ======
welcome_msg = tk.Label(start_frame, text='Peer program', font=('', 20, 'bold'))
welcome_msg.grid(row=0, column=0, padx=25, pady=5, columnspan=2)

p_port_label = tk.Label(start_frame, text='Enter peer port')
p_port_label.grid(row=1, column=0, padx=25, pady=5, sticky=tk.E)

p_port_entry = tk.Entry(start_frame, textvariable=s_port)
p_port_entry.grid(row=1, column=1, padx=25, pady=5, sticky=tk.W)

p_port_button = tk.Button(start_frame, text='Start',
                          command=lambda: start_mys(p_port))
p_port_button.grid(row=2, column=0, padx=25, pady=5, columnspan=2)

# ====== Working Frame ======
p_port_label = tk.Label(sec_frame, font=('', 15))
p_port_label.grid(row=0, column=0, padx=5, pady=5)

t_or_p_frame = tk.LabelFrame(sec_frame, text='Program', height=100,
                             width=100, relief='groove')
t_or_p_frame.grid(row=1, column=0, padx=5, pady=5)
t_or_p_frame.grid_propagate(0)

trck_frame = tk.Frame(sec_frame, bg=trck_color, height=350, width=450)
peer_frame = tk.Frame(sec_frame, bg=peer_color, height=350, width=450)
trck_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky='nsew')
peer_frame.grid(row=0, column=1, rowspan=2, padx=5, pady=5, sticky='nsew')
trck_frame.grid_propagate(0)
peer_frame.grid_propagate(0)

# sec_frame.rowconfigure(0, weight=1)
# sec_frame.rowconfigure(1, weight=2)
# sec_frame.columnconfigure(0, weight=1)
# sec_frame.columnconfigure(1, weight=2)

trck_button = tk.Radiobutton(t_or_p_frame, text='Tracker', value=0,
                             command=check_state, variable=i)
peer_button = tk.Radiobutton(t_or_p_frame, text='Peer', value=1,
                             command=check_state, variable=i)
trck_button.grid(row=0, column=0)
peer_button.grid(row=1, column=0)

# tk.Label(trck_frame, text='Tracker').grid()
# tk.Label(peer_frame, text='Peer').grid()

# ====== Tracker Connect Frame ======
trck_frame_1 = tk.Frame(trck_frame, bg='green', height=150, width=300)
trck_frame_1.grid(row=0, column=0)
trck_frame_1.grid_propagate(0)

trck_label = tk.Label(trck_frame_1, text='Enter tracker port')
trck_entry = tk.Entry(trck_frame_1, textvariable=t_port)
connect_button = tk.Button(trck_frame_1, text='Connect',
                           command=lambda: check_trck_port(t_port))
trck_label.grid(row=0, column=0, padx=5, pady=5)
trck_entry.grid(row=0, column=1, padx=5, pady=5)
connect_button.grid(row=1, column=0, columnspan=2, padx=5, pady=5)

# ====== Tracker Login or Register Frame ======
trck_frame_2 = tk.Frame(trck_frame, bg='yellow', height=150, width=300)
trck_frame_2.grid(row=0, column=0)
trck_frame_2.grid_propagate(0)

login_button = tk.Button(trck_frame_2, text='Login',
                         command=lambda: change_frame(trck_frame_3))
reg_button = tk.Button(trck_frame_2, text='Register',
                       command=lambda: change_frame(trck_frame_4))
login_button.grid(row=0, column=0, padx=50, pady=50)
reg_button.grid(row=0, column=1, padx=50, pady=50)

# ====== Tracker Login Frame ======
trck_frame_3 = tk.Frame(trck_frame, bg='pink', height=150, width=300)
trck_frame_3.grid(row=0, column=0)
trck_frame_3.grid_propagate(0)

uid_label = tk.Label(trck_frame_3, text='Enter your uid')
pwd_label = tk.Label(trck_frame_3, text='Enter your password')
uid_label.grid(row=0, column=0, padx=5, pady=5)
pwd_label.grid(row=1, column=0, padx=5, pady=5)

uid_entry = tk.Entry(trck_frame_3, textvariable=uid)
pwd_entry = tk.Entry(trck_frame_3, textvariable=pwd)
uid_entry.grid(row=0, column=1, padx=5, pady=5)
pwd_entry.grid(row=1, column=1, padx=5, pady=5)

back_button = tk.Button(trck_frame_3, text='Back',
                        command=lambda: change_frame(trck_frame_2))
login_button = tk.Button(trck_frame_3, text='Submit', command=login)
back_button.grid(row=2, column=0, padx=5, pady=5)
login_button.grid(row=2, column=1, padx=5, pady=5)

# ====== Tracker Register Frame ======
trck_frame_4 = tk.Frame(trck_frame, bg='orange', height=150, width=300)
trck_frame_4.grid(row=0, column=0)
trck_frame_4.grid_propagate(0)

name_label = tk.Label(trck_frame_4, text='Enter your name')
uid_label = tk.Label(trck_frame_4, text='Enter your uid')
pwd_label = tk.Label(trck_frame_4, text='Enter your password')
name_label.grid(row=0, column=0, padx=5, pady=5)
uid_label.grid(row=1, column=0, padx=5, pady=5)
pwd_label.grid(row=2, column=0, padx=5, pady=5)

name_entry = tk.Entry(trck_frame_4, textvariable=name)
uid_entry = tk.Entry(trck_frame_4, textvariable=uid)
pwd_entry = tk.Entry(trck_frame_4, textvariable=pwd)
name_entry.grid(row=0, column=1, padx=5, pady=5)
uid_entry.grid(row=1, column=1, padx=5, pady=5)
pwd_entry.grid(row=2, column=1, padx=5, pady=5)

back_button = tk.Button(trck_frame_4, text='Back',
                        command=lambda: change_frame(trck_frame_2))
login_button = tk.Button(trck_frame_4, text='Submit', command=register)
back_button.grid(row=3, column=0, padx=5, pady=5)
login_button.grid(row=3, column=1, padx=5, pady=5)

# ====== Tracker Send and Get File Frame ======
trck_frame_5 = tk.Frame(trck_frame, bg='brown', height=150, width=300)
trck_frame_5.grid(row=0, column=0)
trck_frame_5.grid_propagate(0)

send_button = tk.Button(trck_frame_5, text='Send File')
get_button = tk.Button(trck_frame_5, text='Get File')
disconn_button = tk.Button(trck_frame_5, text='Disconnect')
send_button.grid(row=0, column=0, padx=5, pady=5)
get_button.grid(row=0, column=1, padx=5, pady=5)
disconn_button.grid(row=0, column=2, padx=5, pady=5)

change_frame(start_frame)
change_frame(trck_frame_1)

p_port_entry.focus()
wind.bind('<Return>', lambda x: start_mys(s_port))

wind.mainloop()
