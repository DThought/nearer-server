import base64
from collections import deque
import os
import queue
import re
import socket
import sys
import threading
import time


class NearerCommand(object):
    PLAY, SKIP, STOP, APPEND, REMOVE = range(5)

    def __init__(self, type, data=None):
        self.type = type
        self.data = data


class NearerData(object):
    def __init__(self, uri, length):
        self.uri = uri
        self.length = length


class NearerThread(threading.Thread):
    def __init__(self, out = None, recv=None):
        super(NearerThread, self).__init__()
        self.out = out or sys.stdout
        self.recv = recv or queue.Queue()
        self.alive = threading.Event()
        self.alive.set()
        self._handlers = {
            NearerCommand.PLAY: self._nplay,
            NearerCommand.SKIP: self._nskip,
            NearerCommand.STOP: self._nstop,
            NearerCommand.APPEND: self._nappend,
            NearerCommand.REMOVE: self._nremove
        }
        self._playlist = deque()
        self._nplaying = False
        self._next = None

    def run(self):
        while self.alive.is_set():
            try:
                cmd = self.recv.get(True, 1)
                self._handlers[cmd.type](cmd.data)
            except queue.Empty as e:
                pass
            if self._nplaying and self._next < time.time():
                if self._playlist:
                    track = self._playlist.popleft()
                    self._write('playurl ' + track.uri)
                    self._next = time.time();
                    self._next += int(track.length) + 5
                else:
                    self._nstop(None)

    def join(self, timeout=None):
        self.alive.clear()
        self._nstop(None)
        threading.Thread.join(self, timeout)

    def _nplay(self, data):
        if self._nplaying:
            return
        self._nplaying = True
        self._nskip(data)

    def _nskip(self, data):
        self._next = time.time()

    def _nstop(self, data):
        self._nplaying = False
        self._write('quit')

    def _nappend(self, data):
        self._playlist.append(data)
        self._nplay(data)

    def _nremove(self, data):
        dirty = True
        while dirty:
            dirty = False
            for track in self._playlist:
                if track.uri == data.uri:
                    dirty = True
                    self._playlist.remove(track)
                    break

    def _write(self, string):
        with open(out, 'w') as f:
            f.write(string)


srv = sys.argv[1]
out = sys.argv[2]

try:
    os.unlink(srv)
except FileNotFoundError:
    pass

sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
sock.bind(srv)
os.chmod(srv, 0o777)
sock.listen(1)
thread = NearerThread(out)
thread.start()
while True:
    conn, address = sock.accept()
    try:
        data = conn.recv(64)
        if data:
            data = data.decode('ascii').split()
            try:
                type = getattr(NearerCommand, data[0])
                if len(data) == 3:
                    if re.search(r'/[^\w-]/', data[1]):
                        continue
                    if re.search(r'/\S/', data[2]):
                        continue
                    cmd = NearerCommand(type, NearerData(data[1], data[2]))
                else:
                    cmd = NearerCommand(type)
                thread.recv.put(cmd)
                print(data)
            except AttributeError:
                continue
    finally:
        conn.close()
