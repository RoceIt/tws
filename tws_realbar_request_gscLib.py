#!/usr/bin/env python3
#
#  Copyright (c) 2011, 2012 Rolf Camps (rolf.camps@scarlet.be)
#

"""Requests to read bardata from tws server

Library is using the tws_client_connection library to connect to a
running tws server. Before making a realbar request make sure you
made a connection with a tws server. The request returns a generator
object (streaming client) that returns 
TWSClientServerMessages.RealTimeBars. 

Requests
  <tws_client_connection requests>
  real_time_bars__request: start a real time bars feed
  
namespace properties
  <tws_client_connection namespace properties>
  real_time_bar: DictWithAccessedFlag, hold the timebars
  real_time_bar_id: Dict that hold the id's of the requests
  
namespace conditions
  'real_time_bars' + data: signal manager for new data
  
exceptions
  RealbarRequestsError: descendend of gsc.RequestError
  
"""

import mypy
import TWSClient
import tws
from managed_namespace import DictWithAccessedFlag
from generic_server_client import  (GenericServerClientModel, 
                                    ServerClientRequest,
                                    RequestError,
                                    RequestArgumentError,
                                    RequestTimedOut)
from tws_client_connection_gscLib import TWSClientConnection

class RealbarRequestsError(RequestError): pass


class RealbarRequests(TWSClientConnection):     
    
    @staticmethod
    def real_time_bars__request():
        """Return a 5 seconds live bars data stream.
        
        Requests returns a generator of TWSClientServerMessages.RealTimeBars. 
        You can stop the generator by calling generator.stop().
        
        
        server will stop if the TWS server din't answer for 5 
        minutes.
        
        Check IB API reference guide for valid argument values!
        
        arguments: contract, barsize, what_to_show, use_rth        
        
        """
        
        def digest_data(data):
            err_base = 'real_time_bars'
            err = None
            if len(data) in {4,5,6}:
                contract, barsize, what_to_show, use_rth, *foo = data
                tws_request_timeout_seconds = 300 if len(data) < 5 else data[4]
                keep_tws_feed_alive_seconds = 600 if len(data) < 6 else data[5]
            else:
                err = 'min 4, max 6 arguments'
            if err:
                raise RequestArgumentError(': '.join([err_base, err]))
            return (contract, barsize, what_to_show, use_rth,
                    tws_request_timeout_seconds, keep_tws_feed_alive_seconds)
          
        # SERVER FUNCTION   
        def server_function(data, send, receive, server):
            if not server.self.client_for_request('is_connected_with_tws_server'):
                mess = 'realbar server not connected with tws server'
                err = RealbarRequestsError(mess)
                send(err)
                raise err
            full_data = digest_data(data)
            data = full_data[0:4]
            if not server.has_condition('real_time_bars', *data):
                server.self.client_for_request('_start_real_time_bars_feed',
                                           *full_data)
            old_bar = None
            with server.condition('real_time_bars', *data):
                while 1:
                    try:
                        cw = server.condition('real_time_bars', *data).wait(30)
                    except ManagedNamespaceError:
                        # stop the server function when for some reason the
                        # condition was removed.
                        break
                    new_bar = server.real_time_bar[data]
                    if new_bar == None or new_bar == old_bar:      
                        mess = 'tws server is not sending data'
                        send(RequestTimedOut(mess))
                        raise RequestTimedOut(mess)
                    send(new_bar)
                    #print('sending new bar')
                    old_bar = new_bar
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='real_time_bars',
            mode='stream',
        )
        request.server_function = server_function
        #request.client_function=
        return request
    
    @staticmethod
    def _start_real_time_bars_feed__request():
        # Start the feed and add a threading.condition so other threads
        # can check availability of new data.  The feed wil stop if it
        # doesn't get data in time or when the maximal time without
        # clients is exceeded.
        #
        # The data send to the request must be (in order):
        #    the tws_contract, the barsize in seconds, 
        #    what_to_show (see IB man), use_rth (bool),
        #    time to wait for an answer of the tws server,
        #    max time without clients before the feed gets stopped
        # 
        # The condition to check is 
        #    server.condition[(tws_contract, barsize, what_to_show, use_rth)] 
        
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            wait = data[4]
            max_time_without_clients = data[5]
            if not (isinstance(wait, int) and 
                    isinstance(max_time_without_clients,int)):
                mess = ('real time bars wait and max_time_without_clients'
                        'must be integers')
                server.self.logger.error(mess)
                raise RequestArgumentError(mess)
            data = data[0:4]
            with server.atomic_action:
                if not hasattr(server, 'real_time_bar'):
                    server.real_time_bar = DictWithAccessedFlag()
                    server.real_time_bar_id = dict()     
                if server.has_condition('real_time_bars', *data):
                    send('Done')
                    return
                server.add_condition('real_time_bars', *data)
            tws_s = server.tws_connection
            id_ = tws_s.req_real_time_bars(*data)
            server.real_time_bar_id[data] = id_
            server.real_time_bar[data] = None
            time_without_clients = 0
            send('Done')
            server.self.logger.info('real time bars feed started {:3}:{}'.
                                    format(id_, data))
            print('>>> Real Time Bars Feed STARTED')
            print('{:6}: {}'.format(id_, data))
            while True:
                try:
                    answer = tws_s.real_bar_from(id_, wait=wait)
                except TWSClient.RequestStopped:
                    break
                except (TWSClient.RequestSended,
                        TWSClient.TimeOut):
                    print(1)
                    server.self.client_for_request(
                          '_stop_real_time_bars', *data)
                    mess = 'tws server is not sending data'
                    server.self.logger.error(mess)
                    raise RequestTimedOut(mess)
                except:
                    try:
                        print(2)
                        server.self.client_for_request(
                              '_stop_real_time_bars', *data)
                    except:
                        pass
                    mess = ('unexpected error in realbar request, sending '
                            'request to stop tws request')
                    server.self.logger.exception(mess)
                    raise
                else:
                    if not server.real_time_bar.key_used_for_reading(data):
                        time_without_clients += wait
                        if time_without_clients >= max_time_without_clients:
                            mess = ('maximum time without clients reading data'
                                    ' exceeded, stopping tws request')
                            server.self.logger.warning(mess)
                            server.self.client_for_request(
                                  '_stop_real_time_bars', *data)
                            break
                    else:
                        time_without_clients = 0
                    with server.condition('real_time_bars', *data):
                        server.real_time_bar[data] = answer
                        server.condition('real_time_bars', *data).notify_all() 
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST          
        request = ServerClientRequest(
            request_string='_start_real_time_bars_feed',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request
    
    @staticmethod
    def _stop_real_time_bars__request():
        # Send request to the tws server to stop the real bars stream.
        
        # SERVER FUNCTION
        def server_function(data, send, receive, server):
            if data in server.real_time_bar_id:
                id_ = server.real_time_bar_id[data]
                tws_s = server.tws_connection
                tws_s.stop_real_time_bars(id_)
                server.remove_condition('real_time_bars', *data)               
                send('Done')
                server.self.logger.info('real time bars feed stopped {:3}'.
                                    format(id_))
                print('<<< Real Time Bars Feed STOPPED')
                print('{:6}'.format(id_))
            else:
                mess = 'no request id for {}'.format(data)
                raise RequestError(mess)      
            
        # CLIENT FUNCTION
        #   standard client function
        
        # DEFINE REQUEST   
        request = ServerClientRequest(
            request_string='_stop_real_time_bars',
            mode='single',
        )
        request.server_function = server_function
        #request.client_functions = 
        
        return request 

def server_client(server_ip='localhost', server_port= 14701):
    cs = GenericServerClientModel(server_ip, server_port, 'real_bar_server')
    cs.add_request_library(RealbarRequests())
    return cs

if __name__ == "__main__":
    sc = server_client(server_port=0)
    sc.start_server()
    #connected = sc.request_client('open_connection_with_tws_server', 
                                  #'10.1.1.102', 10911, 37)
    connected = sc.client_for_request('open_connection_with_tws_server', 
                                  'localhost', 10911, 37)
    print(connected)
    #ctr = tws.contract_data('DAX-30')
    ctr = tws.contract_data('euro-dollar')
    #ds = sc.request_client('real_time_bars', ctr, '5 secs', 'TRADES', False)
    ds = sc.client_for_request('real_time_bars', ctr, '5 secs', 'MIDPOINT', False)
    for i, x in enumerate(ds):
        print('x: ',x)
        if i == 4:
            ds.close()
    sc.client_for_request('close_tws_connection')
    sc.stop_server()