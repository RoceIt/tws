#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#

import market_sim
from marketdata import data_bar_feeder_from_file as feeder
from roc_input import (SelectionMenu, get_datetime, get_string,
                       get_integer)

TESTFILE = '/home/rolcam/roce/Data/bigdata/AEX'

def main():
    menu = top_menu()
    dev_trader = market_sim.DevotedTrader('TestTrader',
                                          feeder(TESTFILE, is_index=True))
    while True:
        print()
        choice = menu.get_users_choice()
        if choice == 'quit':
            break
        choice(dev_trader)
    print('C U')
    
def dump(dt):
    '''dump most dt attributes to screen.'''
    print('\nDEVOTED TRADER DUMP')
    print('===================\n')
    print(dt.name)
    print(dt.info)
    print(dt.datatype)
    print('OPEN ORDERS')
    print(dt.open_orders)
    print('FILLED AND REMOVED ORDERS')
    print(dt.filled_and_removed_orders)
    print('POSITIONS')
    print(dt.positions)
    print('CLOSING AND CLOSED POSITIONS')
    print(dt.closing_and_closed_positions)
    print('\nLAST MOVE: ', dt.last_move)
    print('DATA COUNTER', dt.data_counter)
    print('NEXT DATA')
    print(dt.next_data)
    
def move(dt):
    '''test move'''
    to = get_datetime('move to: ', 
                      '%Y.%m.%d %H.%M.%S', err_message='wrong format')
    dt.move_to(to)
    
def buy_order(dt):
    '''create and send a buy order.'''
    print('\nSet up buy order')
    print('----------------\n')
    timestamp = get_datetime('timestamp: ', 
                             '%Y.%m.%d %H.%M.%S', err_message='wrong format')
    info = get_string('info: ', empty=True)
    quantity = get_integer('number of contracts: ', 
                           minimum=1, lim_message='buy at least 1')
    start = get_datetime('start: ', '%Y.%m.%d %H.%M.%S', empty=True)
    until = get_string('order expires (GTC): ', default='GTC',
                       valid_choices=market_sim.Order.EXPIRE_CODES)
    type_ = get_string('type (MARKET): ', default='market',
                       valid_choices=market_sim.Order.ORDER_TYPES)
    dt.buy(timestamp=timestamp, info=info,
           quantity=quantity, start=start, until=until, type=type_,
           volume_aware=False)
    
def sell_order(dt):
    '''create and send a sell order.'''
    print('\nSet up sell order')
    print('----------------\n')
    timestamp = get_datetime('timestamp: ', 
                             '%Y.%m.%d %H.%M.%S', err_message='wrong format')
    info = get_string('info: ', empty=True)
    quantity = get_integer('number of contracts: ', 
                           minimum=1, lim_message='buy at least 1')
    start = get_datetime('start: ', '%Y.%m.%d %H.%M.%S', empty=True)
    until = get_string('order expires (GTC): ', default='GTC',
                       valid_choices=market_sim.Order.EXPIRE_CODES)
    type_ = get_string('type (MARKET): ', default='market',
                       valid_choices=market_sim.Order.ORDER_TYPES)
    dt.sell(timestamp=timestamp, info=info,
           quantity=quantity, start=start, until=until, type=type_,
           volume_aware=False)    

def check_positions(dt):
    '''check nr of items held by a postion'''
    id_ = get_integer('order id')
    try:
        nr = dt.nr_of_items_held_by_id(dt.positions, id_)
    except market_sim.Error as e:
        nr = 'Error Raised({})'.format(e)
    print('\nitems held by {}: {}'.format(id_, nr))
    
def total_positions(dt):
    '''Print total position.'''
    nr = dt.nr_of_items_held(dt.positions)
    print('\nTotal position: {}'.format(nr))
    
def cancel_order(dt):
    '''Canel the order.'''
    timestamp = get_datetime('timestamp: ', 
                             '%Y.%m.%d %H.%M.%S', err_message='wrong format')
    id_ = get_integer('order id')
    try:
        nr = dt.request_order_cancel(timestamp, id_)
    except market_sim.Error as e:
        nr = 'Error Raised({})'.format(e)
    print('\nitems held by {}: {}'.format(id_, nr))
    
def close_positions(dt):
    '''close postions, no id is all'''
    timestamp = get_datetime('timestamp: ', 
                             '%Y.%m.%d %H.%M.%S', err_message='wrong format')
    id_ = get_integer('order id: (enter is all)', default=0)
    dt.close(timestamp, 'closing instruction', id_)    
    
    
def top_menu():
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',
                         auto_number=True)
    #####
    #
    menu.add_menu_item('Quit', return_value='quit')
    #
    menu.add_menu_item('dump trader atrributes', return_value=dump)
    menu.add_menu_item('Move', return_value=move)
    menu.add_menu_item('buy order', return_value=buy_order)
    menu.add_menu_item('sell order', return_value=sell_order)
    menu.add_menu_item('nr of positions by', return_value=check_positions)
    menu.add_menu_item('cancel order', return_value=cancel_order)
    menu.add_menu_item('nr_of_items_held', return_value=total_positions)
    menu.add_menu_item('close positions', return_value=close_positions)
    #####
    return menu
                                          
if __name__ == '__main__':
    main()
    