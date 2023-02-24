#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''

import mypy
import os.path
from trading import ATrade
from SimpleCorseRunner import theRunner, spv, EORTH, REACTIVATE_SUSPENDED_TRADES
from barData import ochlBar
from time import sleep
import mysqlite3
import sql_IB_db

db_PATH= mypy.DB_LOCATION
max_dax_time = mypy.py_time('17:30:00')

#IBContractName = 'AEX-index'
#IBContractName = 'Apple'
#BContractName = 'DJ_Industrial'
IBContractName = 'DAX-30'
#IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'
#start_date = '2010/11/01'
#start_date = '2011/03/01'

algo = theRunner()
the_trade = ATrade(algo)
the_trade.setParameters(spv)
local_parameters = {}
local_parameters = {'name': 'dax',
                    'new': True,
                    'time_unit': 's',
                    'number_of_units': 230,
                    'limit_b_perc': 70,
                    'maximal_stop': 7,
                    'leave_pos_before_eorth_in_s': 120,
                    'enter_pos_before_eorth_in_s': 900,
                    'min_price_variation': 0.5
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

last_eorth = ''
if local_parameters:
    the_trade.setParameters(local_parameters)
the_trade.arm_algoritme()
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
    eorth =  mypy.py_date_time(dates[day]+' '+str(eorth), mypy.iso8601TimeStr)
    the_trade.send_info(EORTH, eorth)
    the_trade.run_procedure('restart_traders')
    for curr_time, q_open, q_close, q_high, q_low in data:
        bar_time = mypy.py_date_time(dates[day]+' '+curr_time, mypy.iso8601TimeStr)
        curr_bar= ochlBar(bar_time, q_open, q_close, q_high, q_low)
        the_trade.new_bar(curr_bar)
    the_trade.run_procedure('eop_proc')

the_trade.run_procedure('eop_proc')
the_trade.save()
