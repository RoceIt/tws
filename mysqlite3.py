#!/usr/bin/python3
#
#  Copyright (c) 2010, 2011 Rolf Camps (rolf.camps@scarlet.be)


''' module for easy sqlite3 db handling'''

import os.path
import sqlite3

from collections import namedtuple

import mypy

#####
# Define exceptions
#####
class MySqliteError(Exception): pass
class DbExistError(MySqliteError): pass
class DBNotFound(MySqliteError): pass
class TableNotFound(MySqliteError): pass
class InsertRecordError(MySqliteError): pass

ColumnDef = namedtuple('ColumnDef', 'name type')

def create_db(dbname, db_dir=mypy.DB_LOCATION, table=None, tableFormat=None):
    db_path = os.path.join(db_dir, dbname)
    if os.path.exists(db_path):
        raise(DbExistError)
    else:
        open(db_path, 'w').close()
        if table:
            db = sqlite3_db(dbname, db_dir)
            db.add_table(table, tableFormat, safe=False)
            db.close()

class sqlite3_db():
    '''Gives an instance of a sqlite3 db, stays open until closed'''
    # zou zo gemaakt kunnen worden dat je een with ... as statement kan gebruiken
    # daarvoor moeten dan 2 nieuwe funcies gecreëerd worden, __exit__ en nog een?
    def __init__(self, db_name, db_dir=mypy.DB_LOCATION, create=False):
        db_path = os.path.join(db_dir, db_name)
        if not os.path.exists(db_path):
            if create:
                create_db(db_name, db_dir)
            else:
                raise DBNotFound('db doesn\'t exist')
        self.db = sqlite3.connect(db_path)
        self.cursor = self.db.cursor()
        self.insert_instr = {}
        
    def add_insert_instruction(self, table, instr):
        self.insert_instr[table] = instr.format(table)

    def commit(self):
        self.db.commit()

    def execute(self, instr, parameter_tuple=(), commit=False):
        self.cursor.execute(instr, parameter_tuple)
        if commit:
            self.commit()
            
    @property
    def answer(self):
        return self.cursor.fetchall()

    def close(self):
        self.commit()
        self.cursor.close()
        self.db.close()
        self.db = self.cursor = None

    def add_table(self, table_name, table_format, safe=False):
        '''Adds a table with table_format structure to the db
        
        The name is the table name, the table_format must be the string sqlite
        excpects for the table definition.
        The function will not check if de table allready exists, you can enable
        this by setting 'safe' to True
        '''        
        instr_ = {False: 'CREATE TABLE {0} {1}',
                  True: 'CREATE TABLE IF NOT EXISTS {0} {1}'
                  }
        instr = instr_[safe]
        self.execute(instr.format(table_name, table_format), commit=True)
        
    def list_tables(self):
        instr = 'SELECT name FROM sqlite_master WHERE type=\'table\''
        self.execute(instr, commit=True)
        return [x[0] for x in self.answer]

    def table_exists(self, table_name):
        '''Returns True if table_name exists else False'''
        instr = 'SELECT name FROM sqlite_master WHERE type=\'table\' and name=?'
        self.execute(instr, (table_name,))
        if self.answer:
            return True
        return False
    
    def list_columns(self, table_name):
        '''Returns a list of ColumnDef's.
        
        A ColumnDef is a namedtuple: (name, type)
        
        '''
        instr = 'PRAGMA table_info({})'.format(table_name)
        self.execute(instr)
        info = [ColumnDef(r[1], r[2]) for r in self.answer]        
        return info
    
    def insert_record(self, table_name, record, commit=False):
        '''Insert the record in the db table.
        
        The table written to is defined in table_name.
        The record must be a tupple with the fields of the tabel definition in
        the right order. The insert instruction must be added with the
        add_insert_instruction before you can use this function.
        The insert will not be automatically committed unless you set commit
        to True.
        
        '''
        try:
            instr = self.insert_instr[table_name]
        except KeyError:
            mess = 'No insert instruction for {}'.format(table_name)
            raise InsertRecordError(mess)
        self.execute(instr, record)
        if commit:
            self.commit()
            
    def highest_value_in(self, table, field):
        '''returns the highest value in the requested field of table'''
        if self.table_exists(table):
            instr = 'SELECT max({}) FROM {}'.format(field, table)
            self.execute(instr)
        else:
            raise TableNotFound(table)
        return self.answer[0][0]
            
    def lowest_value_in(self, table, field):
        '''returns the lowest value in the requested field of table'''
        if self.table_exists(table):
            instr = 'SELECT min({}) FROM {}'.format(field, table)
            self.execute(instr)
        else:
            raise TableNotFound(table)
        return self.answer[0][0]
            
    def get_tablename(self, message=None, empty=True):
        '''returns an existing tablename or none if allowed'''
        if message == None:
            message = 'Select table: '
        tables = self.list_tables()
        choice = mypy.get_from_list(tables, message, empty)
        print(choice)
        return choice        
        #while True:
            #name = mypy.get_string(message, empty=empty)
            #if name == '.s':
                #print('in .s')
                #mypy.print_list(tables, 'TABLES')
                #continue
            #elif name == '' and empty:
                #name = None
                #break
            #elif self.table_exists(name):
                #break
            #print('table name unknown! type \'.s\' for a list')
        #return name
    

DatabaseHandler = sqlite3_db