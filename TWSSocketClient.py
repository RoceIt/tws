#!/usr/bin/env python
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

# FILE: TWSSocketClient.py

'''TWS client socket

This module provides a socket interface with the TWS api
'''

import socket
import struct


EOL = struct.pack('!b', 0)

class TWSSocketClient(socket.socket):

    def _register(self, client_id):
        print('registering...')
        
    
    def __init__(self,host,port, client_id):
        print('Initialising TWSSocketClient')
        super().__init__(socket.AF_INET, socket.SOCK_STREAM)
        print('connecting ...')
        self.connect((host, port))
        self._register(client_id)

    def readByte(self):
        byte = self.recv(1)
        return unpack('!b', byte)[0]

    def write(self, data):
        if data == 0:
            self.send(EOL)
        else:
            for char in data:
                self.send(pack('!c', char)

