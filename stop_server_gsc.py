#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

from threading import Event

from generic_server_client import (LibraryOfServerClientRequests,
                                   ServerClientRequest,
                                   RequestError)

class StopServerRequestError(RequestError): pass

class SimpleStopServerRequest(LibraryOfServerClientRequests):
    
    @staticmethod
    def wait_for_stop_server_request__request():
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            if hasattr(server, 'stop_server'):
                mess = 'wait_for_stop_server request is already running'
                err = RequestError(mess)
                send(err)
                raise err
            server.stop_server = Event()
            server.self.logger.info('Server ready to raise stop_server '
                                    'event')
            server.stop_server.wait()
            send('stop')
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST
        request = ServerClientRequest(
            request_string='wait_for_stop_server_request', 
            mode='single',
        )
        request.server_function = server_function    
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def stop_server__request():
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            if not hasattr(server, 'stop_server'):
                mess = 'No thread is waiting waiting for this signal'
                err = StopServerRequestError(mess)
                send(err)
                raise err
            send('ok')
            server.stop_server.set()
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST
        request = ServerClientRequest(
            request_string='stop_server',
            mode='single',
        )
        request.server_function = server_function
        #request.client_function =
        
        return request
        
        
