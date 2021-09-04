"""Peer program

Attributes:
    conn_d (dict): Description
    frmt (str): Description
    is_trck (bool): Description
    msg (TYPE): Description
    mys (TYPE): Description
    s_port (TYPE): Description
    srvr_thrd (TYPE): Description
"""


import socket
import threading
import pickle
import hashlib


class MyServer:
    """Our peer server

    This class has three functions:
        1. Accept connections from peer client
        2. Receive msg from the peer client
        3. Send file to the peer client

    This class perform three task:
        1. Accept connections from other peers
        2. Receive msg from the peer
        3. Send file to the peer

    Attributes:
        srvr : Server socket object
        port (int): Peer port (Server port)
    """

    def __init__(self, port: int):
        self.host = '127.0.0.1'
        self.port = port

        self.srvr = socket.socket()
        self.srvr.bind((self.host, self.port))
        self.srvr.listen(5)
        print('[+] Peer started on', self.port)

    def accept_conn(self) -> None:
        """Accept clients connections request
        """
        while True:
            conn, addr = self.srvr.accept()

            p2p_srvr_port = conn.recv(1024).decode()
            print('[+] New Peer', p2p_srvr_port)

            s = threading.Thread(target=self.receive_msg, args=[conn, p2p_srvr_port])
            s.start()

    def receive_msg(self, conn, addr) -> bytes:
        """Receiving messages from other peers.

        Args:
            conn : Socket connection object
            addr :
        """
        while True:
            msg = conn.recv(1024).decode()
            print(addr, '->', msg)

            if msg.split()[0] == 'sendfile':
                self.send_file(conn, msg.split()[1])

    def send_file(self, conn, fname):
        """Send the file to the peer

        Args:
            fname (str): Name of the the file
        """
        fileop = FileOp(fname)

        file_lst = fileop.send_file()

        if file_lst:
            conn.send(b'OK')

            for i in range(len(file_lst)):
                print('Send', i+1)
                conn.send(file_lst[i])

            print('All send')

        else:
            conn.send(b'File not found')

        del fileop


class MyClient:
    """Client class: handling clients objects

    This class has three functions:
        1. Connect to the tracker and peer servers with provided port
        2. Send msg to the servers
        3. Receive msg from servers

    This class perform three tasks:
        1. Send msg to and receive msg from tracker
        2. Send msg to the peer
        3. Receive file from the peer

    Attributes:
        clnt : Client object
        port (int): Server port number
    """

    def __init__(self, port):
        self.clnt = socket.socket()
        self.port = port
        self.host = '127.0.0.1'

    def server_connect(self) -> bool:
        """Connect to the given server port.

        Returns:
            bool : True if server accepts connection, otherwise False
        """
        try:
            self.clnt.connect((self.host, self.port))
        except:
            return False
        else:
            return True

    def send_msg(self, bin_msg: bytes) -> None:
        """Send the message (bytes) to the server.

        Args:
            bin_msg (bytes): Message in bytes object
        """
        self.clnt.send(bin_msg)

    def receive_msg(self, size: int=1024) -> bytes:
        """Receive the message (bytes) from the server.

        Optional Args:
            size (int): Buffer size of receiving message

        Returns:
            bytes object
        """
        return self.clnt.recv(size)


class FileOp:
    def __init__(self, fname):
        self.fname = fname
        self.size = 512 * 1024   # 512 kb

    def file_size(self) -> int:
        """Calculate the size of the file

        Returns:
            int: Size of file in bytes
        """
        with open(f'./send/{self.fname}', 'rb') as f:
            return len(f.read())

    def send_file_detail(self) -> dict:
        """Send the file detail provided by peer to tracker in the
        specified format.

        Returns:
            dict : Dictionary of file block in specified format

        """
        file_block = {}
        no_blocks = 0
        t = []

        file_block['FileName'] = self.fname
        file_block['FileOwner'] = details[0], details[1]
        file_block['TotalSize'] = self.file_size()
        file_block['SHAofEveryBlock'] = []

        with open(f'./send/{self.fname}', 'rb') as f:
            data = f.read(self.size)
            file_hsh = hashlib.sha1()

            while data:
                t.append(data)
                no_blocks += 1

                block_hsh = hashlib.sha1(data).hexdigest()
                file_block['SHAofEveryBlock'].append(block_hsh)
                file_hsh.update(data)

                data = f.read(self.size)

        file_block['SHAofFullFile'] = file_hsh.hexdigest()
        file_block['NoBlocks'] = no_blocks

        return file_block

    def send_file(self) -> list:
        """Divide the file in specified parts.

        Returns:
            list : List of file parts in bytes
        """
        file_parts = []

        try:
            with open(f'./send/{self.fname}', 'rb') as f:
                data = f.read(self.size)

                while data:
                    file_parts.append(data)

                    data = f.read(self.size)

        except FileNotFoundError:
            return False

        else:
            return file_parts

    def file_receive(self, data: bytes):
        """Recieve the file in parts and append it to the new created file

        Args:
            data (bytes): Description
        """
        r = 1
        with open(f'./receive/{self.fname}', 'ab+') as f:
            b = f.write(data)
            print('Received', r , 'size', b)


# Tracker client object
def tracker():
    global trck_clnt

    t_port = 3030   # int(input('Enter tracker port:'))
    trck_clnt = MyClient(t_port)

    if trck_clnt.server_connect():
        print('[+] Connected to', t_port)
        trck_clnt.send_msg(str(s_port).encode())
        return True

    else:
        print('Tracker not found')


# List of options
def options():
    print('''List of options:-
            connecttracker (t)
            register (r)
            login (l)
            mydetail (m)
            sendfile (s)
            getfiles (g)
            connectwithpeer (c)
            chatwithpeer (p)
            help (h)
            quittracker (q)
            quit(e)
            ''')

# __main__

details = []
frmt = 'utf-8'
is_trck = False
trck_clnt = None
peers = {}

# Server object
s_port = int(input('Enter your port:'))
mys = MyServer(s_port)

srvr_thrd = threading.Thread(target=mys.accept_conn)
srvr_thrd.start()

# User input
while True:

    msg = input('Enter option or help(h)\n').lower()

    # Tracker chatting
    if msg == 't' and not is_trck:
        is_trck = tracker()

    elif msg == 'r' and is_trck:
        trck_clnt.send_msg(b'register')

        trck_msg = input('Enter details: uid name password: ')
        trck_clnt.send_msg(trck_msg.encode())

        trck_msg = trck_clnt.receive_msg().decode()
        print(trck_msg)

    elif msg == 'l' and is_trck:
        trck_clnt.send_msg(b'login')

        trck_msg = input('Enter details: uid password: ')
        trck_clnt.send_msg(trck_msg.encode())

        data = trck_clnt.receive_msg()

        trck_msg, *details = pickle.loads(data)
        print(trck_msg)

    elif msg == 'm' and is_trck:
        if details:
            print(details)

        else:
            print('Login first')

    elif msg == 's' and details:
        trck_clnt.send_msg(b'sendfile')

        fpath = input('Enter file name:')

        fileop = FileOp(fpath)
        file_block = fileop.send_file_detail()

        data = pickle.dumps(file_block)
        data_length = str(len(data))

        trck_clnt.send_msg(data_length.encode())
        trck_clnt.send_msg(data)

        trck_msg = trck_clnt.receive_msg().decode()
        print(trck_msg)

        del fileop

    elif msg == 'g' and details:
        trck_clnt.send_msg(b'getfiles')

        data = trck_clnt.receive_msg()
        d = pickle.loads(data)

        for i, j in d.items():
            print(i, j)

        name = input('Enter file name:')

        if name in d:

            trck_clnt.send_msg(name.encode())

            data_length = trck_clnt.receive_msg().decode()
            data = trck_clnt.clnt.recv(int(data_length))

            d = pickle.loads(data)
            _d = d.copy()
            del _d['SHAofEveryBlock']
            for i, j in _d.items():
                print(i, j)

        else:
            trck_clnt.send_msg(b'-1')
            print('Wrong file name')

    elif msg == 'q' and is_trck:
        trck_clnt.send_msg(b'bye')
        trck_clnt.clnt.close()

        print('[+] Disconnected from tracker')

        details.clear()
        is_trck = False
        del trck_clnt

    # Peer chatting
    elif msg == 'c':
        p2p_clnt_port = int(input('Enter peer port: '))

        p2p_clnt = MyClient(p2p_clnt_port)

        if p2p_clnt.server_connect():
            print('[+] Connected to', p2p_clnt_port)

            peers[p2p_clnt_port] = p2p_clnt
            p2p_clnt.send_msg(str(s_port).encode())

        else:
            print(p2p_clnt_port, 'is sleeping')

    elif msg == 'p':
        p2p_lst = input('Enter peerport message: ').split()

        p2p_clnt_port, p2p_msg = int(p2p_lst[0]), p2p_lst[1:]

        p2p_msg = ' '.join(p2p_msg)

        if p2p_clnt_port in peers:
            p2p_clnt = peers[p2p_clnt_port]
            p2p_clnt.send_msg(p2p_msg.encode())

            if p2p_lst[1] == 'sendfile':
                msg = p2p_clnt.receive_msg().decode()

                if msg == 'OK':
                    fileop = FileOp(p2p_lst[2])

                    for i in range(d['NoBlocks']):
                        print('Receive', i+1)
                        fileop.file_receive(p2p_clnt.receive_msg(512 * 1024))

                    print(p2p_lst[2], 'received')

                else:
                    print(msg)

        else:
            print('Peer not found, connect to it')

    elif msg == 'h':
        options()

    elif msg == 'e':
        print('[+] Bye')
        break

    else:
        print('Something went wrong')

mys.srvr.close()
