"""a simple stoopid client"""

import mypy

from generic_server_client import *


class sscs_(LibraryOfServerClientRequests):
    
    @staticmethod
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
    
    @staticmethod
    def sum__request():    
        def server_function(data, send, receive, server):
            answer = sum(data)
            send(answer)
        request = ServerClientRequest('sum')
        request.server_function = server_function
        return request
    
    @staticmethod
    def local_sum__request():
        def client_function(data, send, receive, server):
            send(data[:1])
            function = receive()
            return function(data[1], data[2])
        def server_function(data, send, receive, server):
            send(suma)
        request = ServerClientRequest('local_sum')
        request.client_function = client_function
        request.server_function = server_function
        return request
        
    
    @staticmethod
    def count_down__request():
        def server_function(data, send, receive, server):
            start = data[0]
            while start >=0:
                send(start)
                receive()
                start -= 1
            
        request = ServerClientRequest('count_down', mode='stream')
        request.server_function = server_function
        return request
    
def suma(a,b):
    return a+b

def sscs(server_ip='10.1.1.101'):
    a_sscs = GenericServerClientModel(server_ip, 44216)
    a_sscs.add_request_library(sscs_())
    return a_sscs
