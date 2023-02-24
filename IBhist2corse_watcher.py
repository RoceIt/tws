#!/usr/bin/env python3
#
#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)
#
#  license: GNU GPLv3
#
#  This library is free software; you can redistribute it and/or
#  modify it under the terms of the GNU Lesser General Public
#  License as published by the Free Software Foundation; either
#  version 3 of the License, or (at your option) any later version.

# datafeeder zoals bij leJef, op de AEX-indexdb

import mypy
import sql_IB_db
import sql_IB_chart_time_db
import os.path
import pickle
import csv
import mysqlite3
import corse_watcher
from optparse import OptionParser



PERIODS_FOR_OCHL = ['D','h','m','s']


db_PATH= mypy.DB_LOCATION

usage = 'Usage: %prog [options] IBcontractName'
parser = OptionParser(usage=usage)
parser.add_option('-f', '--file', 
                  dest='filename', default=False,
                  help='Write output to FILE', metavar='FILE')
parser.add_option('-u', '--unit',
                  choices=PERIODS_FOR_OCHL,
                  dest='type', default='s',
                  help='choose from D, h, m, s')
parser.add_option('-n', '--number',
                  type='int',
                  dest='number', default=5,
                  help='number of units for 1 period')
#parser.add_option('-o', '--outputfile',
#                  dest='outputfile', default='out',
#                  help='set output filename')
parser.add_option('-i', '--interactive',
                  dest='interactive', action='store_true', default = False,
                  help='run interactive')
parser.add_option('-U', '--update',
                  dest='update', action='store_true', default = False,
                  help='update file')
parser.add_option('-t', '--table',
                  dest='table', default = 'TRADES_5_secs',
                  help='choose the db contracttable you\'ld like to use, TRADES_5_secs is default')
#parser.add_option('-b', '--begin',
#                  default='',
#                  help='set start date', metavar='YYYY/MM/DD HH:MM:SS')
#parser.add_option('-e', '--end',
#                  default=datetime.now().strftime(mypy.stdDateTimeStr),
#                  help='set end date', metavar='YYYY/MM/DD HH:MM:SS')
#parser.add_option('-s', '--show',
#                  choices=list(tws.rhd_what_to_show),
#                  default='TRADES',
#                  help='check tws.rhd_what_to_show for valid strings', metavar='WHAT_TO_SHOW')
(opts, args) = parser.parse_args()
if len(args) >1:
    print('probleem met argumenten, gebruik --help voor info')
    raise
elif len(args) == 1:
    IBContractName = args[0]
else:
    IBContractName = 'AEX-index'

IB_db = os.path.join(db_PATH, IBContractName+'.db')
if not os.path.isfile(IB_db):
    print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
    raise
IB_dbTable = opts.table
column = mypy.ColumnName('IB_db') 
base_filename = IBContractName + '_' + IB_dbTable + '_' + str(opts.number) + str(opts.type)
corse_watcher_filename = base_filename + '.corse'
corse_watcher_bear_corse_filename = base_filename + '.bear'
corse_watcher_bull_corse_filename = base_filename + '.bull'

if opts.update:
    if os.path.isfile(corse_watcher_filename):
        print('loading corse_watcher instance')
        with open(corse_watcher_filename,'rb') as ifh:
            cwh = pickle.load(ifh)            
    else:
        print('can not load', corse_watcher_filename)
        exit()
else:
    cwh = corse_watcher.corse_watcher(opts.type, opts.number)

IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')

###
# if updating search for the last date, else use all dates.
if opts.update:
    last_date = cwh.info('datetime_curr_bar')
    print('last bardate in corse_watcher', last_date)
    dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable, start = last_date)
else:
    dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)

print ('Output naar bestand ',corse_watcher_filename)

for day in range(0, len(dates)):
    print(dates[day])
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    for curr_time, q_open, q_close, q_high, q_low in data:
        bar_time = mypy.py_date_time(dates[day]+' '+curr_time, mypy.iso8601TimeStr)
        if not opts.update or bar_time > last_date:
            if cwh.insert(bar_time, q_open, q_close, q_high, q_low) and opts.interactive:
                cwh.exportCorses(corse_watcher_bull_corse_filename,
                                 corse_watcher_bear_corse_filename)
                input('druk `enter` om te vervolgen')

IB_db_h.close()

cwh.exportCorses(corse_watcher_bull_corse_filename,
                 corse_watcher_bear_corse_filename)
cwh.write_to_file(corse_watcher_filename)
