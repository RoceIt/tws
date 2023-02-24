#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import argparse
import socket

from tws_orders_gscLib import server_client as tws_server_client
from stop_server_gsc import SimpleStopServerRequest

def main():
    orders_server_client = {'tws': tws_orders_server}
    arguments = parse_arguments(orders_server_client.keys())    
    orders_server_client[arguments.data_provider](arguments)
    
def tws_orders_server(arguments):
    action = {'start': start_tws_order_server,
              'stop': stop_tws_order_server}
    action[arguments.action](arguments)
 
def start_tws_order_server(arguments):
    ip, port = arguments.order_server_ip, arguments.order_server_port
    server_client = tws_server_client(ip, port)
    try:
        server_client.raw_data_client('check if server is running')
    except socket.error as err:
        if not err.errno == 111:
            raise
    else:
        print('Server was already running!')
        return
    tws_ip, tws_port = arguments.broker_server_ip, arguments.broker_server_port
    tws_id = arguments.broker_server_client_id
    server_client.add_request_library(SimpleStopServerRequest())
    server_client.start_server()
    server_client.client_for_request('open_connection_with_tws_server',
                                 tws_ip, tws_port, tws_id)
    print('order server started: {}:{}'.format(ip, port))
    print('                 TWS: {}@{}:{}'.format(tws_id, tws_ip, tws_port))
    server_client.client_for_request('wait_for_stop_server_request')
    server_client.client_for_request('close_tws_connection')
    server_client.stop_server()
    
def stop_tws_order_server(arguments):    
    ip, port = arguments.bar_server_ip, arguments.bar_server_port
    server_client = tws_client_server(ip, port)
    server_client.add_request_library(SimpleStopServerRequest())
    try:
        server_client.client_for_request('stop_server')
    except socket.error as err:
        if not err.errno == 111:
            raise
        else:
            print('realbar server was not running')
def parse_arguments(data_providers):
    parser = argparse.ArgumentParser(description='manage an order server')
    parser.add_argument('action',
                        choices=['start', 'stop'])
    parser.add_argument('-i', '--order_server_ip',
                        default='localhost')
    parser.add_argument('-p', '--order_server_port',
                        default=14701)
    parser.add_argument('-c', '--broker_server_client_id',
                        default = 47)
    parser.add_argument('-I', '--broker_server_ip',
                        default='localhost')
    parser.add_argument('-P', '--broker_server_port',
                        default=10911)
    parser.add_argument('-d', '--data_provider',
                        default='tws', choices=['tws'],
                        help = 'type of data provider')
    arguments = parser.parse_args()
    return arguments

if __name__ == '__main__':
    main()

