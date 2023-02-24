#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''

import mypy
import os.path
from trading import ATrade
from SCR2 import theRunner, spv, EORTH
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
                algo = theRunner()
                the_trade = ATrade(algo)
                the_trade.setParameters(spv)
                local_parameters[loop1_parameter] = loop1
                local_parameters[loop2_parameter] = loop2
                the_trade.setParameters(local_parameters)
                trade_list.append(the_trade)
                print('{} starting '.format(mypy.now()),
                                            '|'.join([str(loop1), str(loop2)]))
            for trade in trade_list:
                trade.arm_simulator()
            for day in sorted(data.keys()):
                eorth = data[day][-1].time
                for trade in trade_list:
                    trade.send_info(EORTH, eorth)
                    trade.run_procedure('restart_traders')
                for curr_bar in data[day][:-2]:
                    for trade in trade_list:
                        trade.new_bar(curr_bar)
                for trade in trade_list:
                    trade.run_procedure('eop_proc')
        except Empty:
            return True

db_PATH= mypy.DB_LOCATION
max_dax_time = mypy.py_time('17:30:00')

IBContractName = 'AEX-index'
#IBContractName = 'DJ_Industrial'
#IBContractName = 'DAX-30'
#IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'
#IBContractName = 'DJ_Eurostoxx50'

#start_date = '2009/12/16'
start_date = '2011/06/01'

local_parameters = {'name': 'eurodol2',
                    'new': True,
                    'contract': 'foo',
                    'number_of_contracts': 1,
                    'time_unit': 's',
                    'number_of_units': 5,
                    'limit_b_perc': 100,
                    'maximal_stop': 0.5, 
                    'leave_pos_before_eorth_in_s': None,
                    'enter_pos_before_eorth_in_s': None, 
                    'min_price_variation': 0.05       
                    }

loop1_parameter, loop1_values = 'number_of_units', [20, 25
                                                    ]
loop2_parameter, loop2_values = 'maximal_stop', [0.5] #25,10]

number_of_processes = 4
loops_per_process = 1

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
print('{} creating date date'.format(mypy.now()))
for day in dates: #range(0, len(dates)):
    #print(dates[day])
    print(day)
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, day, #dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    if IBContractName == 'DAX-30':
        data = [ochlBar(mypy.py_date_time(day+' '+curr_time, 
                                          mypy.iso8601TimeStr),
                        q_open, q_close, q_high, q_low)
                for curr_time, q_open, q_close, q_high, q_low in data
                if curr_time <= str(max_dax_time)]
    else:
        data = [ochlBar(mypy.py_date_time(day+' '+curr_time, 
                                          mypy.iso8601TimeStr),
                        q_open, q_close, q_high, q_low)
                for curr_time, q_open, q_close, q_high, q_low in data]
        
    #data.append(mypy.py_date_time(day + ' ' + data[-1][0],
    #                              mypy.iso8601TimeStr)) # is the eorth
    #print(ddata[-1])
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






    
                                         
                                        
