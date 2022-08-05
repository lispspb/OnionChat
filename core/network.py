import threading
import time
import sys
import os
import subprocess
import socket

import config
import core.utils
import core.protocol


class Receiver(threading.Thread):
    def __init__(self, conn, is_incoming=False):
        threading.Thread.__init__(self)
        self.conn = conn
        self.is_incoming = is_incoming
        self.socket = conn.socket
        self.running = True
        self.start()

    def run(self):
        read_buffer = ''
        # self.socket.settimeout(5)
        while self.running:
            try:
                recv = self.socket.recv(4096)
                if recv != '':
                    read_buffer = read_buffer + recv
                    temp = read_buffer.split('\n')
                    read_buffer = temp.pop()

                    for line in temp:
                        if self.running:
                            try:
                                # on outgoing connections we do not allow any
                                # incoming messages other than file*
                                # this prevents an attacker from messaging
                                # or sending commands before the handshake is
                                # completed or pong on the wrong connection
                                if self.is_incoming or line[:4] == 'file':
                                    message = core.protocol.protocol_msg_from_line(
                                        self.conn.bl, self.conn, line)
                                    message.execute()
                                else:
                                    # this is an outgoing connection. Incoming protocol messages are ignored
                                    print(f"Received unexpected '{line}' "
                                          f"on outgoing connection to {self.conn.buddy.address}")
                            except:
                                pass
                else:
                    self.running = False
                    self.conn.onReceiverError()

            except socket.timeout:
                self.running = False
                self.conn.onReceiverError()

            except socket.error:
                self.running = False
                self.conn.onReceiverError()


class InConnection:
    def __init__(self, socket, buddy_list):
        self.buddy = None
        self.bl = buddy_list
        self.socket = socket
        self.last_ping_address = ''  # used to detect mass pings with fake addresses
        self.last_ping_cookie = ''  # used to detect pings with fake cookies
        self.last_active = time.time()
        self.started = True
        self.receiver = Receiver(self, True)

    def send(self, text):
        try:
            self.socket.send(text)
        except:
            print('(2) in-connection send error.')
            self.bl.onErrorIn(self)
            self.close()

    def on_receiver_error(self):
        if self.buddy:
            addr = self.buddy.address
        else:
            addr = self.last_ping_address + ' (unverified)'
        print(f'(2) in-connection receive error: {addr}')
        self.bl.onErrorIn(self)
        self.close()

    def close(self):
        print(f'(2) in-connection closing {self.last_ping_address}')

        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            print(f'(3) socket.shutdown() {sys.exc_info()[1]}')
        try:
            self.socket.close()
        except:
            print(f'(3) socket.close() {sys.exc_info()[1]}')

        self.started = False
        if self in self.bl.listener.conns:
            self.bl.listener.conns.remove(self)
        if self.buddy:
            self.buddy.conn_in = None


class OutConnection(threading.Thread):
    def __init__(self, address, buddy_list, buddy):
        threading.Thread.__init__(self)
        self.bl = buddy_list
        self.buddy = buddy
        self.address = address
        self.pong_sent = False
        self.send_buffer = []
        self.running = False
        self.socket = None
        self.receiver = None
        self.start()

    def run(self):
        self.running = True
        try:
            self.socket = socks.socksocket()
            self.socket.setproxy(socks.PROXY_TYPE_SOCKS4,
                                 config.ini['tor']['address'],
                                 config.ini['tor']['socks_port'])
            print(f"(2) trying to connect '{self.address}'")
            self.socket.connect((str(self.address), config.ONIONCHAT_PORT))
            print(f'(2) connected to {self.address}')
            self.bl.onConnected(self)
            self.receiver = Receiver(self, False)  # this Receiver will only accept file* messages
            while self.running:
                while len(self.send_buffer) > 0:
                    text = self.send_buffer.pop(0)
                    try:
                        print(f'(2) {self.address} out-connection sending buffer')
                        self.socket.send(text)
                    except:
                        print('(2) out-connection send error')
                        self.bl.onErrorOut(self)
                        self.close()

                time.sleep(0.2)

        except:
            print(f'(2) out-connection to {self.address} failed: {sys.exc_info()[1]}')
            self.bl.on_error_out(self)
            self.close()

    def send(self, text):
        self.send_buffer.append(text)

    def on_receiver_error(self):
        print('(2) out-connection receiver error')
        self.bl.onErrorOut(self)
        self.close()

    def close(self):
        self.running = False
        self.send_buffer = []
        try:
            self.socket.shutdown(socket.SHUT_RDWR)
        except:
            print(f'(3) socket.shutdown() {sys.exc_info()[1]}')
        try:
            self.socket.close()
        except:
            print(f'(3) socket.close() {sys.exc_info()[1]}')

        if self.buddy:
            self.buddy.conn_out = None
            print(f'(2) out-connection closed ({self.buddy.address})')
        else:
            print(f'(2) out connection without buddy closed')  # happens after remove_buddy()


class Listener(threading.Thread):
    def __init__(self, buddy_list, socket=None):
        threading.Thread.__init__(self)
        self.buddy_list = buddy_list
        self.conns = []
        self.socket = socket
        self.running = False
        self.start()
        self.start_timer()

    def run(self):
        self.running = True
        if not self.socket:
            interface = config.ini['client']['listen_interface']
            port = config.ini['client']['listen_port']
            self.socket = try_bind_port(interface, port)
        self.socket.listen(5)
        while self.running:
            try:
                conn, address = self.socket.accept()
                self.conns.append(InConnection(conn, self.buddy_list))
                print('(2) new incoming connection')
                print(f'(2) have now {len(self.conns)} incoming connections')
            except:
                print('socket listener error!')
                # self.running = False

    def close(self):
        self.running = False
        try:
            print(f'(2) closing listening socket {config.ini["client"]["listen_interface"]}'
                  f':{config.ini["client"]["listen_port"]}.')

            self.socket.close()
            print('(2) success')
        except:
            print('(2) closing socket failed, traceback follows:')

    def start_timer(self):
        self.timer = threading.Timer(30, self.on_timer)
        self.timer.start()

    def on_timer(self):
        for conn in self.conns:
            if time.time() - conn.last_active > config.DEAD_CONNECTION_TIMEOUT:
                if conn.buddy:
                    print(f'(2) conn_in timeout: disconnecting {conn.buddy.address}')
                    conn.buddy.disconnect()
                else:
                    print(f'(2) closing unused in-connection from {conn.last_ping_address}')
                    conn.close()
                if conn in self.conns:
                    self.conns.remove(conn)
                print(f'(2) have now {len(self.conns)} incoming connections')
        self.start_timer()


def try_bind_port(interface, port):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((interface, port))
        s.listen(5)
        return s
    except:
        return False


def start_portable_tor():
    print(f'(1) entering function startPortableTor()')
    global tor_in, tor_out
    global tor_pid
    global tor_proc
    old_dir = os.getcwd()
    print(f'Current working directory is {os.getcwd()}')
    try:
        print(f'Changing working directory...')
        os.chdir(core.utils.get_data_dir())
        os.chdir('Tor')
        print(f'Current working directory is {os.getcwd()}')
        # completely remove all cache files from the previous run
        # for root, dirs, files in os.walk("tor_data", topdown=False):
        #     for name in files:
        #         os.remove(os.path.join(root, name))
        #     for name in dirs:
        #         os.rmdir(os.path.join(root, name))

        # now start tor with the supplied config file
        print(f'Trying to start Tor...')

        if core.utils.is_windows():
            if os.path.exists('tor.exe'):
                # start the process without opening a console window
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= 1  # STARTF_USESHOWWINDOW
                tor_proc = subprocess.Popen("tor.exe -f torrc.txt".split(), startupinfo=startupinfo)
                tor_pid = tor_proc.pid
            else:
                print(f'There is no portable tor.exe')
                tor_pid = False
        else:
            if os.path.exists('tor.sh'):
                # let our shell script start a tor instance
                os.chmod('tor.sh', 0o0700)
                tor_proc = subprocess.Popen('./tor.sh'.split())
                tor_pid = tor_proc.pid
                print(f'Tor pid is {tor_pid}')
            else:
                print(f'There is no Tor starter script (tor.sh)')
                tor_pid = False

        if tor_pid:
            # tor = subprocess.Popen("tor.exe -f torrc.txt".split(), creationflags=0x08000000)
            print(f'(1) successfully started Tor (pid={tor_pid})')

            # we now assume the existence of our hostname file
            # it WILL be created after the first start
            # if not, something must be totally wrong.
            cnt = 0
            found = False
            while cnt <= 10:
                try:
                    print(f'Trying to read hostname file (try {cnt + 1} of 10)')
                    f = open(os.path.join('hidden_service', 'hostname'), 'r')
                    hostname = f.read().rstrip()[:-6]
                    print(f'(1) found hostname: {hostname}')
                    print('(1) writing own_hostname to onionchat.ini')
                    config.ini['client']['hostanme'] = hostname
                    found = True
                    f.close()
                    break
                except (FileNotFoundError, IOError):
                    # We wait 10 seconds for the file to appear
                    time.sleep(1)
                    cnt += 1

            if not found:
                print('Very strange: portable tor started but hostname could not be read')
                print('Using section [tor], not [tor_portable]')
            else:
                # in portable mode we run Tor on some non-standard ports:
                # so we switch to the other set_option of config-options
                print('Switching active config section from [tor] to [tor_portable]')
                TOR_CONFIG = 'tor_portable'
                # start the timer that will periodically check that tor is still running
                start_portable_tor_timer()
        else:
            print('No own Tor instance. Settings in [tor] will be used')

    except:
        print('An error occurred while starting tor.')

    print(f'Changing working directory back to {old_dir}')
    os.chdir(old_dir)
    print(f'Current working directory is {os.getcwd()}')


def stop_portable_tor():
    if not tor_pid:
        return
    else:
        print(f'(1) tor has pid {tor_pid}, terminating.')
        core.utils.terminate_process(tor_pid)


def start_portable_tor_timer():
    global tor_timer
    tor_timer = threading.Timer(10, on_portable_tor_timer)
    tor_timer.start()


def on_portable_tor_timer():
    if tor_proc.poll() is not None:
        print(f'Tor stopped running. Will restart it now.')
        start_portable_tor()
    else:
        start_portable_tor_timer()
