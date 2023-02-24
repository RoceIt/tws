#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''
import sys
import os
import pickle
from time import sleep

import mypy
from trading import ATrade, load_ATrade
from SimpleCorseRunner import theRunner, spv, EORTH
from barData import ochlBar
import mysqlite3
import sql_IB_db
import tws
import TWSClient

STD_IP = '10.1.1.102'
STD_PORT = 10911
STD_CLIENT = 11

def get_base_files():
    
    '''ask for picle file and data file'''
    pickle_file = mypy.get_string('pickle file: ')
    data_file = mypy.get_string('data file: ')
    return pickle_file, data_file


def admin_file(file_name):

    '''returns the administrator filename for the given file'''
    name = os.path.basename(file_name)
    


def main():

    '''dispatch for cli startup
    
    first argument is the filename with full path to the pickle file
    second argument is the name of data file in TEMP_LOCATION'''
    #read & check cli arguments
    try:
        pickle_Name = sys.argv[-2]
        data_file = sys.argv[-1]
    except IndexError:
        pickleName, datafile = get_base_files()
    data_file = os.path.join(mypy.TMP_LOCATION, data_file)
    if os.path.isfile(pickle_Name):
        pass
    
        
    

pickleName = sys.argv[-2]
datafile = sys.argv[-1]

SCS_running = os.path.join(mypy.TMP_LOCATION, pickleName + 'RUNNING')

if os.path.isfile(SCS_running) or datafile == 'STOP':
    if datafile == 'STOP':
        print('Trying to stop {}'.format(pickleName))
        os.remove(SCS_running)
    else:
        print('{} seems to be running, if not use \'stop\' as 2nd argument')
    exit()

open(SCS_running, 'w').close()

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
        break
    except KeyError:
        print('can\'t find TWS server')

while 1:
    try:
        info_string = 'How late do the markets close today (HH:MM:SS)? '
        eorth = mypy.get_string(info_string, default=False)
        if eorth:
            eorth = mypy.py_date_time(eorth,mypy.TIME_STR)
        break
    except ValueError:
        print('Can not proces date format')

r_contract = mypy.get_string('trading contract:')
r_contract = tws.contract_data(r_contract)
nr_of_contracts = mypy.get_int('number of contracts (1): ',
                               default=1)

if mypy.get_bool('Set gap (Y/N)? ', default = False):    
        t_contract = mypy.get_string('corse contract:')
        t_contract = tws.contract_data(t_contract)
        r_bar_id = twss.req_real_time_bars(r_contract)
        t_bar_id = twss.req_real_time_bars(t_contract)
        gap = (t_bar_id, r_bar_id)
else:
    gap = None
    
    
if mypy.get_bool('create backdoor file (Y/N)?', default=False):
    backdoor_name = mypy.get_string('backoor filename: ')
    twss.open_info_backdoor(backdoor_name)
    

print('loading pickle')
if os.path.isfile(pickleName):
    the_trade = load_ATrade(pickleName)
else:
    raise

if eorth:
    the_trade.send_info(EORTH, eorth)
the_trade.send_info('set_contract_data', (r_contract, nr_of_contracts))

logfile = pickleName.replace('pickle', 'log')
logfile = os.path.join(mypy.LOG_LOCATION, logfile)
the_trade.send_info('set_reporter', ('to file', [logfile]))
tws_send = False

the_trade.run_procedure('restart_traders')


base_file  = mypy.TMP_LOCATION+datafile
#column = mypy.ColumnName('IBdata')
ioh = open(base_file, 'rb')
#ofh = open('traderATwork', 'a')

while 1:
    try:
        latest = pickle.load(ioh)
    except EOFError:
        latest = False
    if not latest:
        if not tws_send:
            the_trade.send_info('set_TWS_h', twss)
            if gap:
                the_trade.send_info('set_future_gap', gap)
            the_trade.run_procedure('restart_traders')
            tws_send = True
        if not os.path.isfile(SCS_running):
            break           
        sleep(0.5)
        continue
    curr_bar = ochlBar(latest.time_, latest.open_, latest.close, 
                       latest.high,latest.low)
    resp = the_trade.new_bar(curr_bar)

the_trade.run_procedure('eop_proc')
if mypy.get_bool('clean exit, write corse_watcher to file? '):
    print('CLEAN EXIT, saving updated files')
    #the_trade.info('simulator_CSV_trade_list')
    the_trade.save(pickleName)
ioh.close()
    #ofh.close()

