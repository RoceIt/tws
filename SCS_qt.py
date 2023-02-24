#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''

import mypy
import os.path
from trading import ATrade, load_ATrade
from SimpleCorseSim import theSimulator, spv, EORTH, REACTIVATE_SUSPENDED_TRADES
from barData import ochlBar
from time import sleep
import mysqlite3
import sql_IB_db

db_PATH= mypy.DB_LOCATION
max_dax_time = mypy.py_time('17:30:00')

LOAD_EXISTING_TRADER = False


pickleName = 'testfile_s_900_tbes_lbp65_ms1.pickle'
#IBContractName = 'AEX-index'
#IBContractName = 'DJ_Industrial'
IBContractName = 'DAX-30'
#IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'
#IBContractName = 'Apple'
#start_date = '2010/11/01'
start_date = '2009/12/15'
#start_date = '2010/09/13'
#start_date = '2011/01/15'
#start_date = '2011/01/31'
end_date = '2010/12/16'
if not LOAD_EXISTING_TRADER:
    algo = theSimulator()
    the_trade = ATrade(algo)
    the_trade.setParameters(spv)
    local_parameters = {}
    local_parameters = {'name': 'qt_dax2',
                        'new': True,
                        'time_unit': 's',
                        'number_of_units': 330,
                        'export_trader_instructions': True,
                        'limit_b_perc': 97,
                        'maximal_c': None,
                        'maximal_stop': 7, 
                        'leave_pos_before_eorth_in_s': 120,
                        'enter_pos_before_eorth_in_s': None
                        }
    if local_parameters:
        the_trade.setParameters(local_parameters)
        the_trade.arm_simulator()
else:
    print(pickleName)
    the_trade = load_ATrade(pickleName)

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
dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable, start = mypy.py_date(start_date),
                                                 stop = mypy.py_date(end_date))
#dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)
print(dates)

last_eorth = ''
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
        the_trade.send_info(EORTH, eorth)
        last_eorth = eorth
    the_trade.send_info(REACTIVATE_SUSPENDED_TRADES)
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

the_trade.info('simulator_CSV_trade_list')
the_trade.save()
