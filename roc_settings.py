#!/usr/bin/env python3
#
#  Copyright (c) 2014 Rolf Camps (rolf.camps@scarlet.be)

from os.path import join as full_path
import os

S_PARENT_DIR = os.getenv('HOME')
S_DIR_NAME = '.roce'
S_BASE_DIRECTORY_FILE = 'mydir'

class Error(Exception):
    pass

# Find directory for base settings
_settings_base_dir =  full_path(S_PARENT_DIR, S_DIR_NAME)

#
try:
    with open(full_path(_settings_base_dir, S_BASE_DIRECTORY_FILE)) as ipf:
        BASE_DIR = ipf.readline()
except Exception:
    mss = 'Can not find all settings : {}. Run roc_settings.py'
    mss = mss.format(_settings_base_dir)
    if not __name__ == '__main__':
        raise Error(mss)
    
def roce_setup():
    print('Create a directory \'{}\' in {}.'.format(S_DIR_NAME, S_PARENT_DIR))
    roce_basedirectory_setup()
    
def roce_basedirectory_setup():
    print('Make a textfile \'{}\' in  {} with the full path'
          ' to your base directory'.
          format(S_BASE_DIRECTORY_FILE, _settings_base_dir))
        
    
def main():
    if not os.path.isdir(_settings_base_dir):
        roce_setup()
        exit()
    current_base_directory_setting = full_path(_settings_base_dir,
                                               S_BASE_DIRECTORY_FILE)
    if not os.path.isfile(current_base_directory_setting):
        roce_basedirectory_setup()
        exit()
    
    print('Base directory: {}'.format(BASE_DIR))
     

if __name__ == '__main__':
    main()
    
