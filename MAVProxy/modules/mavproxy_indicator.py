#!/usr/bin/env python
'''indicator module for use with PiIndicator'''
import socket
import threading
import Queue
import time
from MAVProxy.modules.lib import mp_module
from pymavlink import mavutil

class SocketClientThread(threading.Thread):
    """ Implements the threading.Thread interface (start, join, etc.) and
        can be controlled via the cmd_q Queue attribute. Replies are
        placed in the reply_q Queue attribute.
    """
    def __init__(self, cmd_q=None, reply_q=None, port=8246):
        super(SocketClientThread, self).__init__()
        self.cmd_q = cmd_q or Queue.Queue()
        self.port = port
        self.alive = threading.Event()
        self.alive.set()
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    def run(self):

        while self.alive.isSet():
            try:
                # Queue.get with timeout to allow checking self.alive
                cmd = self.cmd_q.get(True, 0.1)
                try:
                    # try to send
                    self.socket.sendall(cmd + '\n')
                except IOError as e:
                    try:
                        # couldn't send, try to reconnect
                        print("Connect")
                        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        self.socket.connect(('localhost', self.port))
                        # try to send again before giving up
                        self.socket.sendall(cmd + '\n')
                    except IOError as e:
                        continue

            except Queue.Empty as e:
                continue

    def send(self, signalstring):
        self.cmd_q.put(signalstring, timeout=0.1)

    def join(self, timeout=None):
        self.alive.clear()
        threading.Thread.join(self, timeout)



class IndicatorModule(mp_module.MPModule):
    def __init__(self, mpstate):
        super(IndicatorModule, self).__init__(mpstate, "indicator", "indicator module", public = True)
        self.hb_enabled = True
        self.client = SocketClientThread()
        self.client.start()

    def send_signal(self, signalstring):
        self.client.send(signalstring)



    def mavlink_packet(self, m):
        '''handle an incoming mavlink packet'''
        if m.get_type() == "HEARTBEAT":
            if m.type != 6:
                if (m.base_mode & mavutil.mavlink.MAV_MODE_FLAG_SAFETY_ARMED) != 0:
                    self.send_signal("MAV_HB_ARMED")
                else:
                    self.send_signal("MAV_HB_DISARMED")


def init(mpstate):
    '''initialise module'''
    return IndicatorModule(mpstate)
