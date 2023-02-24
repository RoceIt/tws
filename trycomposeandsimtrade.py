#!/usr/bin/env python3
#
#  Copyright (c) 2013 Rolf Camps (rolf.camps@scarlet.be)
#
import datetime

from mypy import import_pickle
from marketdata import data_bar_feeder, DataBarComposer, Error
from roc_input import SelectionMenu, get_integer, get_bool, get_time, get_float
import market_sim

#TESTFILE = import_pickle('/home/rolcam/roce/tmp.dax.db', 'serial databars')
TESTFILE = '/home/rolcam/roce/Data/db/EOE IND EUR AEX@FTA.db'

def compose_new_bars_from_feeder(*args, **kwds):
    '''Create feeder with new bar length from existing bars.
    
    Needs the feeder keyword with the feeder, other kwds args will be
    send to the composer.
    '''
    old_time = None
    unread_data = []
    feeder = kwds.pop('feeder')
    new_data_bars = DataBarComposer(*args, **kwds)
    for bar in feeder:
        time = bar.time
        #date = bar.time.date()
        if old_time and time - old_time < bar.duration:
            continue
        if not old_time or not time.date() == old_time.date():
            if not new_data_bars.start_time is None:
                unread_data = new_data_bars.reset_composer()
        new_data_bars.insert_bar(bar)
        new_bar = new_data_bars.pop_complete_bar()
        if not new_bar is None:
            unread_data.append(new_bar)
        while unread_data:
            yield unread_data.pop(0)
        old_time = time
            
#old_date = None            
#for bar in data_bar_feeder(TESTFILE, is_index=True):
    #if old_date is None:
        #old_date = bar.time
        #continue
    #if bar.time - old_date < datetime.timedelta(seconds=5):
        #print(bar)
        #continue
    #old_date = bar.time
#exit()

#t = 0
#for bar in compose_new_bars_from_feeder(
    #feeder= data_bar_feeder(TESTFILE, is_index=True),
    #minutes=1,
#):
    #t+=1
    #if t %1000 == 0:
        #print(bar)
#print('last bar: ', bar)
#exit()
    

#new_data_bars =  DataBarComposer(minutes=1)
dev_trader = market_sim.DevotedTrader('TestTrader',
                                      data_bar_feeder(TESTFILE, is_index=True))
old_date = previous_close = None

for bar in compose_new_bars_from_feeder(
    feeder= data_bar_feeder(TESTFILE, is_index=True), # Data source
    minutes=1, # new composed bar length
):
    ts = bar.end_time()
    date = bar.time.date()
    if not date == old_date:
        old_date = date
        print(date)
        if previous_close is None:
            continue
        last_close = previous_close
        in_trade, ts = dev_trader.in_trade_at(ts)
        if in_trade:
            order_id, ts = dev_trader.close_position(ts, 'OVERNIGHT?!!', 0)
            dev_trader.print_order(order_id)
            continue
        if bar.close < last_close:
            #get_bool('a buy', default=True)
            order = dev_trader.buy
            gain = stop = dev_trader.sell
            take_on_average = 10
        else:
            order = dev_trader.sell
            gain = stop = dev_trader.buy
            take_on_average = -10
        order_id, ts = order(
            timestamp=ts,
            info='in begin second bar of the day',
            quantity=market_sim.OrderValue(1),
            start=market_sim.OrderStartConditions('now'),
            until=(market_sim.RemoveOrderCondition('GTC'),),           
            type='market',
            volume_aware=False,
        )
        dev_trader.print_order(order_id)
        gain_id, ts = gain(
            parent_order=order_id,
            timestamp=ts,
            info ='set profit taker when order is filled',
            quantity=market_sim.OrderValue(1),
            start=market_sim.OrderStartConditions('parent_filled'),
            until=(
                market_sim.RemoveOrderCondition('parent_closed'),
                market_sim.RemoveOrderCondition('GTD', bar.time.date())),
            type='limit',
            limit=market_sim.OrderValue('avg_in_parent', take_on_average),
            volume_aware=False,
            closes=order_id,
        )
        dev_trader.print_order(order_id)
        stop_id, ts = stop(
            parent_order=order_id,
            timestamp=ts,
            info ='set stop when order is filled',
            quantity=market_sim.OrderValue(1),
            start=market_sim.OrderStartConditions('parent_filled'),
            until=(
                market_sim.RemoveOrderCondition('parent_closed'),
                market_sim.RemoveOrderCondition('GTD', bar.time.date())),
            type='stop_limit',
            stop=market_sim.OrderValue('avg_in_parent', -take_on_average),
            limit=market_sim.OrderValue('no_limit'),
            volume_aware=False,
            closes=order_id,
        )
        dev_trader.print_order(gain_id)
        continue
    previous_close = bar.close
    #in_trade,ts = dev_trader.in_trade_at(ts)
    
dev_trader.pickle_order_lists()

        