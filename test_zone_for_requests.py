#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

from generic_server_client import *

class TestZoneForRequests(LibraryOfServerClientRequests):
    
    @staticmethod
    def repeat__request():
        """Keep sending back
        
        arguments: repeating number"""
        def client_function(data, send, receive, client):
            send(data)
            answer = receive()
            return answer
        def server_function(data, send, receive, server):
            number, repeat = data
            while repeat > 0:
                send(number)
                receive()
                repeat -= 1
        request = ServerClientRequest('echo', mode='stream')
        request.client_function = client_function
        request.server_function = server_function
        return request
    
    @staticmethod
    def give_me_a_five__request():
        """Return a 5."""
        def server_function(data,send,receive, server):
            send(5)
        request = ServerClientRequest('give_me_a_five')
        request.server_function = server_function
        return request 
    
    @staticmethod
    def give_me_a_number__request():
        """Return a 5."""
        def server_function(data,send,receive, server):
            anumber = server.self.client_for_request('give_me_a_five')
            send(anumber)
        request = ServerClientRequest('give_me_a_number')
        request.server_function = server_function
        return request
    
    @staticmethod
    def lock__request(name):
        """Return the ns lock"""
        def server_function(data,send,receive, server):
            if hasattr(server, name):
                
    