#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)
import csv

import mypy
import tws
import sql_ib_db as db_manager

def main():
    start_date = mypy.get_date('start date (YYYY/MM/DD): ')
    end_date = mypy.get_date('end date (empy for end of data): ', empty=True)
    major_contr_name = db_manager.i_select_db(message='major contract: ')
    major_db = db_manager.HistoricalDatabase(major_contr_name)
    major_table_name = major_db.get_tablename()
    major_columns = get_columns_to_show(major_db, major_table_name)
    major_db.close()
    major_columns = major_columns
    major_contr_info = (major_contr_name, major_table_name, major_columns)
    minor_contr_info = []
    while mypy.get_bool('\n\nAdd minor contract (Y/n): ', default=True):
        mess = 'minor contract {}: '.format(len(minor_contr_info)+1)
        minor_contr_name = db_manager.i_select_db(message=mess, empty=True)
        if not minor_contr_name:
            break
        minor_db = db_manager.HistoricalDatabase(minor_contr_name)
        minor_table_name = minor_db.get_tablename()
        minor_columns = get_columns_to_show(minor_db, minor_table_name)
        minor_contr_info.append((minor_contr_name, minor_table_name,
                                 minor_columns))
        minor_db.close()
    convert(major_contr_info, minor_contr_info, start_date, end_date)
    
    
def get_columns_to_show(db, table_name):
    '''Let the user choose valid columnnames from contract>table.'''
    columns = []
    valid_column_names = [r.name for r in db.list_columns(table_name)]
    valid_column_names.remove('datetime')
    valid_column_names.append('DONE')
    while len(valid_column_names) > 1:
        column = mypy.get_from_list(valid_column_names)
        if column == 'DONE':
            break
        columns.append(column)
        valid_column_names.remove(column)
    return columns

def convert(major_contr_info, minor_contr_info, 
            start_date, end_date, 
            output_file='ibhist2cvs.out'):
    key = 'datetime'
    db_list = []
    column_names = [key]
    for name, table, columns in [major_contr_info] + minor_contr_info:
        db_list.append(dict(db_name=name,
                            db=db_manager.HistoricalDatabase(name),
                            table=table, columns=[key] + columns))
        for column in columns:
            column_names.append('>'.join([name, table, column]))        
    date_range = db_list[0]['db'].get_dates(db_list[0]['table'],
                                            start_date, end_date)
    csv_out = csv.writer(open(output_file, 'w'))
    csv_out.writerow(column_names)    
    for date in date_range:
        print('starting {}'.format(date))
        data = []
        for db in db_list:
            info = db['db'].get_data_on_date(db['table'], date, *db['columns'])
            if data:
                info = {row[0]: row[1:] for row in info}
            data.append(info)
        for row in data[0]:
            selector = row[0]
            output = row
            for set_nr, data_set in enumerate(data[1:]):
                try:
                    minor_data = data_set[selector]
                except KeyError:
                    minor_data = tuple(0 for x in range(
                                     len(minor_contr_info[set_nr][2])))
                output += minor_data                                   
            #try:
                #for data_dict in data[1:]:
                    #output += data_dict[selector]
            #except KeyError:
                #continue        
            csv_out.writerow(output)
            
if __name__ == '__main__':
    main()
