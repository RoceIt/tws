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

algo = theSimulator()
the_trade = ATrade(algo)
the_trade.setParameters(spv)
local_parameters = {}
local_parameters = {'new': True,
                    'time_unit': 's',
                    'number_of_units': 100
                    }
if local_parameters:
    the_trade.setParameters(local_parameters)
the_trade.arm_simulator()

base_file  = os.path.join(mypy.TMP_LOCATION,'aex5s.data')
column     = mypy.ColumnName('IBdata')
ioh = open(base_file, 'r')

while 1:
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
