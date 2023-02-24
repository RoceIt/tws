#!/usr/bin/env python3

#  FILENAME: historicaldata.py

#  Copyright (c) 2010, Rolf Camps (rolf.camps@scarlet.be)

import os.path
import sqlite3
import io
from optparse import OptionParser
from datetime import datetime, timedelta

import mypy
import mysqlite3
import sql_IB_db
import tws as Broker           # Data, definitions & rules
import twsR as BrokerInterface #

class HistoricalDataError(Exception): pass
class ArgumentError(HistoricalDataError): pass


def main():
    usage = 'Usage: %prog [options] IBcontractName'
    parser = OptionParser(usage=usage)
    parser.add_option('-f', '--file', 
                      dest='filename', default=False,
                      help='Write output to FILE', metavar='FILE')
    parser.add_option('-d', '--barsize',
                      choices=list(Broker.rhd_bar_sizes),
                      default='1 day',
                      help='check Broker.rhd_bar_sizes for valid strings', 
                      metavar='BARSIZE')
    parser.add_option('-b', '--begin',
                      default=None,
                      help='set start date', metavar='YYYY/MM/DD HH:MM:SS')
    parser.add_option('-e', '--end',
                      default=datetime.now().strftime(mypy.DATE_TIME_STR),
                      help='set end date', metavar='YYYY/MM/DD HH:MM:SS')
    parser.add_option('-s', '--show',
                      choices=list(Broker.rhd_what_to_show),
                      default='TRADES',
                      help='check Broker.rhd_what_to_show for valid strings',
                      metavar='WHAT_TO_SHOW')
    (opts, args) = parser.parse_args()
    if len(args) != 1:
        print('Missing arguments, use historicaldta.py --help for info')
        return 'wrong number of arguments'
    contract_name = args[0]
    print(opts.end)
    try:
        end_time = mypy.py_date_time(opts.end)
    except ValueError:
        print('end date, wrong format use YYYY/MM/DD HH:MM:SS')
        return
    if opts.begin:
        try:
            start_time = mypy.py_date_time(opts.begin)
        except ValueError:
            print('start date, wrong format use YYYY/MM/DD HH:MM:SS')
            return
    else:
        start_time = None
    try:
        historical_data(contract_name, end_time, start_time, opts.barsize,
                        opts.show, opts.filename)
    except Broker.ContractNotInDB as err:
        print('Contract {} not in db'.format(err))   

def historical_data(contract_name, 
                   end_time = datetime.now(),
                   start_time = None,
                   barsize = '1 day',
                   show = 'TRADES',
                   filename = False,
                   db_PATH = mypy.DB_LOCATION):
    # check and initialise parameters
    broker_contract = Broker.contract_data(contract_name)
    if not start_time:
        start_time = end_time - timedelta(days=32)
        #begin = begin_time.strftime(mypy.DATE_TIME_STR)
    if start_time > end_time:
        raise ArgumentError('end time is before start time')
    if barsize in Broker.rhd_intraday_bar_sizes:
        timeFormat = mypy.iso8601TimeStr
    elif barsize in Broker.rhd_interval_bar_sizes:
        timeFormat = mypy.iso8601TimeStr[:8]
    else:
        raise ArgumentError('Invalid barsize')
    if not filename:
        filename = '.'.join((contract_name, 'db'))
    db_table_name= ' '.join((show, barsize)).replace(' ','_')
    # open or create db and db table
    dbh = mysqlite3.sqlite3_db(filename, db_PATH, create=True)
    if not dbh.table_exists(db_table_name):
        dbh.add_table(db_table_name, sql_IB_db.TABLE_DEF)
    dbh.add_insert_instruction(db_table_name, sql_IB_db.INSERT_INSTR)
    #db_insert_instruction = 'INSERT INTO {0} VALUES (?,?,?,?,?,?,?,?,?)'.format(db_table_name)
    tmpFileName = mypy.temp_file_name()   
    while end_time > start_time:
        # Send historical request to Broker Interface
        BrokerInterface.make_historical_request(broker_contract, end_time, 
                                                barsize, 
                                                Broker.rhd_max_req_period[barsize][0],
                                                whatToShow=show,
                                                filename=tmpFileName,
                                                host= 'localhost',
                                                port=10911)
        # proces historical data
        ioh = open(tmpFileName,'r')
        #first_entry = mypy.py_date_time(ioh.readline().split(',')[0], timeFormat)
        first_entry = mypy.epoch2date_time(int(ioh.readline().split(',')[0]))
        ioh.seek(io.SEEK_SET)
        errors = []
        for line in ioh:
            items = line.split(',')
            #items[0] = mypy.py_time(items[0], timeFormat)
            #items[0]= mypy.date_time2format(mypy.py_date_time(items[0], timeFormat),
            # mypy.iso8601TimeStr)
            try:
                items[0] = mypy.date_time2format(mypy.epoch2date_time(int(items[0])),
                                                mypy.iso8601TimeStr)
                dbh.insert_record(db_table_name, sql_IB_db.Record(*items))
            except ValueError as err:
                errors.append(err)
            #mydbCurs.execute(db_insert_instruction,tuple(items))
            #full_date = mypy.py_time(items[0], timeFormat)
            #print (full_date)
        ioh.close()
        dbh.commit()
        end_time = first_entry
    dbh.close()
    mypy.rmTempFile(tmpFileName) 
    for c, err in enumerate(errors):
        print(c,':',err)
        mypy.get_bool('hit enter', default=True)


if __name__ == '__main__':
    main()
                      
