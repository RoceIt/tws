#!/usr/bin/env python3

import asyncore
import logging
import socket

#from asynchat_echo_server import EchoServer
from socketclientexp import EchoClient

logging.basicConfig(level=logging.DEBUG,
                    format='%(name)s: %(message)s',
                    )

#address = ('localhost', 0) # let the kernel give us a port
#server = EchoServer(address)
#ip, port = server.address # find out what port we were given

#message_data = open('lorem.txt', 'r').read()
client = EchoClient('localhost', 7496, 1)

client.close()
