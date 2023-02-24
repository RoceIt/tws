#!/usr/bin/python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import glob
import os.path

from collections import namedtuple

import mypy
import tws
from mysqlite3 import *
#this should be integrated in the mysqlite3 module
TABLE_DEF = ('(datetime text UNIQUE ON CONFLICT IGNORE, open real, ' +
             'high real, low real, close real, volume integer, ' +
             'counts integer, wap real, hasgaps integer)')
Record = namedtuple('Record', 'datetime  open high low close '
                              'volume counts wap hasgaps')
INSERT_INSTR = 'INSERT INTO {0} VALUES (?,?,?,?,?,?,?,?,?)'

date_format = mypy.DATE_STR_iso

db_date = lambda date: mypy.datetime2format(date, mypy.DATE_STR_iso)
py_date = lambda date: mypy.py_date(date, mypy.DATE_STR_iso)
py_date_time = lambda date: mypy.py_date_time(date, mypy.iso8601TimeStr)

    
class HistoricalDatabase(DatabaseHandler):
    '''Returns a handler to acces a database with historical data.
    
    The first argument is the  db name.
    The db wil not be created if it doesn't exist, you can set the 'create'
    argument to True if you want it to be created.
    The standard db directory is DB_LOCATION, defined in the mypy module,
    you can change this directory using the db_dir argument name    
    '''
    def __init__(self, db_name, db_dir=mypy.DB_LOCATION, create=False):
        if not db_name.endswith('.db'):
            db_name = '.'.join([db_name, 'db'])
        super().__init__(db_name, db_dir, create)
        for table in self.list_tables():
            self.add_insert_instruction(table, INSERT_INSTR)
            
    def add_table(self, table_name):
        '''Adds a historical db specific table to the db
        
        The name of the table is table_name, the table definition used
        is TABLE_DEF, defined in this module
        '''
        super().add_table(table_name, TABLE_DEF, safe=True)
        self.add_insert_instruction(table_name, INSERT_INSTR)
        
    def get_dates(self, table, start=None, stop=None):
        '''Returns an ordered list with the requested datetime.date's
        
        Keyword arguments:
        start, stop -- datetime or datetime.date format
        
        '''
        request = ['SELECT DISTINCT date(datetime) FROM {0}'.format(table)]
        request_info = []
        if start:
            request.append('WHERE date(datetime) >=?')
            request_info.append(db_date(start))
        if stop:
            request.append('AND' if start else 'WHERE')
            request.append('date(datetime) <=?')
            request_info.append(db_date(stop))
        request.append('ORDER BY date(datetime)')
        request = ' '.join(request)
        request_info = tuple(request_info)
        self.execute(request, request_info)
        dates = [py_date(d[0]) for d in self.answer]
        return dates
    
    def get_data_on_date(self, table, date, *fields):
        answer = namedtuple('answer', ' '.join(fields))
        request=['select distinct']
        request.append(','.join(fields))
        request.append('from {0} where date(datetime)=? order by datetime'
                       .format(table))  
        request = ' '.join(request)
        self.execute(request, (db_date(date),))
        data = [list(record) for record in self.answer]
        if 'datetime' in fields:
            position = fields.index('datetime')
            for record in data:
                record[position] = py_date_time(record[position])
        data = [answer(*record) for record in data]
        return data
    
    def first_entry_date_time(self, table):
        '''returns a datetime that holds the oldest date & time in the db
        '''
        timestring = self.lowest_value_in(table, 'datetime')
        return py_date_time(timestring)
    
    def last_entry_date_time(self, table):
        '''returns a datetime that holds the most recent date & time in the db
        '''
        timestring = self.highest_value_in(table, 'datetime')
        return py_date_time(timestring)
    
    def data_stream(self, table, *fields, start=None, stop=None):
        '''return a generator for chronological historical data
        
        start and date must be dates'''
        dates = self.get_dates(table, start, stop)
        for date in dates:
            day_data = self.get_data_on_date(table, date, *fields)
            for line in day_data:
                yield line
        
    
    
def make_historical_db_name(contract):
    
    assert isinstance(contract, tws.contract), contract
    ell = [contract.symbol.upper()]
    ell.append(contract.secType)
    if contract.right in ['C', 'P']:
        ell.append('{}_{}'.format(contract.right, contract.strike))
    if contract.multiplier:
        ell.append('X{}'.format(contract.multiplier))
    if contract.expiry:
        ell.append(contract.expiry)
    ell.append(contract.currency)
    ell.append('{}@{}'.format(contract.localSymbol,contract.exchange))
    return '.'.join([' '.join(ell),'db'])

def make_table_name(show, barsize):
    
    return ' '.join((show, barsize)).replace(' ','_')


def select_db(symbol='', secType='', right='', strike='', multiplier='', 
              expiry='', currency='', localsymbol='', exchange='',
              db_dir=mypy.DB_LOCATION):
    '''returns a list of db's that match the parameters'''
    look_up = [symbol if symbol else '*']
    look_up.append(' {}'.format(secType) if secType else '*')
    look_up.append(' {}_'.format(right) if right else '*')
    look_up.append('_{}'.format(strike) if strike else '*')
    look_up.append(' X{}'.format(multiplier) if multiplier else '*')
    look_up.append(' {}'.format(expiry) if expiry else '*')
    look_up.append(' {}'.format(currency) if currency else '*')
    look_up.append(' {}@'.format(localsymbol) if expiry else '*')
    look_up.append('@{}'.format(exchange) if currency else '*')
    look_up.append('.db')
    for count in range(len(look_up)-1):
        if look_up[count] == '*' and look_up[count+1] == '*':
            look_up[count] = ''
        if look_up[2].endswith('_') and look_up[3].startswith('_'):
            look_up[2].pop()
        if look_up[7].endswith('_') and look_up[8].startswith('_'):
            look_up[7].pop()
    look_up_glob = os.path.join(db_dir, ''.join(look_up))
    db_list = [os.path.basename(x) for x in glob.glob(look_up_glob)]
    return db_list

def i_select_db(symbol='', secType='', right='', strike='', multiplier='', 
                expiry='', currency='', localsymbol='', exchange='', 
                db_dir=mypy.DB_LOCATION,
                message='Select database', confirm=True, empty=False):
    if message:
        print(message)
    found_dbs = select_db(symbol, secType, right, strike, multiplier,
                          expiry, currency, db_dir)
    found_dbs = [x.split() for x in found_dbs]
    selecting = 'Symbol name'
    for selector in range(6):
        options = {x[selector] for x in found_dbs}
        if selecting == 'Local@Market':
            options = {x.split('.')[0] for x in options}
        if len(options) > 1:
            choice = mypy.get_from_list(sorted(options),
                                       'select {}: '.format(selecting.lower()),
                                       empty=True)
        else:
            choice = options.pop()
        if selecting == 'Local@Market':
            choice += '.db'
        print('{}: {}'.format(selecting, choice))
        found_dbs = [x for x in found_dbs if x[selector] == choice]
        if len(found_dbs) == 1:
            break
        if selecting == 'Symbol name':
            selecting = 'Security type'
        elif selecting == 'Security type':
            curr_sec_type = found_dbs[0][1]
            if curr_sec_type == 'OPT':
                selecting = 'Right@strike'
            elif curr_sec_type == 'FUT':
                selecting = 'Multiplier'
            else:
                selecting = 'Currency'
        elif selecting == 'Right@strike':
            selecting = 'Multiplier'
        elif selecting == 'Multiplier':
            selecting = 'Expiry'
        elif selecting == 'Expiry':
            selecting = 'Currency'
        elif selecting == 'Currency':
            selecting = 'Local@Market'
        else:
            raise Exception('HDIGH?')
    db_name = ' '.join(found_dbs[0]) if found_dbs else None
    if confirm and not db_name:
        confirmed = mypy.get_bool('No selection made! Continue(Y/n)? ', 
                                default=True)
    elif confirm:
        print('Please confirm following selection:')
        confirmed = mypy.get_bool('{}  (Y/n)? '.format(db_name) , default=True)
    if not confirmed:
        return i_select_db(symbol, secType, right, strike, multiplier,
                           expiry, currency, db_dir, message)
    else:
        return db_name
              
            
    
    
    

    