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
This module creates and give acces to a db with time ofsets to
create fluid charts. These times make the graphs fluid (without time
gaps)
"""

#######################################################################
# helper om te debuggen,
# daar heeft python3 zeker en vast een betere oplossing voor ;)
verbose = True
def vprint(message):
    if verbose:
        print(message)
#######################################################################

import os.path
import mypy
import mysqlite3
import sql_IB_db
import tws

CHART_TIME_TABLE = '(datetime text UNIQUE ON CONFLICT REPLACE, offset integer)'
SQL_INSERT_CHART_TIME = 'INSERT INTO chart_time VALUES (?,?)'
SQL_SELECT_MAX_DATE_BEFORE = 'SELECT max(datetime) FROM chart_time WHERE datetime <= ?'
SQL_SELECT_MIN_DATE_AFTER  = 'SELECT min(datetime) FROM chart_time WHERE datetime > ?'
SQL_SELECT_OFFSET_ON = 'SELECT offset FROM chart_time WHERE datetime = ?'

column = mypy.ColumnName('IB_db') 

def make_chart_time_db(IBcontractName, type_of_data, barsize, db_dir=mypy.DB_LOCATION):
    input_db_name = IBcontractName+'.db'
    output_db_name = IBcontractName+'_ct.db'
    table = type_of_data+'_'+barsize.replace(' ','_')
    vprint(table)
    max_data_gap = tws.rhd_max_req_period[barsize][1]
    vprint(max_data_gap)
    if not os.path.exists(os.path.join(db_dir, input_db_name)):
        print('geen db beschikbaar voor deze contractnaam')
        raise
    else:
        # zoek allereerste tijd
        input_db = mysqlite3.sqlite3_db(input_db_name, db_dir)
        sql_instruction = 'SELECT min(datetime) from {}'.format(table)
        input_db.cursor.execute(sql_instruction)     
        first_time = input_db.cursor.fetchone()[0]
        input_db.close()
        # schrijf allereerste tijd naar db met offset 0
        mysqlite3.create_db(output_db_name, 'chart_time', CHART_TIME_TABLE, db_dir)
        output_db = mysqlite3.sqlite3_db(output_db_name, db_dir)
        output_db.cursor.execute(SQL_INSERT_CHART_TIME, (first_time, 0))
        output_db.close()
        # vul db verder aan
        update_chart_time_db(IBcontractName, type_of_data, barsize, db_dir=mypy.DB_LOCATION)

def update_chart_time_db(IBcontractName, type_of_data, barsize, db_dir=mypy.DB_LOCATION):
    input_db_name = IBcontractName+'.db'
    output_db_name = IBcontractName+'_ct.db'
    table = type_of_data+'_'+barsize.replace(' ','_')
    max_data_gap = tws.rhd_max_req_period[barsize][1]
    print('mds=', max_data_gap.seconds)
    if not os.path.exists(os.path.join(db_dir, output_db_name)):
        print('chart time db niet beschikbaar voor deze contractnaam')
        raise
    else:
        input_db = mysqlite3.sqlite3_db(input_db_name, db_dir)   
        output_db = mysqlite3.sqlite3_db(output_db_name, db_dir)
        # zoek tijd van laatste offset
        sql_instruction = 'SELECT max(datetime) from chart_time'
        output_db.cursor.execute(sql_instruction)
        last_offset_time = output_db.cursor.fetchone()[0]
        # zoek waarde laatste offset
        sql_instruction = 'SELECT offset FROM chart_time WHERE datetime=?'
        output_db.cursor.execute(sql_instruction, (last_offset_time,))
        last_offset = output_db.cursor.fetchone()[0]
        offset_time = mypy.py_date_time(last_offset_time, mypy.iso8601TimeStr)
        vprint(offset_time)
        vprint(last_offset)
        date_list = sql_IB_db.get_dates(input_db, table, 
                                        sql_IB_db.db_date(last_offset_time))
        vprint(date_list[0]+' '+date_list[-1])
        previous_datetime = offset_time
        print(type(previous_datetime), type(offset_time))
        print(previous_datetime, offset_time)
        for date in date_list:
            tlist = sql_IB_db.get_data_on_date(input_db, table,
                                               date,
                                               column.datetime)
            py_tlist = [mypy.py_date_time(t[0] , mypy.iso8601TimeStr) for t in tlist]
            for a_time in py_tlist:
                timediff = a_time - previous_datetime
                #print(a_time, timediff.seconds)
                if timediff.seconds > 0:
                    if a_time.day != previous_datetime.day:
                        offset_day = previous_datetime - offset_time
                        new_offset = offset_day.seconds + last_offset +1
                        output_db.cursor.execute(SQL_INSERT_CHART_TIME, (a_time, new_offset))
                        output_db.commit()
                        #print(a_time, new_offset)
                        last_offset = new_offset
                        offset_time = a_time                        
                        previous_datetime = a_time 
                    elif timediff.seconds <= max_data_gap.seconds:
                        previous_datetime = a_time
                    else:
                        offset_day = previous_datetime - offset_time
                        new_offset = offset_day.seconds + last_offset +1
                        output_db.cursor.execute(SQL_INSERT_CHART_TIME, (a_time, new_offset))
                        output_db.commit()
                        #print(a_time, new_offset)
                        last_offset = new_offset
                        offset_time = a_time                        
                        previous_datetime = a_time
            
        #    print(date)        
        #print(tlist[-1])
        #print(last_offset_time)
        input_db.close()
        output_db.close()        

class chart_time_feeder():
    ##########
    #  class die een toegang tot een charttime db open houdt en
    #  toegankelijk maakt
    ##########
    def __init__(self, IBcontractName, db_dir=mypy.DB_LOCATION):
        db_name = IBcontractName+'_ct.db'
        if not os.path.exists(os.path.join(db_dir, db_name)):
            print('geen db beschikbaar voor deze contractnaam')
            raise
        self.db = mysqlite3.sqlite3_db(db_name, db_dir)
        self.last_query = self.next_query = self.last_offset = None

    def offset_for(self, a_date):
        if not(self.last_query and \
                   (a_date >= self.last_query) and \
                   (not self.next_query or a_date < self.next_query )):
            self.db.cursor.execute(SQL_SELECT_MAX_DATE_BEFORE, 
                                   (str(a_date),))
            last_query = self.db.cursor.fetchone()[0]
            self.db.cursor.execute(SQL_SELECT_MIN_DATE_AFTER,
                                   (last_query,))
            next_query = self.db.cursor.fetchone()[0]
            self.db.cursor.execute(SQL_SELECT_OFFSET_ON,
                                   (last_query,))
            self.last_offset = self.db.cursor.fetchone()[0]
            print('***',last_query, next_query, self.last_offset)
            self.last_query = mypy.py_date_time(last_query, mypy.iso8601TimeStr)
            self.next_query = mypy.py_date_time(next_query, mypy.iso8601TimeStr) if \
                next_query else None
        return self.last_offset

    def symbol_chart_time(self, a_date):
        self.offset_for(a_date)
        return self.last_offset + (a_date - self.last_query).seconds
            
    def close(self):
        self.db.close()
