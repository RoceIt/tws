#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

from generic_server_client import (GenericServerClientModel,
                                   ServerClientRequest,
                                   RequestError)
from tws_client_connection_gscLib import TWSClientConnection

class OrderRequestError(RequestError):pass

class OrderRequests(TWSClientConnection):
    
    @staticmethod
    def new_order__request():
        def server_function(data, send, receive, server):
            if not server.self.client_for_request('is_connected_with_tws_server'):
                mess = 'realbar server not connected with tws server'
                err = RealbarRequestsError(mess)
                send(err)
                raise
            try:
                id_ = self.server.tws_connection.place_order(*data)
            except Exception as err:
                send(err)
                raise
            send(id_)
        request = ServerClientRequest('new_order')
        request.server_function = server_function
        return request 
            
                
            
def server_client(server_ip='localhost', server_port= 0):
    cs = GenericServerClientModel(server_ip, server_port, 'real_bar_server')
    cs.add_request_library(OrderRequests())
    return cs