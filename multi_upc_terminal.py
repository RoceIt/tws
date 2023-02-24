#!/usr/bin/env python3

#  FILENAME: multi_upc_terminal.py

#  Copyright (c) 2011 Rolf Camps (rolf.camps@scarlet.be)

import sys
import os.path

import mypy
import option_analysis


UnderlyingPutCall = option_analysis.UnderlyingPutCall



def main():
    if len(sys.argv) == 1:
        terminal('mu')
    else:
        mess = 'version with parameter not yet available'
        raise NotImplementedError(mess)
    
def terminal_menu():
    menu = mypy.SelectionMenu()
    menu.add_menu_item('List combos', 'L', list_combos)
    menu.add_menu_item('Quit', 'q')
    return menu
    
def terminal(base_file_name):
    menu = terminal_menu()
    info_file_name = os.path.join(
                        mypy.TMP_LOCATION, '.'.join([base_file_name, 'info']))
    upc_list = mypy.import_pickle(info_file_name)
    choice = menu.get_users_choice()
    print(choice)
    
def list_combos():
    print('a listing')
        
    
    
    
if __name__ == '__main__':
    main()