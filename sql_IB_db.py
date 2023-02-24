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
"""
This module provides acces to the intraday db
"""

#Bestand met functies om intraday sqlite bestand te beheren

import sqlite3
from collections import namedtuple
import mysqlite3
import mypy
import datetime

TABLE_DEF = ('(datetime text UNIQUE ON CONFLICT IGNORE, open real, ' +
             'high real, low real, close real, volume integer, wap real, ' +
             'hasgaps integer, counts integer)')
Record = namedtuple('Record', 'datetime  open high low close '
                              'volume wap hasgaps counts')

INSERT_INSTR = 'INSERT INTO {0} VALUES (?,?,?,?,?,?,?,?,?)'

IB_std_date_str = '%Y-%m-%d'
IB_std_time_str = '%H:%M:%S'
IB_std_datetime_str = ' '.join([IB_std_date_str, IB_std_time_str])
db_date = lambda date_time: date_time[:10]

def _checkdate(date):
    try:
        mypy.py_date(date, IB_std_date_str)
    except ValueError:
        try:
            date = date.replace('/','-')
            mypy.py_date(date, IB_std_date_str)
        except ValueError:
            print('sql_IB_db.py: date in wrong format')
            raise
    return date

def _adjust_date(a_date):
    '''controleert in welk formaat de tijd werd ingevoerd,
    en transformeert gekende formaten naar de standaard string'''
    # Voor datetime datum
    if type(a_date) == datetime.datetime:
        datestr= mypy.datetime2format(a_date, IB_std_date_str)
    else:
        print('onbekend datumformaat in wql_IB_db.py')
        raise
    return datestr

def get_dates(db, table, start=None, stop=None):
    db_open = db.__class__==mysqlite3.sqlite3_db
    req_info = tuple()
    if start and not stop:
        stop = 'date("now")'
    if db_open:
        dbcur = db.cursor
    else:
        mydb = sqlite3.connect(db)
        dbcur = mydb.cursor()
    request = 'SELECT DISTINCT date(datetime) FROM {0}'.format(table)
    if stop:
        request += ' WHERE date(datetime)<=?'
        req_info = (str(stop)[:10],)
    if start:
        request += ' AND date(datetime)>=?'
        req_info += (str(start)[:10],)
    request += ' ORDER BY datetime'
    dbcur.execute(request, req_info)
    dates = [a[0] for a in dbcur.fetchall()]
    if not db_open:
        dbcur.close()
        mydb.close()
    return dates

def get_data_on_date(db, table, date, *fields):
    db_open = db.__class__==mysqlite3.sqlite3_db
    date=_checkdate(date)
    if db_open:
        dbcur = db.cursor
    else:
        mydb = sqlite3.connect(db)
        dbcur = mydb.cursor()
    request='select distinct '+fields[0]
    for field in fields[1:]:
        request += ', '+field
    request += ' from {0} where date(datetime)=? order by datetime'.format(table)  
    
    dbcur.execute(request, (date,))
    data=dbcur.fetchall()
    if not db_open:
        dbcur.close()
        mydb.close()
    return data

def get_price_on_date(db, table, datetime, what=None):
    '''Geeft prijs van db, table op datetime
    ook 'opening' en 'closing' mogelijk als waarden voor datetime'''
    db_open = db.__class__==mysqlite3.sqlite3_db
    if db_open:
        dbcur = db.cursor
    else:
        mydb = sqlite3.connect(db)
        dbcur = mydb.cursor()
    if what == 'closing':
        request = 'SELECT max(datetime) FROM {0} WHERE date(datetime)=?'.format(table)
    if what == 'opening':
        request = 'SELECT min(datetime) FROM {0} WHERE date(datetime)=?'.format(table)
    if what:
        dbcur.execute(request, (datetime,))
        datetime = dbcur.fetchone()[0]
    request = 'SELECT close FROM {0} WHERE datetime=?'.format(table)
    dbcur.execute(request, (datetime,))
    quote = dbcur.fetchone()
    if not db_open:
        dbcur.close()
        mydb.close()
    return quote

def time_first_last_quote_on_date(db, table, a_date):
    '''Geeft een tuple met de tijd van de eerste en de laatste quote op de dag'''
    db_open = db.__class__==mysqlite3.sqlite3_db
    if db_open:
        dbcur = db.cursor
    else:
        mydb  = sqlite3.connect(db)
        dbcur = mydb.cursor()
    db_date = _adjust_date(a_date)
    request = 'SELECT min(datetime) FROM {0} WHERE date(datetime)=?'.format(table)
    dbcur.execute(request, (db_date,))
    time_first_quote = mypy.py_time(dbcur.fetchone()[0], IB_std_datetime_str)
    request = 'SELECT max(datetime) FROM {0} WHERE date(datetime)=?'.format(table)
    dbcur.execute(request, (db_date,))
    time_last_quote = mypy.py_time(dbcur.fetchone()[0], IB_std_datetime_str)
    if not db_open:
        dbcur.close()
        mydb.close()
    return time_first_quote, time_last_quote  
    
def get_closingprice_on_date(db, table, date):
    # For reverse compatibility
    # DEPRICATED!!
    # use: get_price_on_date(db, table, 'closing')
    mydb = sqlite3.connect(db)
    dbcur = mydb.cursor()
    request = 'SELECT max(datetime) FROM {0} WHERE date(datetime)=?'.format(table)
    dbcur.execute(request, (date,))
    last_quote_time = dbcur.fetchone()
    request = 'SELECT close FROM {0} WHERE datetime=?'.format(table)
    dbcur.execute(request, (last_quote_time))
    last_quote = dbcur.fetchone()
    return last_quote
