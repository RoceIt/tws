#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)
#

'''Just a file to test the SimpleCorseSim'''
import sys
import os.path
from time import sleep

import mypy
from trading import ATrade, load_ATrade
from SimpleCorseSim import theSimulator, spv, EORTH
from barData import ochlBar
import mysqlite3
import sql_IB_db

pickleName = sys.argv[-2]
datafile = sys.argv[-1]

#IBContractName = 'AEX-index'
IBContractName = 'DJ_Industrial' 
#IBContractName = 'DAX-30'
#IBContractName = 'euro-dollar'
#IBContractName = 'S&P_500'
#IBContractName = 'Nasdaq_100'

while 1:
    try:
        eorth = input('How late do the markets close today (HH:MM:SS)? ')
        eorth = mypy.py_time(eorth)
        break
    except ValueError:
        print('Can not proces date format')

print('loading pickle')
if os.path.isfile(pickleName):
    the_trade = load_ATrade(pickleName)
else:
    raise

the_trade.send_info(EORTH, eorth)

base_file  = mypy.TMP_LOCATION+datafile
column = mypy.ColumnName('IBdata')
ioh = open(base_file, 'r')
#ofh = open('traderATwork', 'a')

old_resp = ''
try:
    while 1:
        latest = ioh.readline().split()
        if not latest:
            sleep(0.5)
            continue
        try:
            theTime = mypy.epoch2date_time(float(latest[column.time]))
            bar_open = float(latest[column.open])
            bar_low = float(latest[column.low])
            bar_high = float(latest[column.high])
            bar_close = float(latest[column.close])
        except (ValueError, IndexError) as err:
            continue
        curr_bar = ochlBar(theTime, bar_open, bar_close, bar_high, bar_low)
        resp = the_trade.new_bar(curr_bar)

except KeyboardInterrupt:
    print('clean exit, writing corse_watcher to file')
    the_trade.info('simulator_CSV_trade_list')
    the_trade.save(pickleName)
    ioh.close()
    #ofh.close()

