#!/usr/bin/env python3
#
#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)
#

import argparse
import socket

from alarm_server_gscLib import server_client as alarm_server_client
from stop_server_gsc import SimpleStopServerRequest

ALARM_SERVER_IP = 'localhost'
ALARM_SERVER_PORT = 14703

def main():
    action = {
        'start': start_alarm_server,
        'stop': stop_alarm_server,
    }
    arguments = parse_arguments() 
    action[arguments.action](arguments)
 
def start_alarm_server(args):
    ip, port = args.alarm_ip, args.alarm_port
    print(ip, port)
    server = alarm_server_client(ip, port)
    if not port == 0:
        try:
            server.raw_data_client('check if server is running')
        except socket.error as err:
            if not err.errno == 111:
                raise
        else:
            print('Server was already running!')
            return
    server.add_request_library(SimpleStopServerRequest())
    server.start_server()
    port = server.server_port
    print(ip, port)
    print('Alarm server started: {}:{}'.format(ip, port))
    server.client_for_request('wait_for_stop_server_request')
    server.stop_server()
    
def stop_alarm_server(args):    
    ip, port = args.alarm_ip, args.alarm_port
    server_client = alarm_server_client(ip, port)
    server_client.add_request_library(SimpleStopServerRequest())
    try:
        server_client.client_for_request('stop_server')
    except socket.error as err:
        if not err.errno == 111:
            raise
        else:
            print(' server was not running')
            return
    print( ' server halted')
    
            
def parse_arguments():
    parser = argparse.ArgumentParser(description='alarm server')
    parser.add_argument('action',
                        choices=['start', 'stop'])
    parser.add_argument('-i', '--alarm_ip',
                        default=ALARM_SERVER_IP)
    parser.add_argument('-p', '--alarm_port', type=int,
                        default=ALARM_SERVER_PORT)
    arguments = parser.parse_args()
    ###
    
    return arguments

if __name__ == '__main__':
    main()

