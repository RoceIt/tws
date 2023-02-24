#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
#

import os
from datetime import timedelta
from time import sleep

import mypy
import tws
import TWSClient

STD_IP = '10.1.1.102'
STD_PORT = 10911
STD_CLIENT = 6

def main():

    active_feeds = {}
    do = {'S': stop_feed,
          'R': request_feed,
          'L': show_list,
          'A': automatic}     
    twss = connect2server()
    while True:
        action = get_users_choice()
        if action == 'Q':
            break
        elif action in do.keys():
                do[action](twss, active_feeds)
        else:
            print('Wrong choice!')
    twss.disconnect()


def connect2server():
    
    while 1:
        server_ip = mypy.get_string('server ip({}): '.format(STD_IP),
                                    default = STD_IP)
        server_port = mypy.get_int('server port({}): '.format(STD_PORT),
                                   default = STD_PORT)
        server_client = mypy.get_int('client id({}): '.format(STD_CLIENT),
                                     default = STD_CLIENT)
        try:
            twss = TWSClient.TWSconnection(server_ip, server_port, 
                                           client_id=server_client)
        except KeyError:
            print('can\'t find TWS server')
        return twss

def get_users_choice():

    request = ('(R)equest feed | (S)top feed | (L)ist | (Q)uit program \n')
    choice = mypy.get_string(request)
    return choice


def request_feed(twss, active_feeds):
    
    while True:
        contract = mypy.get_string('contract name:', default='STOP')
        try:
            contr_data = tws.contract_data(contract)
            break
        except tws.ContractNotInDB:
            if contract == 'STOP':
                return False
            else:                
                print('Unknown contract')
    while True:
        wts = mypy.get_string('what_to_show (TRADES): ',
                                  default = 'TRADES')
        if wts in tws.rtb_what_to_show:
            break
    if (contract in active_feeds and
        wts in active_feeds[contract]):
        print('feed already active, \nfilename: {}'.
              format(active_feeds[contract][wts][1]))
        return False
    else:
        active_feeds[contract] = {}
    filename = os.path.join(mypy.TMP_LOCATION, contract+'.data')
    if os.path.exists(filename):        
        reset = mypy.get_bool('Clear existing file?', default=True)
    else:
        reset = False
    id_ = send_request(twss, contr_data, wts, filename, reset)
    active_feeds[contract][wts] = (id_, contr_data, filename, mypy.now())
    print('outputfile set to {}'.format(filename))
    
        
def send_request(twss, tws_contract, what_to_show, filename, reset):
    
    id_ = twss.req_real_time_bars(tws_contract, what_to_show=what_to_show)
    twss.set_outputfile_for_id(id_, filename, reset)
    return id_


def stop_feed(twss, active_feeds):

    contract = mypy.get_string('contract name:')
    wts = mypy.get_string('what_to_show (TRADES): ', default='TRADES')
    try:
        id_ = active_feeds[contract][wts][0]
    except KeyError:
        print('can\'t find feed for contract')
        return False
    send_stop(twss, id_)
    del active_feeds[contract][wts]
    print('feed stopped!')
        
def send_stop(twss, id_):
    
    twss.remove_outputfile_for_id(id_)
    twss.stop_real_time_bars(id_)
    

def show_list(twss, active_feeds):

    print('\nACTIVE FEEDS')
    print('************')   
    for contract, wtss in active_feeds.items():
        for wts, v in wtss.items():
            print('{} {} to {}'.
                  format(contract, wts, v[2]))
    print('\n\n')
    
def automatic(twss, active_feeds):
    test_file = 'auto_feed_reader.tst'
    print('remove {} to continue in interactive mode'.format(test_file))
    open(test_file, 'a').close()
    while os.path.exists(test_file):
        for contract, wtss in active_feeds.items():
            for wts, v in wtss.items():
                if mypy.now() - v[-1] > timedelta(hours=10):
                    print('re-requesting {} {}'.format(contract, wts))
                    contr_data = active_feeds[contract][wts][1]
                    filename = active_feeds[contract][wts][2]
                    send_stop(twss, active_feeds[contract][wts][0])
                    id_ = send_request(twss, contr_data, wts, filename, False)
                    active_feeds[contract][wts] = (id_, contr_data, 
                                                   filename, mypy.now())
                    print('remove {} to continue in interactive mode'.
                          format(test_file))
        sleep(10)
                    
                    
if __name__ == '__main__':
    main()
