#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)


import pickle
import socket
import struct
import sys

class TWS_Slots_ID_Error(Exception): pass

address = ["localhost", 21001]




class SocketManager:

    def __init__(self, address):
        self.address = address

    def __enter__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect(self.address)
        return self.sock

    def __exit__(self, *ignore):
        self.sock.close()

def main():
    if len(sys.argv) > 1:
        address[0] = sys.argv[1]
    request = dict(a= get_client_id,
                   b= release_client_id,
                   c= show_client_id)
    menu = ( 'a: Ask a new client ID \n'
             'b: Release client ID \n'
             'c: Print occupied client ID\'s \n')
    valid = range(1,4)
    while True:
        action = UserInput.getnumber(request, valid)
        request[action](interactive=True)

def get_client_id(interactive=False):
    ok, data = handel_request("GET_CLIENT_ID")
    if not ok:
        raise(TWS_Slots_ID_Error)
    if interactive:
        print('you received client id: {d}'.format(data[0]))
    return data[0]

def handle_request(*parameters, wait_for_reply=False):
    sizestruct = struct.Struct('!I')
    data = pickle.dumps(parameters, 3)

    try:
        with SocketManager(tupple(address)) as sock:
            sock.sendall(sizestruct.pack(len(data)))
            sock.sendall(data)
            if not wait_for_reply:
                return
            
            size_answer = sock.recv(SizeStruct.size)
            size = sizestruct.unpack(size_answer)[0]
            result = bytearray()
            while True:
                data = sock.recv(4000)
                if not data:
                    break
                result.extend(data)
                if len(result) >= size:
                    break
        return pickle.loads(result)
    except socket.error as err:
        print("{0}: is the server running?".format(err))
        sys.exit(1)

if __name__ == '__main__':
    main()
