#!/usr/bin/env python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)


# datafeeder zoals bij leJef, op de AEX-indexdb

import mypy
import sql_IB_db
#import sql_IB_chart_time_db
import os.path
#import pickle
import csv
import mysqlite3
#import corse_watcher
from optparse import OptionParser
import gnuplot



PERIODS_FOR_OCHL = ['D','h','m','s']
db_PATH= mypy.DB_LOCATION
temp_store_file = 'IBhist2linegraph.tmp'

usage = 'Usage: %prog [options] IBcontractName'
parser = OptionParser(usage=usage)
#parser.add_option('-f', '--file', 
#                  dest='filename', default=False,
#                  help='Write output to FILE', metavar='FILE')
#parser.add_option('-u', '--unit',
#                  choices=PERIODS_FOR_OCHL,
#                  dest='type', default='s',
#                  help='choose from D, h, m, s')
#parser.add_option('-n', '--number',
#                  type='int',
#                  dest='number', default=5,
#                  help='number of units for 1 period')
#parser.add_option('-o', '--outputfile',
#                  dest='outputfile', default='out',
#                  help='set output filename')
#parser.add_option('-i', '--interactive',
#                  dest='interactive', action='store_true', default = False,
#                  help='run interactive')
#parser.add_option('-U', '--update',
#                  dest='update', action='store_true', default = False,
#                  help='update file')
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

IB_db_h = mysqlite3.sqlite3_db(IBContractName+'.db')


########
## compose the chart
########
chart = gnuplot.chart('AEX-index')
chart.settings.add_pre_setting('datafile','separator','","')
chart.settings.add_pre_setting('timefmt','"%H:%M:%S"')
chart.settings.add_pre_setting('xdata','time')

chart.add_plot()
chart.plotlist[0].add_data_serie('AEX-INDEX', filename='./IBhist2linegraph.tmp', 
                               fields=[1,2],
                               style='line')

while 1:
    day = input('Datum (YYYY/MM/DD) of Stop: ')
    if day == 'S' or day.lower() == 'stop':
        break
    else:
        data = sql_IB_db.get_data_on_date(IB_db_h, IB_dbTable, day, 
                                          column.time, column.close)
        with open(temp_store_file, 'w') as of:
            writer = csv.writer(of, quoting=csv.QUOTE_NONNUMERIC)
            writer.writerows(data)
    chart.plot()

IB_db_h.close()
