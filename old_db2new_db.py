#!/usr/bin/env python3

#Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)

import mypy
import mysqlite3
import twsclientapps
import sql_IB_db as old_sql
import sql_ib_db


old_db_file_name = mypy.get_string('old db name: ')
old_db_dir = mypy.get_string('old db dir (roce/data/db): ',
                             default=mypy.DB_LOCATION)
atws_conn = twsclientapps.set_up_tws_connection(interactive=True)
contr =  twsclientapps.select_contract(atws_conn).summary
atws_conn.disconnect()
new_db_filename = sql_ib_db.make_historical_db_name(contr)
old_db = mysqlite3.sqlite3_db(old_db_file_name, old_db_dir)
tablename = mypy.get_string('Table name (TRADES_5_secs): ',
                            default='TRADES_5_secs')
dates = old_sql.get_dates(old_db, tablename)
new_db = sql_ib_db.HistoricalDatabase(new_db_filename,create=True)
new_db.add_table(tablename)
dates = old_sql.get_dates(old_db, tablename)
c_o = mypy.ColumnName('IB_db')
print(dates)
for date in dates[2:]:
    print(date)
    dt = old_sql.get_data_on_date(old_db, tablename, date, 
                                  c_o.datetime, c_o.open, c_o.high, c_o.low, 
                                  c_o.close, c_o.volume, c_o.counts, c_o.wap, 
                                  c_o.hasgaps)
    dt_n = [(a,b,c,d,e,f,int(g),h,i) for a,b,c,d,e,f,g,h,i in dt]
    for line in dt_n:
        new_db.insert_record(tablename, sql_ib_db.Record(*line))
    new_db.commit()