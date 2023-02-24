#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''

import mypy
import os.path
from trading import ATrade
from SimpleCorseSim import theSimulator, spv
from barData import ochlBar
from time import sleep
import mysqlite3
import sql_IB_db

db_PATH= mypy.DB_LOCATION

IBContractName = 'euro-dollar'
start_date = '2010/11/01'


algo = theSimulator()
the_trade = ATrade(algo)
the_trade.setParameters(spv)
local_parameters = {}
local_parameters = {'new': True,
                    'time_unit': 's',
                    'number_of_units': 300
                    }
if local_parameters:
    the_trade.setParameters(local_parameters)
the_trade.arm_simulator()

IB_db = os.path.join(db_PATH, IBContractName+'.db')
if not os.path.isfile(IB_db):
    print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
    raise
IB_dbTable = 'MIDPOINT_5_secs'
column = mypy.ColumnName('IB_db')
IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')

#dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable, start = mypy.py_date(start_date))
dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)



for day in range(0, len(dates)):
    print(dates[day])
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    for curr_time, q_open, q_close, q_high, q_low in data:
        bar_time = mypy.py_date_time(dates[day]+' '+curr_time, mypy.iso8601TimeStr)
        curr_bar= ochlBar(bar_time, q_open, q_close, q_high, q_low)
        the_trade.new_bar(curr_bar)


while False:
    latest = ioh.readline().split()
    if not latest:
        sleep(0.5)
        continue
        #print(strftime(mypy.stdTimeStr, localtime(int(latest[column.time]))), 
        #       float(latest[column.wap]))
    try:
        theTime = mypy.epoch2date_time(float(latest[column.time]))
               #quote   = float(latest[column.wap])
        bar_open = float(latest[column.open])
        bar_low = float(latest[column.low])
        bar_high = float(latest[column.high])
        bar_close = float(latest[column.close])
    except (ValueError, IndexError) as err:
        continue
    curr_bar = ochlBar(theTime, bar_open, bar_close, bar_high, bar_low)
    the_trade.new_bar(curr_bar)
