#!/usr/bin/env python3
#
#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)


import os.path
import csv
from datetime import datetime
from collections import Iterable

import mypy

def table2csv(table, columns=[], file_name=None, dir_=mypy.TMP_LOCATION,
              date_time_conversion=mypy.iso8601TimeStr, dialect=None):
    """
    writes a table (or list) to a csv file, returns the full path to the file
    
    you can select columns or the order the coluns by setting the columns
    """
    
    if not file_name:
        file_name = mypy.temp_file_name(directory=dir_)
    else:
        file_name = os.path.join(dir_, file_name)
    
    if columns:
        csv_data = []
        for line in table:
            csv_data.append([line[col] for col in columns])
    else:
        csv_data = table
        
    #for col_nr, ell in csv_data[0]:
        #if isinstance(ell, datetime):
            
        
    print('data = {}'.format(csv_data))
    with open(file_name, 'w') as ofh:
        csvh=csv.writer(ofh, dialect=dialect)
        if isinstance(csv_data[0], Iterable):
            csvh.writerows(csv_data)
        else:
            csvh.writerows([list((x,)) for x in csv_data])
        
    return file_name

    for line in table:
        if not columns == 'ALL':
            line = [line[col] for col in columns]
        csvh.writerow(line)
    return filename