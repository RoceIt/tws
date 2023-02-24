#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)


"""Requests to start & stop a tws connection in a GSC model

Library provides the requests to open, close & check a tws connection.

Requests
  open_connection_with_tws_server: open a tws connection
  close_tws_connection: close the tws connection
  is_connected_with_tws_server: check if a tws server is connected
  tws_server_is_responsive: check if connected tws server is responsive
  
namespace properties
  tws_connection: server, the handle for the tws connection
   
"""


import tws
import TWSClient
from generic_server_client import *


class TWSClientConnection(LibraryOfServerClientRequests):
    
    @staticmethod
    def open_connection_with_tws_server__request():
        """Connect to a running tws server.
                
        Arguments
          server_ip: string, network address or localhost
          server_port: integer, port number
          client_id: integer, id for tws connection (see tws api)
          
        Return Value
          'connected': tws server is connected
          TWSClient.ConnectingError: connection failed
          
        Server Side        
          -new namespace properties
            tws_connection: the handle to use the tws connection
          -handeled exceptions
            TWSClient.ConnectingError: logged, passed to server & client
        
        """
        # SERVER FUNCTION
        def server_function(data, send, receive, server_ns):
            if not hasattr(server_ns, 'tws_connection'):
                server_ip, server_port, client_id = data
                try:          
                    server_ns.tws_connection = TWSClient.TWSconnection(
                        server_ip, server_port, client_id)     
                except TWSClient.ConnectingError as err:
                    server_ns.self.logger.warning(
                        'could not make tws connection {}@{}:{} | {}'.format(
                            client_id, server_ip, server_port, err))
                    send(err)
                    raise
            server_ns.self.logger.info(
                'server: open_connection_with_tws_server: {}@{}:{}'.
                format(client_id, server_ip, server_port))
            send('connected')
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST
        request = ServerClientRequest(
            request_string='open_connection_with_tws_server',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def close_tws_connection__request():
        """Close connection with tws server.
        
        Arguments
          No arguments
          
        Return Value
          True: tws connection closed
          
        Server Side
          -removed namespace properties
            tws_connection  
        
        """
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            server.tws_connection.disconnect(silent=True)
            del server.tws_connection
            server.self.logger.info('server: tws_connection_closed')
            send(True) 
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST       
        request = ServerClientRequest(
            request_string='close_tws_connection',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def is_connected_with_tws_server__request():
        """Check if server is connected with a tws server.
        
        Arguments
         No arguments
         
        Return Value
          True: server is connected with a tws server
          False: server is not connected with a tws server
        
        """  
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            send(hasattr(server, 'tws_connection'))  
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='is_connected_with_tws_server',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
        
    @staticmethod
    def tws_server_is_responsive__request():
        """Check if tws server is answering in time.
        
        Arguments
          No arguments
          
        Return Value
          True: tws server is responding in time
          False: tws server is not responding in time
          
        
        """   
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            if not hasattr(server, 'tws_connection'):
                answer = False
            else:
                answer = server.tws_connection.is_alive()
            send(answer)        
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST           
        request = ServerClientRequest(
            request_string='tws_server_is_responsive',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request