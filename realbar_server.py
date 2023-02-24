#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import argparse
import socket

from tws_realbar_request_gscLib import server_client as tws_server_client
from stop_server_gsc import SimpleStopServerRequest

TWS = 'tws'

def main():
    realbar_server_client = {TWS: tws_realbar_server}
    arguments = parse_arguments(realbar_server_client.keys())    
    realbar_server_client[arguments.data_provider](arguments)
    
def tws_realbar_server(arguments):
    action = {'start': start_tws_realbar_server,
              'stop': stop_tws_realbar_server}
    action[arguments.action](arguments)
 
def start_tws_realbar_server(arguments):
    ip, port = arguments.bar_server_ip, arguments.bar_server_port
    print(ip, port)
    server = tws_server_client(ip, port)
    if not port == 0:
        try:
            server.raw_data_client('check if server is running')
        except socket.error as err:
            if not err.errno == 111:
                raise
        else:
            print('Server was already running!')
            return
    tws_ip, tws_port = arguments.data_server_ip, arguments.data_server_port
    tws_id = arguments.data_server_client_id
    server.add_request_library(SimpleStopServerRequest())
    server.start_server()
    port = server.server_port
    print(ip, port)
    server.client_for_request('open_connection_with_tws_server',
                                 tws_ip, tws_port, tws_id)
    print('realbar server started: {}:{}'.format(ip, port))
    print('                   TWS: {}@{}:{}'.format(tws_id, tws_ip, tws_port))
    server.server.realbar_data_provider = TWS
    server.client_for_request('wait_for_stop_server_request')
    server.client_for_request('close_tws_connection')
    server.stop_server()
    
def stop_tws_realbar_server(arguments):    
    ip, port = arguments.bar_server_ip, arguments.bar_server_port
    server_client = tws_server_client(ip, port)
    server_client.add_request_library(SimpleStopServerRequest())
    try:
        server_client.client_for_request('stop_server')
    except socket.error as err:
        if not err.errno == 111:
            raise
        else:
            print('realbar server was not running')
def parse_arguments(data_providers):
    parser = argparse.ArgumentParser(description='manage a realbar server')
    parser.add_argument('action',
                        choices=['start', 'stop'])
    parser.add_argument('-i', '--bar_server_ip',
                        default='localhost')
    parser.add_argument('-p', '--bar_server_port', type=int,
                        default=14701)
    parser.add_argument('-c', '--data_server_client_id', type=int,
                        default = 37)
    parser.add_argument('-I', '--data_server_ip',
                        default='localhost')
    parser.add_argument('-P', '--data_server_port', type=int,
                        default=10911)
    parser.add_argument('-d', '--data_provider',
                        default=TWS, choices=[TWS],
                        help = 'type of data provider')
    arguments = parser.parse_args()
    return arguments

if __name__ == '__main__':
    main()

