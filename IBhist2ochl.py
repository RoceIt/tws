#!/usr/bin/python3
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
import barData_0_1_1 as barData
from optparse import OptionParser



PERIODS_FOR_OCHL = ['D','h','m','s']


db_PATH= mypy.dblocation

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
parser.add_option('-o', '--outputfile',
                  dest='outputfile', default='out',
                  help='set output filename')
parser.add_option('-p', '--do_not_pickle',
                  dest='pickle', action='store_false', default = True,
                  help='Don\'t pickle te dict')
parser.add_option('-t', '--text_file',
                  dest='text', action='store_true', default = False,
                  help='Write as txt-file, for openoffice ...')
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

IB_db      = db_PATH+'/'+IBContractName+'.db'
if not os.path.isfile(IB_db):
    print('Geen database gegevens voor gegeven contract: {}', (IB_db,))
    raise
IB_dbTable = 'TRADES_5_secs'
column = mypy.ColumnName('IB_db') 
IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')
dates = sql_IB_db.get_dates(IB_db_h, IB_dbTable)
outputfile = opts.outputfile+'.ochl'
outputtxt  = opts.outputfile+'.csv'
#if opts.type == 's':
#    end_of_period = eop_s
#bar = {}
ochl_list= barData.ochl(opts.type, opts.number)

print ('Output naar bestand ',outputfile)

for day in range(1, len(dates)):
    print(dates[day])
    #curr_open = curr_close = curr_high = curr_low = 0
    data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, dates[day], 
                                      column.time, 
                                      column.open, column.close,
                                      column.high, column.low)
    for curr_time, q_open, q_close, q_high, q_low in data:
        #if not curr_open:
        #    curr_open  = q_open
        #    curr_close = q_close
        #    curr_high  = q_high
        #    curr_low   = q_low
        #else:
        #    curr_high  = max(curr_high, q_high)
        #    curr_low   = min(curr_low, q_low)
        bar_time = mypy.py_date_time(dates[day]+' '+curr_time, mypy.iso8601TimeStr)
        #if end_of_period(bar_time, opts.number):
        #    bar[bar_time]=[curr_open, q_close, curr_high, curr_low]
        #    curr_open = curr_close = curr_high = curr_low = 0
        ##pt = ochl_list.insert(bar_time, q_open, q_close, q_high, q_low)
        ##if pt:
        ##    print(pt)
        ochl_list.insert(bar_time, q_open, q_close, q_high, q_low)
    #print(ochl_list.hard_bar())

IB_db_h.close()

if opts.pickle:
    try:
        with open(outputfile, 'wb') as ofh:
            pickle.dump(ochl_list.ochl_list, ofh)
    except EnvironmentError as err:
        print(err)

if opts.text:
    ctf = sql_IB_chart_time_db.chart_time_feeder(IBContractName)
    print('creating text version')
    with open(outputtxt, 'w') as ofh:
        bar_writer = csv.writer(ofh)
        for bar in ochl_list.ochl_list:
            bar_writer.writerow([mypy.date_time2format(bar[0], mypy.iso8601TimeStr)] +
                                [ctf.symbol_chart_time(bar[0])]+
                                list(bar[1:]))
    ctf.close()


       
        

