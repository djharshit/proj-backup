#!usr/bin/env python3

"""Peer program."""


import socket
import threading
import pickle
import hashlib
import time
from os import path


class FileOp:
    """Class for handling all file related operations.

    This class perform three tasks:
        1. Make file detail in specific format and send it to MyServer class
        2. Send the file to the peer in chunks
        3. Receive the file from the peer

    Attributes:
        fname (str): Name of the file
        size : 512 kb (chunk size)
    """

    whole_file = []

    def __init__(self, fname, conn=None):
        """Init method of FileOp class.

        Args:
            fname (TYPE): Description
        """
        self.fname = fname
        self.conn = conn

    def send_file_detail(self) -> dict:
        """Send the file detail provided by peer to tracker
            in the specified format.

        Returns:
            dict : Dictionary of file block in specified format
        """
        file_block = {}
        no_blocks = 0
        size = 512 * 1024   # 512 kb

        file_block['FileName'] = self.fname
        file_block['FileOwner'] = details[0], details[1]
        file_block['TotalSize'] = path.getsize(f'./p/{self.fname}')
        file_block['SHAofEveryBlock'] = []
        file_block['PeerPorts'] = [s_port]

        with open(f'./p/{self.fname}', 'rb') as f:
            data = f.read(size)
            file_hsh = hashlib.sha1()

            while data:
                no_blocks += 1

                block_hsh = hashlib.sha1(data).hexdigest()
                file_block['SHAofEveryBlock'].append(block_hsh)
                file_hsh.update(data)

                data = f.read(size)

        file_block['SHAofFullFile'] = file_hsh.hexdigest()
        file_block['NoBlocks'] = no_blocks

        return file_block

    def send_file(self, start, end):
        """Divide the file in specified size (chunks).

        Returns:
            generator : Generator of file data (chunks) in bytes
        """
        file_parts = []
        size = 512 * 1024   # 512 kb

        with open(f'./p/{self.fname}', 'rb') as f:
            data = f.read(size)

            while data:
                file_parts.append(data)
                data = f.read(size)

        for i in range(start, end + 1):
            print('Send part', i)
            data = [i, file_parts[i - 1]]
            self.conn.send(pickle.dumps(data))
            time.sleep(0.5)

    @classmethod
    def receive_file(cls, fname, clnt, start, sha_list):
        """Recieve the file in chunks and append it to the new created file.

        Args:
            conn
        """

        size = 513 * 1024   # 512 kb -> file_part | 1 kb -> part_number
        cls.whole_file += [0] * len(sha_list)
        # print(len(cls.whole_file), 105)

        for i, i_hsh in enumerate(sha_list):

            data = clnt.receive_msg(size)
            no, block = pickle.loads(data)

            b_hsh = hashlib.sha1(block).hexdigest()

            if i_hsh == b_hsh:
                print('Receiving', i + start, 'OK')
                cls.whole_file[no - 1] = block
                time.sleep(0.5)
            else:
                print('Corrupted', i + start)

        # if cls.whole_file.count(0) != 0:
        #     print(cls.whole_file.index(0)+1, 'Error')
        # else:
        #     print('All OK')

        time.sleep(0.5)
        with open(f'./p/{fname}', 'wb+') as f:
            for i in cls.whole_file:
                if type(i) is int:
                    print(cls.whole_file.index(i)+1, '====== Corrupted ======')
                    continue
                f.write(i)

        clnt.send_msg(b'bye')
        clnt.clnt.close()


class MyServer(FileOp):
    """Our peer server.

    This class perform three tasks:
        1. Accept connections from other peers
        2. Receive messages from peers
        3. Send the file in chunks to the peer

    Attributes:
        srvr : Server socket object
        port (int): Peer port (Server port)
    """

    def __init__(self, port: int):
        """Init method of MyServer class.

        Args:
            port (int): Description
        """
        self.host = '127.0.0.1'
        self.port = port

        self.srvr = socket.socket()
        self.srvr.bind((self.host, self.port))
        self.srvr.listen(5)
        print('[+] Peer started on', self.port)

    def accept_conn(self):
        """Accept clients connections request."""
        while True:
            conn, addr = self.srvr.accept()

            p2p_srvr_port = conn.recv(1024).decode()
            print('[+] New Peer', p2p_srvr_port)

            s = threading.Thread(target=self.receive_msg,
                                 args=[conn, p2p_srvr_port])
            s.start()

    def receive_msg(self, conn, addr) -> None:
        """Receive messages from the other peers.

        Args:
            conn : Socket connection object
            addr : Peer port no
        """
        while True:
            msg = conn.recv(1024).decode()
            print(addr, '->', msg)

            if msg == 'bye':
                print(addr, 'disconnected')
                conn.close()
                break

            elif msg.startswith('sendfile'):
                fname, f, l = msg.split()[1:]
                f, l = int(f), int(l)

                super().__init__(fname, conn)
                self.send_file(f, l)


class MyClient(FileOp):
    """Client class: handling clients objects.

    This class perform four tasks:
        1. Try to connect to the server
        2. Send messages to and receive messages from tracker
        3. Send messages to the peer
        4. Receive file in chunks from the peer

    Attributes:
        clnt : Client socket object
        port (int): Server port number
    """

    def __init__(self, port):
        """Init method of MyClient class.

        Args:
            port (TYPE): Description
        """
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
        except ConnectionRefusedError:
            return False
        else:
            return True

    def send_msg(self, bin_msg: bytes) -> None:
        """Send the message (bytes) to the server.

        Args:
            bin_msg (bytes): Message in bytes
        """
        self.clnt.send(bin_msg)

    def receive_msg(self, size: int=1024) -> bytes:
        """Receive the message (bytes) from the server.

        Optional Args:
            size (int): Buffer size of receiving message

        Returns:
            bytes: Message in bytes
        """
        return self.clnt.recv(size)


def tracker() -> bool:
    """Handling tracker client object.

    Returns:
        bool: True if connected with the tracker, otherwise False
    """
    global trck_clnt

    t_port = 3030  # int(input('Enter tracker port:\n'))
    trck_clnt = MyClient(t_port)

    if trck_clnt.server_connect():
        print('[+] Connected to', t_port)
        trck_clnt.send_msg(str(s_port).encode())
        return True

    else:
        print('Tracker not found')
        return False


def options():
    """List of options."""
    print('''List of options:-
            connecttracker (t)
            register (r)
            login (l)
            mydetail (m)
            sendfile (s)
            getfiles (g)
            downloadfile (d)
            quittracker (k)
            quit (q)
            help (h)
            ''')

# __main__

details = []
file_detl = None
is_trck = False
trck_clnt = None
peers = {}


# Server object
s_port = int(input('Enter your port:\n'))
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

        trck_msg = input('Enter details: uid name password:\n')
        trck_clnt.send_msg(trck_msg.encode())

        trck_msg = trck_clnt.receive_msg().decode()
        print(trck_msg)

    elif msg == 'l' and is_trck:
        trck_clnt.send_msg(b'login')

        trck_msg = input('Enter details: uid password:\n')
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

        fname = input('Enter file name:\n')

        fileop = FileOp(fname)
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

        name = input('Enter file name:\n')

        if name in d:

            trck_clnt.send_msg(name.encode())

            data_length = trck_clnt.receive_msg().decode()
            data = trck_clnt.clnt.recv(int(data_length))

            file_detl = pickle.loads(data)

            for i, j in file_detl.items():
                if i in ['SHAofEveryBlock', 'SHAofFullFile']:
                    continue
                print(i, j)

        else:
            trck_clnt.send_msg(b'-1')
            print('Wrong file name')

    elif msg == 'k' and is_trck:
        trck_clnt.send_msg(b'bye')
        trck_clnt.clnt.close()

        print('[+] Disconnected from tracker')

        details.clear()
        is_trck = False
        del trck_clnt

    # Peer chatting
    elif msg == 'd':

        if file_detl is None:
            print('There is no file detail')
            continue

        for p2p_clnt_port in file_detl['PeerPorts']:
            p2p_clnt = MyClient(p2p_clnt_port)

            if p2p_clnt.server_connect():
                print('[+] Connected to', p2p_clnt_port)

                peers[p2p_clnt_port] = p2p_clnt
                p2p_clnt.send_msg(str(s_port).encode())
            else:
                print(p2p_clnt_port, 'is sleeping')

        peer_no = len(peers)

        if peer_no == 0:
            print('No peer available')
            continue

        if file_detl['NoBlocks'] % peer_no == 0:
            each_parts = file_detl['NoBlocks'] // peer_no
        else:
            each_parts = (file_detl['NoBlocks'] // peer_no) + 1

        time.sleep(0.5)
        fname = file_detl['FileName']
        f, l = 1, each_parts
        last = left = file_detl['NoBlocks']
        thrds = []

        for k, clnt in peers.items():
            left -= each_parts

            clnt.send_msg(f'sendfile {fname} {f} {l}'.encode())

            t = threading.Thread(target=clnt.receive_file,
                                 args=[fname, clnt, f,
                                       file_detl['SHAofEveryBlock'][f-1:l]])
            thrds.append(t)
            t.start()

            f += each_parts
            if left >= each_parts:
                l += each_parts
            else:
                l = last

        for i in thrds:
            i.join()

        print(fname, 'fully received')
        trck_clnt.send_msg(b'more')
        trck_clnt.send_msg(fname.encode())

    elif msg == 'h':
        options()

    elif msg == 'q':
        if not is_trck:
            print('[+] Bye')
            break
        else:
            print('Not allowed to quit')

    else:
        print('Something went wrong')

mys.srvr.close()
