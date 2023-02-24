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

db_PATH= mypy.DB_LOCATION
max_dax_time = mypy.py_time('17:30:00')

#IBContractName = 'AEX-index'
#IBContractName = 'DJ_Industrial'
#IBContractName = 'DAX-30'
IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'
#IBContractName = 'DJ_Eurostoxx50'
#start_date = '2010/11/01'
start_date = '2011/01/15'


local_parameters = {'name': 'eurodol',
                    'new': True,
                    'time_unit': 's',
                    'number_of_units': 'loop1',
                    'export_trader_instructions': False,
                    'limit_b_perc': 60 ,
                    'maximal_c': None,
                    'maximal_stop': None   , 
                    'leave_pos_before_eorth_in_s': None,
                    'enter_pos_before_eorth_in_s': None
                    }

IB_db = os.path.join(db_PATH, IBContractName+'.db')
if not os.path.isfile(IB_db):
    print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
    raise
IB_dbTable = 'TRADES_5_secs'
if IBContractName == 'euro-dollar':
    IB_dbTable = 'MIDPOINT_5_secs'
column = mypy.ColumnName('IB_db')
IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')

#dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable, start = mypy.py_date(start_date))
dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)
trade_list=[]
last_eorth = ''

loop1_parameter, loop1_values = 'number_of_units', [ 275, 280, 285, 290, 295]
loop2_parameter, loop2_values = 'maximal_stop', [None]

for loop1 in loop1_values:
    for loop2 in loop2_values:
        algo = theSimulator()
        the_trade = ATrade(algo)
        the_trade.setParameters(spv)
        local_parameters[loop1_parameter] = loop1
        local_parameters[loop2_parameter] = loop2
        the_trade.setParameters(local_parameters)
        trade_list.append(the_trade)

for trade in trade_list:
    trade.arm_simulator()

for day in range(0, len(dates)):
    print(dates[day])
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    eorth = data[-1][0]
    if IBContractName == 'DAX-30':
        eorth = max_dax_time
        data = [x for x in data if x[0] <= str(eorth)]
    if not eorth == last_eorth:
        for trade in trade_list:
            trade.send_info(EORTH, eorth)
        last_eorth = eorth
    for trade in trade_list: 
        trade.send_info(REACTIVATE_SUSPENDED_TRADES)
    for curr_time, q_open, q_close, q_high, q_low in data:
        bar_time = mypy.py_date_time(dates[day]+' '+curr_time, mypy.iso8601TimeStr)
        curr_bar= ochlBar(bar_time, q_open, q_close, q_high, q_low)
        for trade in trade_list:
            trade.new_bar(curr_bar)

for trade in trade_list:
    trade.info('simulator_CSV_trade_list')
    trade.save()
