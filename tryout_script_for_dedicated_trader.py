#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
import datetime

from mypy import import_pickle
import market_sim
#from marketdata import data_bar_feeder_from_file as feeder, data_bar_feeder as dbfeeder
from marketdata import data_bar_feeder as dbfeeder
from roc_input import SelectionMenu, get_integer, get_bool, get_time, get_float
#TESTFILE = '/home/rolcam/roce/Data/bigdata/AEX'
#TESTFILE = '/tmp/d.db'
TESTFILE = import_pickle('/tmp/d.ser', 'serial databars')

def main():
    menu = top_menu()
    while True:
        print()
        choice = menu.get_users_choice()
        if choice == 'quit':
            break
        #dev_trader = market_sim.DevotedTrader('TestTrader',
                                              #feeder(TESTFILE, is_index=True))
        dev_trader = market_sim.DevotedTrader('TestTrader',
                                              dbfeeder(TESTFILE, is_index=True))
        choice(dev_trader)
    print('C U')
    
def stream_all_data(dev_trader):
    print('Not implemented.')
    return

def day_intra_day(dev_trader):
    '''model for daily settings
    
    You can use this to set opens or previous close.
    base model:
    
        old_date = None
        for bar in feeder(TESTFILE, is_index=BOOL):
            date = bar.time.date()
            if not date == old_date:
                < Code is ran first time and intraday >
                old_date = date
            < Code is ran during day >
    
    '''
    
    menu = day_and_intraday_menu()
    print()
    choice = menu.get_users_choice()
    choice(dev_trader)
        
def olis_gap(dev_trader):
    chase_gap = get_integer('start chasing when gap >? ', minimum=1)
    last_entry = get_time('last entry (h:m:s): ', '%H:%M:%S')
    last_exit = get_time('last exit: ', '%H:%M:%S')
    old_date = None
    previous_bar = None
    previous_close = None
    gain = loss= 0
    with open('/tmp/tryout', 'w') as of:
        for bar in dbfeeder(TESTFILE, is_index=True):
            date = bar.time.date()
            if not date == old_date:
                # Code is ran first time and intraday
                traded_today = False
                print(date)
                if previous_bar:
                    previous_close = previous_bar.close
                else:
                    get_bool('First time in can not set close.', default=True)
                old_date = date
            # Code is ran during day
            in_trade = dev_trader.in_trade_at(bar.time)
            timestamp = dev_trader.advance_timestamp_for_one_request(bar.time)
            if (not traded_today and
                not in_trade and
                bar.time.time() <= last_entry and
                previous_close is not None):
                if bar.high - previous_close > chase_gap:
                    #get_bool('{}|{}'.format(bar.high, previous_close), default=True)
                    print('\n>>>>>>>>  ',timestamp, '  >>>>>>>>')         
                    dev_trader.sell(
                        timestamp=timestamp,
                        info='ok',
                        quantity=1,
                        start=None,
                        until='GTC',
                        type='market',
                        volume_aware=False,
                        )
                    traded_today = True
                    profit_taker = previous_close
            elif (in_trade and
                  bar.high - dev_trader.avg_in() > 1 * chase_gap):
                dev_trader.close(timestamp, 'loss', 0)
                loss += 1
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' | ', loss, file=of)
            elif (in_trade and
                  bar.low - profit_taker < 0):
                dev_trader.close(timestamp, 'gain', 0)
                gain += 1
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' G|L ', loss, file=of, flush=True)
                #traded_today = False
            elif (in_trade and
                  bar.time.time() >= last_exit):
                dev_trader.close(timestamp, 'to late', 0)    
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' G|L ', loss, file=of, flush=True)
            previous_bar = bar
    dev_trader.pickle_order_lists()
        
def olis_gap_trail_out(dev_trader):
    #1# make these changes, if faulty, goes overnight but is almost
    #   positive!!
    chase_gap = get_integer('start chasing when gap >? ', minimum=1)
    pl_ratio = get_float('profit/loss ratio: ', minimum=0.1)
    last_entry = get_time('last entry (h:m:s): ', '%H:%M:%S')
    trail_exit = get_time('trail exit from: ', '%H:%M:%S')
    last_exit = get_time('last exit: ', '%H:%M:%S')
    old_date = None
    previous_bar = None
    previous_close = None
    trailing = forced = False
    gain = loss= 0
    with open('/tmp/tryout', 'w') as of:
        for bar in dbfeeder(TESTFILE, is_index=True):
            date = bar.time.date()
            if not date == old_date:
                # Code is ran first time and intraday
                traded_today = False
                print(date)
                if previous_bar:
                    previous_close = previous_bar.close
                else:
                    get_bool('First time in can not set close.', default=True)
                old_date = date
            # Code is ran during day
            in_trade = dev_trader.in_trade_at(bar.time)
            timestamp = dev_trader.advance_timestamp_for_one_request(bar.time)
            if (not traded_today and
                not in_trade and
                bar.time.time() <= last_entry and
                previous_close is not None):
                if bar.high - previous_close > chase_gap:
                    #get_bool('{}|{}'.format(bar.high, previous_close), default=True)
                    print('\n>>>>>>>>  ',timestamp, '  >>>>>>>>')         
                    dev_trader.sell(
                        timestamp=timestamp,
                        info='ok',
                        quantity=1,
                        start=None,
                        until='GTC',
                        type='market',
                        volume_aware=False,
                        )
                    traded_today = True
                    profit_taker = previous_close
                    trailing = forced = False
            if in_trade:
                if trailing:
                    stop = trailing
                else:
                    #1# stop = dev_trader.avg_in()
                    stop = dev_trader.avg_in() + pl_ratio * chase_gap
            if (in_trade and
                bar.high > stop ): #1# bar.high - stop > pl_ratio * chase_gap
                if (trailing and not forced):
                    dev_trader.close(timestamp, 'gain', 0)
                    gain += 1
                    #traded_today = False
                elif trailing:                    
                    dev_trader.close(timestamp, 'forced trailing', 0)
                else:
                    dev_trader.close(timestamp, 'loss', 0)
                    loss +=1
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' | ', loss, file=of)
            elif (in_trade and
                  bar.low - profit_taker < 0):
                print('TRAILING  ', timestamp, 'TRAILING\n')
                trailing = profit_taker = bar.high
            elif (in_trade and
                  not forced and #1# remove this line
                  bar.time.time() >= trail_exit):
                print('T EXIT  ', timestamp, 'T EXIT\n')
                trailing = profit_taker = bar.high
                forced = True
            elif (in_trade and
                  bar.time.time() >= last_exit):
                dev_trader.close(timestamp, 'to late', 0)    
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' G|L ', loss, file=of, flush=True)
            previous_bar = bar
    dev_trader.pickle_order_lists()
        
def olis_gap_trail_2(dev_trader):
    chase_gap = get_float('start chasing when gap >? ', minimum=0.1)
    perc_chase_gap = get_bool('percentage {}: ', default=False)
    perc_chase_gap = chase_gap if perc_chase_gap else False
    print('p gap: ', perc_chase_gap)
    pl_ratio = get_float('profit/loss ratio: ', minimum=0.1)
    last_entry = get_time('last entry (h:m:s): ', '%H:%M:%S')
    old_date = None
    previous_bar = None
    previous_close = None
    trailing = forced = False
    gain = loss= profit_taker= 0
    if perc_chase_gap:
        get_bool('Percentage!!', default=True)
    with open('/tmp/tryout', 'w') as of:
        #for bar in feeder(TESTFILE, is_index=True):
        for bar in dbfeeder(TESTFILE, is_index=True):
            date = bar.time.date()
            if not date == old_date:
                # Code is ran first time and intraday
                traded_today = False
                print(date)
                if previous_bar:
                    previous_close = previous_bar.close
                else:
                    get_bool('First time in can not set close.', default=True)
                old_date = date
                if perc_chase_gap:
                    chase_gap = bar.open_ * perc_chase_gap / 100
            # Code is ran during day
            in_trade = dev_trader.in_trade_at(bar.time)
            timestamp = dev_trader.advance_timestamp_for_one_request(bar.time)
            if (not traded_today and
                not in_trade and
                bar.time.time() <= last_entry and
                previous_close is not None):
                if bar.high - previous_close > chase_gap:
                    #get_bool('{}|{}'.format(bar.high, previous_close), default=True)
                    print('\n>>>>>>>>  ',timestamp, '  >>>>>>>>')         
                    dev_trader.sell(
                        timestamp=timestamp,
                        info='ok',
                        quantity=1,
                        start=None,
                        until='GTC',
                        type='market',
                        volume_aware=False,
                        )
                    traded_today = True
                    #profit_taker = previous_close
                    trailing = forced = False
            if in_trade:
                if profit_taker == 0:
                    profit_taker = dev_trader.avg_in() - chase_gap
                if trailing:
                    stop = trailing
                else:
                    stop = dev_trader.avg_in()# + 1 / pl_ratio * chase_gap
            if (in_trade and
                bar.high > stop + 1 / pl_ratio * chase_gap):
                if (trailing and not forced):
                    dev_trader.close(timestamp, 'gain', 0)
                    gain += 1
                    #traded_today = False
                elif trailing:                    
                    dev_trader.close(timestamp, 'forced trailing', 0)
                else:
                    dev_trader.close(timestamp, 'loss', 0)
                    loss +=1
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' | ', loss, file=of)
                profit_taker = 0
            elif (in_trade and
                  bar.low - profit_taker < 0):
                print('TRAILING  ', timestamp, 'TRAILING\n')
                trailing = profit_taker = bar.high
            previous_bar = bar
    dev_trader.pickle_order_lists()
        
def olis_gap_trail_2_up(dev_trader):
    chase_gap = get_float('start chasing when gap >? ', minimum=0.1)
    perc_chase_gap = get_bool('percentage {}: ', default=False)
    perc_chase_gap = chase_gap if perc_chase_gap else False
    print('p gap: ', perc_chase_gap)
    pl_ratio = get_float('profit/loss ratio: ', minimum=0.1)
    last_entry = get_time('last entry (h:m:s): ', '%H:%M:%S')
    old_date = None
    previous_bar = None
    previous_close = None
    trailing = forced = False
    gain = loss= profit_taker= 0
    if perc_chase_gap:
        get_bool('Percentage!!', default=True)
    with open('/tmp/tryout', 'w') as of:
        for bar in dbfeeder(TESTFILE, is_index=True):
            date = bar.time.date()
            if not date == old_date:
                # Code is ran first time and intraday
                traded_today = False
                print(date)
                if previous_bar:
                    previous_close = previous_bar.close
                else:
                    get_bool('First time in can not set close.', default=True)
                old_date = date
                if perc_chase_gap:
                    chase_gap = bar.open_ * perc_chase_gap / 100
            # Code is ran during day
            in_trade = dev_trader.in_trade_at(bar.time)
            timestamp = dev_trader.advance_timestamp_for_one_request(bar.time)
            if (not traded_today and
                not in_trade and
                bar.time.time() <= last_entry and
                previous_close is not None):
                if previous_close - bar.low > chase_gap:
                    #get_bool('{}|{}'.format(bar.high, previous_close), default=True)
                    print('\n>>>>>>>>  ',timestamp, '  >>>>>>>>')         
                    dev_trader.buy(
                        timestamp=timestamp,
                        info='ok',
                        quantity=1,
                        start=None,
                        until='GTC',
                        type='market',
                        volume_aware=False,
                        )
                    traded_today = True
                    #profit_taker = previous_close
                    trailing = forced = False
            if in_trade:
                if profit_taker == 0:
                    profit_taker = dev_trader.avg_in() + chase_gap
                if trailing:
                    stop = trailing
                else:
                    stop = dev_trader.avg_in()# + 1 / pl_ratio * chase_gap
            if (in_trade and
                bar.low < stop - 1 / pl_ratio * chase_gap):
                if (trailing and not forced):
                    dev_trader.close(timestamp, 'gain', 0)
                    gain += 1
                    #traded_today = False
                elif trailing:                    
                    dev_trader.close(timestamp, 'forced trailing', 0)
                else:
                    dev_trader.close(timestamp, 'loss', 0)
                    loss +=1
                print('<<<<<<<<  ', timestamp, '<<<<<<<<\n')
                print(timestamp, gain, ' | ', loss, file=of)
                profit_taker = 0
            elif (in_trade and
                  bar.high - profit_taker > 0):
                print('TRAILING  ', timestamp, 'TRAILING\n')
                trailing = profit_taker = bar.low
            previous_bar = bar
    dev_trader.pickle_order_lists()
            
def top_menu():
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',)
    #####
    #
    menu.add_menu_item('Quit', 'Q', return_value='quit')
    #
    menu.add_menu_item('One big stream', 's', return_value=stream_all_data)
    menu.add_menu_item('Day & Intraday code', 'd', return_value=day_intra_day)
    #####
    return menu

def day_and_intraday_menu():
    menu = SelectionMenu(interface='TXT_ROW',
                         message='Choice: ',
                         auto_number=True)
    ###
    menu.add_menu_item('oli\'s gap', return_value=olis_gap)
    menu.add_menu_item('oli\'s trailing gap', return_value=olis_gap_trail_out)
    menu.add_menu_item('oli\'s trailing gap2', return_value=olis_gap_trail_2)
    menu.add_menu_item('oli\'s trailing gap2up', return_value=olis_gap_trail_2_up)
    ###
    return menu
    
        
if __name__ == '__main__':
    main()
    
    