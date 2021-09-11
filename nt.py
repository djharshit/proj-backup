"""
Tracker program to and save the details of peers and files given
by them.
"""
import socket
import threading
import json
import logging
import hashlib
import pickle


class UsersDetails():
    """Class for handling user login and register.

    This class perform two tasks:
        1. Register the new peer and act accordingly
        2. Login the existing peer, if success then update the
           new port of the user

    Attributes:
        p_port (int): Port of the peer from which this class is called
    """

    def __init__(self, p_port: int):
        self.p_port = p_port

    def peer_register(self, dtls: list) -> str:
        """Registration of the peer for first time and
           Save details in details file

        Args:
            dtls (list): ['Uid', 'Name', 'Password']

        Returns:
            msg: Register message
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
                         password=pwd, port=self.p_port)

                usrs['users'].append(d)

                f.truncate(0)
                f.seek(0)
                json.dump(usrs, f, indent=4)

                m = 'User details saved'
                logging.debug(f'Peer {self.p_port} -> \
                                {dtls[0]} {dtls[1]} registerd')

        details_lock.release()
        return m

    def peer_login(self, dtls: list) -> str:
        """Login of peer using his details and
           updating its new port in both files.

        Args:
            dtls (list): ['Uid', 'Password']

        Returns:
            msg: Login message
        """
        details_lock.acquire()

        with open('details.json', 'r+') as f:
            users = json.load(f)

            for i in users['users']:
                if int(dtls[0]) == i['uid']:
                    pwd = hashlib.sha256(dtls[1].encode()).hexdigest()
                    # print(pwd)
                    if pwd == i['password']:
                        logging.debug(f'Peer {self.p_port} -> \
                            {dtls[0]} logged in')

                        old_port = i['port']
                        i['port'] = self.p_port
                        m = 'Login successful', i['uid'], i['name'], i['port']

                        # Update the port no if login success in details
                        f.truncate(0)
                        f.seek(0)
                        json.dump(users, f, indent=4)
                        print(97, old_port)
                        self.update_ports(old_port)
                        print(99, old_port)
                        break

                    else:
                        m = 'Wrong password',
                        break
            else:
                m = 'Uid not found',

        details_lock.release()
        return m

    def update_ports(self, old_port: int) -> None:
        """Update the port no of the file it has send in files.

        Args:
            old_port (int): Old port of the peer
        """
        files_lock.acquire()
        print(118, old_port)
        with open('files.json', 'r+') as f:
            files = json.load(f)
            print(121, old_port)
            for j in files['files']:
                print(123, old_port)
                if old_port in j['PeerPorts']:
                    print(125, old_port)
                    j['PeerPorts'].remove(old_port)
                    j['PeerPorts'].append(self.p_port)
                    print(125, j['PeerPorts'])

            f.truncate(0)
            f.seek(0)
            json.dump(files, f, indent=4)

        files_lock.release()


class FileOperation():
    """Class for handling all file related operations.

    This class perform four tasks:
        1. Register a new file in the files
        2. Show only name and size of all files to the peer
        3. Return all details of a file to the peer
        4. Update the current PeerPorts list of the file

    Attributes:
        p_port (int): Port of the peer from which this class is called
        uid (int): Uid of the peer from which this class is called
    """

    def __init__(self, p_port: int, uid: int):
        self.p_port = p_port
        self.uid = uid

    def file_entry(self, file_block: dict):
        """Save file details provided by peer in the files.

        Args:
            file_block (dict): Dictionary of file details

        """
        files_lock.acquire()

        logging.debug(f'Peer {self.p_port} Uid {self.uid} \
                        Savefile name {file_block["FileName"]}')

        with open('files.json', 'r+') as f:
            files = json.load(f)

            # file_block.append()

            files['files'].append(file_block)

            f.truncate(0)
            f.seek(0)
            json.dump(files, f, indent=4)

        files_lock.release()
        return 'File details saved'

    def file_show(self):
        """Show the names and size of all files so that the peer can
           choose one from it.
        """
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

    def file_detail(self, name: str) -> dict:
        """Give all details of the file to the peer

        Args:
            name (str): Name of the file

        Returns:
            dict: File details dictionary
        """
        files_lock.acquire()

        logging.debug(f'Peer {self.p_port} Uid {self.uid} \
                        Ask for file {name} detail')

        with open('files.json') as f:
            files = json.load(f)

            for i in files['files']:
                if i['FileName'] == name:
                    break

        files_lock.release()
        return i

    def update_peer(self, fname: str) -> None:
        """Update the file PeerPorts to the port of the peer.

        Args:
            fname (str): File name to which port be added
        """
        files_lock.acquire()

        with open('files.json', 'r+') as f:
            files = json.load(f)

            for i in files['files']:
                if i['FileName'] == fname:
                    i['PeerPorts'].append(self.p_port)

                    f.truncate(0)
                    f.seek(0)
                    json.dump(files, f, indent=4)

                    break
        files_lock.release()

    def delete_peer(self):
        files_lock.acquire()

        with open('files.json', 'r+') as f:
            files = json.load(f)

            for i in files['files']:
                if self.p_port in i['PeerPorts']:
                    i['PeerPorts'].remove(self.p_port)

            f.truncate(0)
            f.seek(0)
            json.dump(files, f, indent=4)

        files_lock.release()


class MyPeer:
    """Class for handling the peer messages and act accordingly.

    This class perform one task:
        1. Chat with the particular peer and act accordingly to
           the condition

    Attributes:
        conn (obj): Connection object of the peer client
        p_port (int): Port of the peer from which it is chatting
    """

    def __init__(self, conn, p_port):
        self.conn = conn
        self.p_port = p_port
        self.detail = []
        self.uid = None

    def peer_chat(self):
        """Chat with the particular peer and act accordingly to
           the condition.
        """
        while True:
            msg = self.conn.recv(1024).decode()
            print(f'Peer {self.p_port} -> {msg}')

            logging.info(f'Peer {self.p_port} -> {msg}')

            if msg == 'register':
                msg = self.conn.recv(1024).decode()

                print(self.p_port, '->', msg)
                msg = msg.split()

                user = UsersDetails(self.p_port)
                msg = user.peer_register(msg)
                self.conn.send(msg.encode())

            elif msg == 'login':
                msg = self.conn.recv(1024).decode()

                print(self.p_port, '->', msg)
                msg = msg.split()

                user = UsersDetails(self.p_port)
                msg = user.peer_login(msg)

                data = pickle.dumps(msg)
                self.conn.send(data)

                msg, *(self.detail) = msg

                if self.detail != []:
                    self.uid = self.detail[0]

            elif msg == 'sendfile':
                data_length = self.conn.recv(1024).decode()
                data = self.conn.recv(int(data_length))

                file_block = pickle.loads(data)

                fileop = FileOperation(self.p_port, self.uid)
                msg = fileop.file_entry(file_block)

                self.conn.send(msg.encode())

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

            elif msg == 'more':
                fname = self.conn.recv(1024).decode()

                fileop = FileOperation(self.p_port, self.uid)
                fileop.update_peer(fname)

            elif msg == 'bye':
                # fileop = FileOperation(self.p_port, self.uid)
                # fileop.delete_peer()

                print('[+] Disconnected from peer', self.p_port)
                logging.warning(f'Peer {self.p_port} -> disconnected')
                self.conn.close()
                break

            else:
                self.conn.send(b'Wrong input')

# ====== Main ======

# Log file configurations
log_frmt = '{asctime} | {levelname} | {lineno} | {threadName} |{message}'
logging.basicConfig(filename='tracker.log', level=logging.DEBUG, style='{',
                    format=log_frmt)

# Setting Locks for the files
details_lock = threading.Lock()
files_lock = threading.Lock()


def main():
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

        myp = MyPeer(conn, int(p_port))

        t = threading.Thread(target=myp.peer_chat)
        logging.info(f'New Peer {p_port} with thread {t.name}')
        t.start()

    s.close()

if __name__ == '__main__':
    main()
