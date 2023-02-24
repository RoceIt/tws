#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)

'''Standard roce directories.

DATA_LOCATION -- directory for all data
DB_LOCATION -- directory with databases
CSV_DATA_LOCATION -- directory with data in csv format'''

from os.path import join as full_path

from roc_settings import BASE_DIR

DATA_LOCATION = full_path(BASE_DIR, 'Data') # TEST OK
DB_LOCATION = full_path(DATA_LOCATION, 'db') # TEST OK
CSV_DATA_LOCATION = full_path(DATA_LOCATION, 'bigdata') # TEST OK
TMP_LOCATION = full_path('/tmp')

def main():
    print()
    print('roc directories')
    print('===============')
    print()
    print('Data location:', DATA_LOCATION)
    print('Database location:', DB_LOCATION)
    print('CSV data location:', CSV_DATA_LOCATION)
    print('\n\n')
    
if __name__ == '__main__':
    main()
        
    