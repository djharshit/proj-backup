#!usr/bin/env python3

"""Peer program."""


import socket
import threading
import pickle
import hashlib
import time
from os import path


class MyServer:
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
            print('[+] New Peer', p2p_srvr_port, 47)

            s = threading.Thread(target=self.receive_msg,
                                 args=[conn, p2p_srvr_port])
            s.start()

    def receive_msg(self, conn, addr) -> str:
        """Receive messages from the other peers.

        Args:
            conn : Socket connection object
            addr : Peer port
        """
        while True:
            msg = conn.recv(1024).decode()
            print(63, addr, '->', msg, 63)

            if msg == 'bye':
                print(addr, 'disconnected')
                conn.close()
                break

            elif msg.split()[0] == 'sendfile':
                self.send_file(conn, msg)

    def send_file(self, conn, msg):
        """Send the file in chunks to the peer.

        Args:
            conn : Connection object
            fname (str): Name of the file
        """

        fname, f, l = msg.split()[1:]
        f, l = int(f), int(l)
        # print(fname, f, l, 79)
        # print(type(fname), type(f), type(l))
        fileop = FileOp(fname, conn)
        fileop.send_file(f, l)
        '''
        if file_lst:
            conn.send(b'File Found')

            for i, j in enumerate(file_lst):
                print('Send', i + 1)
                conn.send(j)
                time.sleep(0.5)
            print('All send')

        else:
            conn.send(b'File not found')
        '''
        del fileop


class MyClient:
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
        except:
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

    def __init__(self, fname, conn):
        """Init method of FileOp class.

        Args:
            fname (TYPE): Description
        """
        self.fname = fname
        self.conn = conn
        self.size = 512 * 1024   # 512 kb

    def send_file_detail(self) -> dict:
        """Send the file detail provided by peer to tracker
            in the specified format.

        Returns:
            dict : Dictionary of file block in specified format
        """
        file_block = {}
        no_blocks = 0

        file_block['FileName'] = self.fname
        file_block['FileOwner'] = details[0], details[1]
        file_block['TotalSize'] = path.getsize(f'./p/{self.fname}')
        file_block['SHAofEveryBlock'] = []
        file_block['PeerPorts'] = [s_port]

        with open(f'./p/{self.fname}', 'rb') as f:
            data = f.read(self.size)
            file_hsh = hashlib.sha1()

            while data:
                no_blocks += 1

                block_hsh = hashlib.sha1(data).hexdigest()
                file_block['SHAofEveryBlock'].append(block_hsh)
                file_hsh.update(data)

                data = f.read(self.size)

        file_block['SHAofFullFile'] = file_hsh.hexdigest()
        file_block['NoBlocks'] = no_blocks

        return file_block

    def send_file(self, start, end) -> iter:
        """Divide the file in specified size (chunks).

        Returns:
            generator : Generator of file data (chunks) in bytes
        """
        # print(self.fname, start, end, 219)
        # print(type(self.fname), type(start), type(end))

        file_parts = []
        with open(f'./p/{self.fname}', 'rb') as f:
            data = f.read(self.size)

            while data:
                file_parts.append(data)
                data = f.read(self.size)

        for i in range(start, end+1):
            print('Send part', i)
            # self.conn.send(file_parts[i-1])
            # self.conn.send(str(i).encode())
            data = [i, file_parts[i-1]]
            self.conn.send(pickle.dumps(data))
            time.sleep(0.5)

    def file_receive(self, start, sha_list: list):
        """Recieve the file in chunks and append it to the new created file.

        Args:
            conn
        """
        # print(len(sha_list))
        self.whole_file += [0] * len(sha_list)

        for i, i_hsh in enumerate(sha_list):
            # no = self.conn.receive_msg(1).decode()
            # block = self.conn.receive_msg(512 * 1024) # .decode().split(maxsplit=1)
            # no = self.conn.receive_msg(10).decode()
            # print(no, block)

            data = self.conn.receive_msg(513 * 1024) # .decode().split(maxsplit=1)
            no, block = pickle.loads(data)
            # print(type(no), type(block), 260)

            b_hsh = hashlib.sha1(block).hexdigest()

            if i_hsh == b_hsh:
                print('Receiving', i+start, 'OK')
                self.whole_file[no-1] = block
                time.sleep(0.5)
            else:
                print('Corrupted', i+start)

        # print(len(self.whole_file))
        if 0 in self.whole_file:
            print('====== Yes ======')
        else:
            print('====== No ======')

        with open(f'./p/{self.fname}', 'wb+') as f:
            for i in self.whole_file:
                if type(i) is int:
                    # print(self.whole_file.index(i) , '====== Corrupted ======')
                    continue
                f.write(i)

        print(self.fname, 'Received')

        # self.conn.send_msg(b'bye')
        # self.conn.clnt.close()

        # return True


def tracker() -> bool:
    """Handling tracker client object.

    Returns:
        bool: True is tracker is running, otherwise False
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
            quittracker (k)
            register (r)
            login (l)
            mydetail (m)
            sendfile (s)
            getfiles (g)
            downloadfile (d)
            connectwithpeer (c)
            chatwithpeer (p)
            help (h)
            quitpeer(e)
            quit (q)
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

        fileop = FileOp(fname, None)
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
    elif msg == 'c':
        p2p_clnt_port = int(input('Enter peer port:\n'))

        p2p_clnt = MyClient(p2p_clnt_port)

        if p2p_clnt.server_connect():
            print('[+] Connected to', p2p_clnt_port)

            peers[p2p_clnt_port] = p2p_clnt
            p2p_clnt.send_msg(str(s_port).encode())

        else:
            print(p2p_clnt_port, 'is sleeping')

    elif msg == 'p':
        p2p_lst = input('Enter peerport message:\n').split()

        p2p_clnt_port, p2p_msg = int(p2p_lst[0]), p2p_lst[1:]

        p2p_msg = ' '.join(p2p_msg)

        if p2p_clnt_port in peers:
            p2p_clnt = peers[p2p_clnt_port]

            try:
                p2p_clnt.send_msg(p2p_msg.encode())

                if p2p_lst[1] == 'sendfile':
                    msg = p2p_clnt.receive_msg().decode()

                    if msg == 'File Found':
                        sha_lst = file_detl['SHAofEveryBlock']

                        fileop = FileOp(p2p_lst[2])
                        fileop.file_receive(p2p_clnt, sha_lst)

                        print(p2p_lst[2], 'received')

                        try:
                            trck_clnt.send_msg(b'more')
                            trck_clnt.send_msg(p2p_lst[2].encode())
                        except:
                            print('You are disconnect from tracker')

                    else:
                        print('File not found')
            except:
                print(f'{p2p_clnt_port} closed')
                del peers[p2p_clnt_port]

        else:
            print('Peer not found, connect to it')

    elif msg == 'd':
        # fname = input('Enter file name:\n')

        if file_detl is None:
            print('There is no file detail')

        else:
            for p2p_clnt_port in file_detl['PeerPorts']:
                p2p_clnt = MyClient(p2p_clnt_port)

                if p2p_clnt.server_connect():
                    print('[+] Connected to', p2p_clnt_port)

                    peers[p2p_clnt_port] = p2p_clnt
                    p2p_clnt.send_msg(str(s_port).encode())
                else:
                    print(p2p_clnt_port, 'is sleeping')

            how_many_peer = len(peers)

            if file_detl['NoBlocks'] % how_many_peer == 0:
                parts_from_each_peer = file_detl['NoBlocks'] // how_many_peer
            else:
                parts_from_each_peer = (file_detl['NoBlocks'] // how_many_peer) + 1

            time.sleep(0.5)
            fname = file_detl['FileName']
            f, l = 1, parts_from_each_peer
            left = file_detl['NoBlocks']
            for k, v in peers.items():
                # print(k, f, l)
                v.send_msg(f'sendfile {fname} {f} {l}'.encode())

                fileop = FileOp(fname, v)
                # fileop.file_receive(f, l, file_detl['SHAofEveryBlock'][f-1:l])

                t = threading.Thread(target=fileop.file_receive, args=[f, file_detl['SHAofEveryBlock'][f-1:l]])
                t.start()

                f += parts_from_each_peer
                if left >= parts_from_each_peer:
                    l += parts_from_each_peer
                else:
                    l = file_detl['NoBlocks']

                left -= parts_from_each_peer

            # print(fname, 'Received', 519)
            trck_clnt.send_msg(b'more')
            trck_clnt.send_msg(fname.encode())

    elif msg == 'h':
        options()

    elif msg == 'e':
        p2p_clnt_port = int(input('Enter peer port:\n'))
        if p2p_clnt_port in peers:
            p2p_clnt = peers[p2p_clnt_port]

            p2p_clnt.send_msg(b'bye')
            p2p_clnt.clnt.close()

            del peers[p2p_clnt_port]

        else:
            print('Peer not exist')

    elif msg == 'q':
        if len(peers) == 0 and not is_trck:
            print('[+] Bye')
            break
        else:
            print('Not allowed to quit')

    else:
        print('Something went wrong')

mys.srvr.close()
