#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

"""a simple stoopid client"""

import mypy
from generic_server_client import *



def your_name__request():
    def client_function(data, send, receive, client):
        send(data)
        answer = receive()
        return answer
    
    def server_function(data, send, receive, server):
        send('simple stoopid client')
        
    request = ServerClientRequest('your_name')
    request.client_function = client_function
    request.server_function = server_function
    return request


def sum__request():    
    def server_function(data, send, receive, server):
        answer = sum(data)
        send(answer)
    request = ServerClientRequest('sum')
    request.server_function = server_function
    return request
      

def sscs(server_ip='10.1.1.101'):
    a_sscs = GenericServerClientModel(server_ip, 44216)
    a_sscs.add_request(your_name__request())
    a_sscs.add_request(sum__request())
    return a_sscs


