#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
from datetime import datetime

from marketdata import data_bar_feeder_from_file as feeder, data_bar_feeder as dbfeeder
from roc_input import SelectionMenu, get_integer, get_bool, get_time, get_float, get_string
from mypy import export_pickle

def main():
    menu = top_menu()
    while True:
        print()
        choice = menu.get_users_choice()
        if choice == 'quit':
            break
        data_in = get_string('input name: ')
        data_out = get_string('export to: ')
        choice(data_in, data_out)
        #dev_trader = market_sim.DevotedTrader('TestTrader',
                                              #feeder(TESTFILE, is_index=True))
        #dev_trader = market_sim.DevotedTrader('TestTrader',
                                              #dbfeeder(TESTFILE, is_index=True))
        #choice(dev_trader)
    print('C U')
    
def db2pickle(data_in, data_out):
    in_format = db_menu().get_users_choice()
    if in_format == 'sql_ib_db, trades, 5 seconds':
        feeder =  dbfeeder(data_in)
    print('start', datetime.now())
    d = [x for x in feeder]
    print('end', datetime.now())
    print('exporting pickle')
    export_pickle(d, data_out, 'serial databars')
    print('finished: ', datetime.now())
    
    
def top_menu():
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',)
    #####
    #
    menu.add_menu_item('Quit', 'Q', return_value='quit')
    #
    menu.add_menu_item('db --> pickle', 's', return_value=db2pickle)
    #####
    return menu

def db_menu():
    menu = SelectionMenu(
        interface='TXT_ROW',
        message='Select DB type: ',
        auto_number=True,
    )
    menu.add_menu_item('sql_ib_db, trades, 5 seconds')
    return menu

if __name__ == '__main__':
    main()