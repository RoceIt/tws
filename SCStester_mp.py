#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''

import mypy
import os.path
from trading import ATrade
from SimpleCorseSim import theSimulator, spv, EORTH, REACTIVATE_SUSPENDED_TRADES
from barData import ochlBar
from time import sleep
import mysqlite3
import sql_IB_db
from multiprocessing import Queue, Manager, Process
from queue import Empty

def loop(work, data):
    while 1:
        try:
            todo = work.get(timeout=5)
            trade_list=[]
            last_eorth = ''
            for loop1, loop2 in todo:
                algo = theSimulator()
                the_trade = ATrade(algo)
                the_trade.setParameters(spv)
                local_parameters[loop1_parameter] = loop1
                local_parameters[loop2_parameter] = loop2
                the_trade.setParameters(local_parameters)
                trade_list.append(the_trade)
            for trade in trade_list:
                trade.arm_simulator()
            for day in sorted(data.keys()):
                eorth = data[day][-1][0]
                if not eorth == last_eorth:
                    for trade in trade_list:
                        trade.send_info(EORTH, eorth)
                    last_eorth = eorth
                for trade in trade_list: 
                    trade.send_info(REACTIVATE_SUSPENDED_TRADES)
                for curr_time, q_open, q_close, q_high, q_low in data[day]:
                    bar_time = mypy.py_date_time(day+' '+curr_time, mypy.iso8601TimeStr)
                    curr_bar= ochlBar(bar_time, q_open, q_close, q_high, q_low)
                    for trade in trade_list:
                        trade.new_bar(curr_bar)
            for trade in trade_list:
                trade.info('simulator_CSV_trade_list')
        except Empty:
            return True

db_PATH= mypy.DB_LOCATION
max_dax_time = mypy.py_time('17:30:00')

#IBContractName = 'AEX-index'
#IBContractName = 'DJ_Industrial'
IBContractName = 'DAX-30'
#IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'
#IBContractName = 'DJ_Eurostoxx50'

start_date = '2009/12/16'

local_parameters = {'name': 'dax',
                    'new': True,
                    'time_unit': 's',
                    'number_of_units': 340,
                    'export_trader_instructions': False,
                    'limit_b_perc': 115,
                    'maximal_c': None,
                    'maximal_stop': 0.00150, 
                    'leave_pos_before_eorth_in_s': 120,
                    'enter_pos_before_eorth_in_s': 900
                    }

loop1_parameter, loop1_values = 'number_of_units', [200, 205, 210, 215,
                                                    220, 225, 230, 235,
                                                    240, 245, 250, 255,
                                                    260]
loop2_parameter, loop2_values = 'maximal_stop', [7]

number_of_processes = 4
loops_per_process = 4

data_manager = Manager()
loop_data_list = Queue()
loop_data = []

for loop1 in loop1_values:
    for loop2 in loop2_values:
        loop_data.append((loop1,loop2))
        if len(loop_data) == loops_per_process:
            loop_data_list.put(loop_data)
            loop_data = []
if loop_data:
    loop_data_list.put(loop_data)

IB_db = os.path.join(db_PATH, IBContractName+'.db')
if not os.path.isfile(IB_db):
    print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
    raise
IB_dbTable = 'TRADES_5_secs'
if IBContractName == 'euro-dollar':
    IB_dbTable = 'MIDPOINT_5_secs'
column = mypy.ColumnName('IB_db')
IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')

dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable,
                            start = mypy.py_date(start_date))
#dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)

intradaydata = data_manager.dict()
#intradaydata = {}
for day in dates: #range(0, len(dates)):
    #print(dates[day])
    print(day)
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, day, #dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    if IBContractName == 'DAX-30':
        eorth = max_dax_time
        data = [x for x in data if x[0] <= str(max_dax_time)]
    #intradaydata[dates[day]]=(data)
    intradaydata[day] = data

IB_db_h.close()

process = []
for nr_of_process in range(number_of_processes):
    print('number of process', nr_of_process)
    process.append(Process(target=loop,
                           args=(loop_data_list,
                                 intradaydata)))
for worker in process:
    worker.start()

for worker in process:
    worker.join()






    
                                         
                                        
