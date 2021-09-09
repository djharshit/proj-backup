"""Tracker program to and save the details of peers and files given
by them.
"""
import socket
import threading
import json
import logging
import hashlib
import pickle
import os


class UsersDetails():

    """
    Summary.
    Ab kya btaye
    """

    def __init__(self, p_port):
        self.p_port = p_port

    def peer_register(self, dtls):
        """Registration of the peer for first time and
            Save details in detail.json.

        Args:
            dtls (TYPE): Description
        """
        details_lock.acquire()

        with open('details.json', 'r+') as f:
            usrs = json.load(f)

            for i in usrs['users']:
                if int(dtls[0]) == i['uid']:
                    m = 'Uid existed'
                    break
            else:
                pwd = hashlib.sha256(dtls[2].encode()).hexdigest()
                # print(pwd)
                d = dict(uid=int(dtls[0]), name=dtls[1],
                         password=pwd, port=int(dtls[3]))

                usrs['users'].append(d)

                f.truncate(0)
                f.seek(0)
                json.dump(usrs, f, indent=4)

                m = 'User details saved'
                logging.debug(f'Peer {self.p_port} -> \
                                {dtls[0]} {dtls[1]} registerd')

        details_lock.release()
        return m

    def peer_login(self, dtls):
        """Login of peer using his details and taking further actions.

        Args:
            dtls (TYPE): Description

        Returns:
            TYPE: Description
        """
        details_lock.acquire()

        with open('details.json', 'r+') as f:
            usrs = json.load(f)

            for i in usrs['users']:
                if int(dtls[0]) == i['uid']:
                    pwd = hashlib.sha256(dtls[1].encode()).hexdigest()
                    # print(pwd)
                    if pwd == i['password']:
                        i['port'] = int(dtls[2])
                        m = 'Login successful', i['uid'], i['name'], i['port']

                        f.seek(0)
                        json.dump(usrs, f, indent=4)
                        f.truncate()

                        logging.debug(f'Peer {self.p_port} -> \
                                        {dtls[0]} logged in')

                        break

                    else:
                        m = 'Wrong password',
                        break
            else:
                m = 'Uid not found',

        details_lock.release()
        return m


class FileOperation():

    """Summary.

    Attributes:
        p_port (TYPE): Description
    """

    def __init__(self, p_port, uid):
        self.p_port = p_port
        self.uid = uid

    # Save file details provided by peer in the files.json
    def file_entry(self, file_block):
        files_lock.acquire()

        logging.debug(f'Peer {self.p_port} Uid {self.uid} \
                        Savefile name {file_block["FileName"]}')

        with open('files.json', 'r+') as f:
            files = json.load(f)

            files['files'].append(file_block)

            f.truncate(0)
            f.seek(0)
            json.dump(files, f, indent=4)

        files_lock.release()
        return 'File details saved'

    def file_show(self):
        files_lock.acquire()

        logging.debug(f'Peer {self.p_port} Uid {self.uid} Ask for files')

        d = {}
        with open('files.json') as f:
            files = json.load(f)
            for i in files['files']:
                fname, fsize = i['FileName'], i['TotalSize']
                d[fname] = fsize

        files_lock.release()
        return d

    def file_detail(self, name):
        files_lock.acquire()

        logging.debug(f'Peer {self.p_port} Uid {self.uid} \
                        Ask for file {name} detail')

        with open('details.json') as df, open('files.json') as ff:
            details = json.load(df)
            files = json.load(ff)

            for i in files['files']:
                if i['FileName'] == name:
                    break

            for j in details['users']:
                # print(j)
                if j['uid'] == i['FileOwner'][0]:
                    # print(j['uid'])
                    i['PeerPort'] = j['port']

        files_lock.release()
        return i


class MyPeer:
    """Peer class

    Attributes:
        conn (TYPE): Description
        detail (list): Description
        p_port (TYPE): Description
    """

    def __init__(self, conn, p_port):
        self.conn = conn
        self.p_port = p_port
        self.detail = []
        self.uid = None

    def peer_chat(self):
        while True:
            msg = self.conn.recv(1024).decode()
            print(f'Peer {self.p_port} -> {msg}')

            logging.info(f'Peer {self.p_port} -> {msg}')

            if msg == 'register':
                msg = self.conn.recv(1024).decode()

                print(self.p_port, '->', msg)
                msg = msg.split() + [self.p_port]

                user = UsersDetails(self.p_port)
                msg = user.peer_register(msg)
                self.conn.send(msg.encode())

                del user

            elif msg == 'login':
                msg = self.conn.recv(1024).decode()

                print(self.p_port, '->', msg)
                msg = msg.split() + [self.p_port]

                user = UsersDetails(self.p_port)
                msg = user.peer_login(msg)

                data = pickle.dumps(msg)
                self.conn.send(data)

                msg, *(self.detail) = msg

                if self.detail != []:
                    self.uid = self.detail[0]

                del user

            elif msg == 'sendfile':
                data_length = self.conn.recv(1024).decode()
                data = self.conn.recv(int(data_length))

                file_block = pickle.loads(data)

                fileop = FileOperation(self.p_port, self.uid)
                msg = fileop.file_entry(file_block)

                self.conn.send(msg.encode())

                del fileop

            elif msg == 'getfiles':
                fileop = FileOperation(self.p_port, self.uid)

                d = fileop.file_show()
                data = pickle.dumps(d)
                self.conn.send(data)

                name = self.conn.recv(1024).decode()

                if name != '-1':
                    d = fileop.file_detail(name)

                    data = pickle.dumps(d)
                    data_length = str(len(data))

                    self.conn.send(data_length.encode())
                    self.conn.send(data)

                del fileop

            elif msg == 'bye':
                print('[+] Disconnected from peer', self.p_port)
                logging.warning(f'Peer {self.p_port} -> disconnected')
                self.conn.close()
                break

            else:
                self.conn.send(b'Wrong input')


# Log file configurations
log_frmt = '{asctime} | {levelname} | {lineno} | {threadName} |{message}'
logging.basicConfig(filename='tracker.log', level=logging.DEBUG, style='{',
                    format=log_frmt)

# Setting Locks for the files
details_lock = threading.Lock()
files_lock = threading.Lock()

t_port = 3030  # int(input('Enter tracker port:'))
s = socket.socket()

host = '127.0.0.1'  # socket.gethostbyname(comp_nme)
s.bind((host, t_port))
s.listen(10)

print('[+] Tracker started on', t_port)
logging.warning(f'Tracker started on {t_port}')

while True:
    conn, addr = s.accept()
    s.settimeout(None)
    p_port = conn.recv(10).decode()
    print('[+] New Peer', p_port)

    myp = MyPeer(conn, p_port)

    t = threading.Thread(target=myp.peer_chat)
    logging.info(f'New Peer {p_port} with thread {t.name}')
    t.start()

s.close()
