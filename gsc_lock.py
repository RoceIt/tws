#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import threading
import sys
import mypy

from managed_namespace import *
from generic_server_client import *

"""Lock server

Start server: ./gsc_lock.py start_server <ip>:<host>

"""

_STD_IP = 'localhost'
_STD_PORT = 14700

class GSC_Lock(LibraryOfServerClientRequests):
    
    def __init__(self, name=None, ip='localhost', port= 14700):
        if not name == None:
            self.name = name
            self.GSC = client_server(ip, port)
                        
    def __call__(self):        
        assert hasattr(self, 'name') and hasattr(self, 'GSC'), (
            'use GSC_Lock(general_server_client, name) for with statement')
        assert isinstance(self.GSC, GenericServerClientModel),(
            'GSC must be a GenericServerClientModel')
        client, get_lock = self.GSC.client_for_request('get_server_lock', self.name)
        if get_lock == 'ok':
            class cm_server_lock():
                def __init__(self):
                    pass
                def __enter__(self_):
                    pass
                def __exit__(self_, *ignore):
                    client.close()
            return cm_server_lock()
        client.close()
        return get_lock
            
    
    @staticmethod
    def get_server_lock__request():
        def server_function(data, send, receive, server):  
            print('in server function')    
            assert isinstance(server, ManagedNamespace), 'nenenen'
            name = data[0]
            if not server.has_lock(name):
                print('creating lock')
                server.add_lock(name)
            with server.lock(name):
                send('ok')
                print('ok')
                try:
                    receive()
                except:
                    pass
                print('ok stopped')
        request = ServerClientRequest('get_server_lock', mode='keep_open')
        request.server_function = server_function
        return request

def client_server(server_ip=_STD_IP, server_port=_STD_PORT):
    gcs = GenericServerClientModel(server_ip, server_port)
    gcs.add_request_library(GSC_Lock())
    return gcs
    
if __name__ == '__main__':
    if (not len(sys.argv) in {2,3}
        or
        not sys.argv[1] == 'start_server'):
        print('usage: {} start_server [<ip>:<port>]'.format(sys.argv[0]))
    else:
        try:
            ip, port = sys.argv[2].split(':')
            port = int(port)
        except IndexError:
            ip, port = _STD_IP, _STD_PORT
        lock_server = client_server(ip, port)
        ip, port = lock_server.start_server()
        print('LOCK SERVER RUNNING @ {}:{}'.format(ip, port))
        mess = "Enter 'stop_server' to stop the server: "
        while not mypy.get_string(mess, empty=True) == 'stop_server':
            pass
        lock_server.stop_server()
        
    
    
                
        
            
            