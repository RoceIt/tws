#!/usr/bin/env python3

#  Copyright (c) 2012 Rolf Camps (rolf.camps@scarlet.be)

import mypy
import mysqlite3

import sql_ib_db as db_manager

def main():
    major_contr_name = db_manager.i_select_db(message='major contract: ') 
    major_db = db_manager.HistoricalDatabase(major_contr_name)
    major_table_name = major_db.get_tablename()
    to_db_name = mypy.get_string('export db: ')
    to_table_name = mypy.get_string('export table: ')
    exp_db = db_manager.HistoricalDatabase(to_db_name, mypy.TMP_LOCATION, create=True)
    if not exp_db.table_exists(to_table_name):
        exp_db.add_table(to_table_name)
    cur = major_db.cursor
    request = 'select * from {} order by datetime'.format(major_table_name)
    cur.execute(request)
    count = 0
    flag = False
    for d in cur:
        try:
            tup = (d[0], #mypy.py_date_time(d[0], mypy.iso8601TimeStr), 
                   d[1], d[2], d[3], d[4], d[5], int(d[8].strip()), d[6], d[7])
        except:
            print('!!! {} ***'.format(d))
            flag = True
            #continue
        else:
            count += 1
            exp_db.insert_record(to_table_name, db_manager.Record(*tup))
            if count == 1000:
                exp_db.commit()
                count = 0
                print(tup[0])
            if flag:
                print(tup)
                flag = False
    exp_db.commit()
    exp_db.close()
            
    

if __name__ == '__main__':
    main()
    